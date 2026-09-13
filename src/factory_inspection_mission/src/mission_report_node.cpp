#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "factory_inspection_interfaces/msg/inspection_result.hpp"
#include "factory_inspection_interfaces/msg/patrol_round_summary.hpp"
#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;

namespace
{

using InspectionResult = factory_inspection_interfaces::msg::InspectionResult;
using PatrolRoundSummary = factory_inspection_interfaces::msg::PatrolRoundSummary;

constexpr char kRoundReportSchemaVersion[] = "round_report.v3";
constexpr char kDashboardStateSchemaVersion[] = "dashboard_state.v3";
constexpr char kCampaignStateSchemaVersion[] = "campaign_state.v3";

std::string json_escape(const std::string & value)
{
  std::string escaped;
  escaped.reserve(value.size() + 8U);

  for (const char character : value) {
    switch (character) {
      case '\\':
        escaped += "\\\\";
        break;
      case '"':
        escaped += "\\\"";
        break;
      case '\n':
        escaped += "\\n";
        break;
      default:
        escaped.push_back(character);
        break;
    }
  }

  return escaped;
}

std::string html_escape(const std::string & value)
{
  std::string escaped;
  escaped.reserve(value.size() + 8U);

  for (const char character : value) {
    switch (character) {
      case '&':
        escaped += "&amp;";
        break;
      case '<':
        escaped += "&lt;";
        break;
      case '>':
        escaped += "&gt;";
        break;
      case '"':
        escaped += "&quot;";
        break;
      default:
        escaped.push_back(character);
        break;
    }
  }

  return escaped;
}

std::string csv_escape(const std::string & value)
{
  std::string escaped = "\"";
  for (const char character : value) {
    if (character == '"') {
      escaped += "\"\"";
    } else {
      escaped += character;
    }
  }
  escaped += "\"";
  return escaped;
}

std::string lowercase_copy(std::string value)
{
  std::transform(
    value.begin(),
    value.end(),
    value.begin(),
    [](const unsigned char character) { return static_cast<char>(std::tolower(character)); });
  return value;
}

int severity_rank(const std::string & severity)
{
  const auto normalized = lowercase_copy(severity);
  if (normalized == "critical") {
    return 2;
  }
  if (normalized == "warning" || normalized == "warn") {
    return 1;
  }
  return 0;
}

std::string join_strings(const std::vector<std::string> & values, const std::string & delimiter)
{
  if (values.empty()) {
    return "";
  }

  std::ostringstream stream;
  for (std::size_t index = 0; index < values.size(); ++index) {
    stream << values.at(index);
    if (index + 1U < values.size()) {
      stream << delimiter;
    }
  }
  return stream.str();
}

std::string format_fixed(const double value, const int precision = 1)
{
  std::ostringstream stream;
  stream << std::fixed << std::setprecision(precision) << value;
  return stream.str();
}

std::string report_file_stem(const std::uint32_t round_number)
{
  std::ostringstream stem;
  stem << "round_" << std::setw(4) << std::setfill('0') << round_number << "_report";
  return stem.str();
}

std::string severity_badge_class(const std::string & severity)
{
  const auto normalized = lowercase_copy(severity);
  if (normalized == "critical") {
    return "badge-critical";
  }
  if (normalized == "warning" || normalized == "warn") {
    return "badge-warning";
  }
  return "badge-normal";
}

std::string file_url_for_path(const std::string & path)
{
  if (path.empty()) {
    return "";
  }
  return "file://" + path;
}

bool is_truth_anomaly(const std::string & severity)
{
  return severity_rank(severity) > 0;
}

struct EvaluationSummary
{
  std::size_t known_truth_count{0U};
  std::size_t matched_count{0U};
  std::size_t mismatch_count{0U};
  std::size_t ground_truth_anomaly_count{0U};
  std::size_t false_positive_count{0U};
  std::size_t false_negative_count{0U};
};

struct DetectionMetrics
{
  double accuracy_percent{0.0};
  double precision_percent{0.0};
  double recall_percent{0.0};
  double f1_percent{0.0};
};

struct ZoneSummary
{
  std::size_t inspection_count{0U};
  std::size_t anomaly_count{0U};
  std::size_t critical_count{0U};
  float health_sum{0.0F};
};

EvaluationSummary evaluate_inspections(const std::vector<InspectionResult> & inspections)
{
  EvaluationSummary summary;

  for (const auto & inspection : inspections) {
    if (inspection.ground_truth_label.empty()) {
      continue;
    }

    ++summary.known_truth_count;
    if (inspection.matches_ground_truth) {
      ++summary.matched_count;
    } else {
      ++summary.mismatch_count;
    }

    const bool truth_anomaly = is_truth_anomaly(inspection.ground_truth_severity);
    if (truth_anomaly) {
      ++summary.ground_truth_anomaly_count;
    }

    if (inspection.is_anomaly && !truth_anomaly) {
      ++summary.false_positive_count;
    }
    if (!inspection.is_anomaly && truth_anomaly) {
      ++summary.false_negative_count;
    }
  }

  return summary;
}

DetectionMetrics compute_detection_metrics(const EvaluationSummary & evaluation)
{
  DetectionMetrics metrics;
  if (evaluation.known_truth_count > 0U) {
    metrics.accuracy_percent =
      100.0 * static_cast<double>(evaluation.matched_count) /
      static_cast<double>(evaluation.known_truth_count);
  }

  const auto true_positive_count =
    evaluation.ground_truth_anomaly_count - evaluation.false_negative_count;
  const auto predicted_positive_count = true_positive_count + evaluation.false_positive_count;

  if (predicted_positive_count > 0U) {
    metrics.precision_percent =
      100.0 * static_cast<double>(true_positive_count) /
      static_cast<double>(predicted_positive_count);
  }
  if (evaluation.ground_truth_anomaly_count > 0U) {
    metrics.recall_percent =
      100.0 * static_cast<double>(true_positive_count) /
      static_cast<double>(evaluation.ground_truth_anomaly_count);
  }
  if (metrics.precision_percent > 0.0 && metrics.recall_percent > 0.0) {
    metrics.f1_percent =
      2.0 * metrics.precision_percent * metrics.recall_percent /
      (metrics.precision_percent + metrics.recall_percent);
  }
  return metrics;
}

std::map<std::string, ZoneSummary> summarize_zones(const std::vector<InspectionResult> & inspections)
{
  std::map<std::string, ZoneSummary> summaries;
  for (const auto & inspection : inspections) {
    auto & zone = summaries[inspection.zone.empty() ? std::string("unknown") : inspection.zone];
    ++zone.inspection_count;
    if (inspection.is_anomaly) {
      ++zone.anomaly_count;
    }
    if (severity_rank(inspection.inspection_severity) >= 2) {
      ++zone.critical_count;
    }
    zone.health_sum += inspection.health_score;
  }
  return summaries;
}

std::vector<InspectionResult> prioritized_inspections(std::vector<InspectionResult> inspections)
{
  std::sort(
    inspections.begin(),
    inspections.end(),
    [](const InspectionResult & left, const InspectionResult & right) {
      const int left_severity = severity_rank(left.inspection_severity);
      const int right_severity = severity_rank(right.inspection_severity);
      if (left_severity != right_severity) {
        return left_severity > right_severity;
      }
      if (left.asset_priority != right.asset_priority) {
        return left.asset_priority > right.asset_priority;
      }
      if (std::abs(left.health_score - right.health_score) > 0.01F) {
        return left.health_score < right.health_score;
      }
      return left.asset_id < right.asset_id;
    });
  return inspections;
}

std::string build_site_map_svg(const std::vector<InspectionResult> & inspections)
{
  if (inspections.empty()) {
    return "<svg viewBox=\"0 0 640 260\" role=\"img\" aria-label=\"No inspections yet\"></svg>";
  }

  double min_x = std::numeric_limits<double>::max();
  double max_x = std::numeric_limits<double>::lowest();
  double min_y = std::numeric_limits<double>::max();
  double max_y = std::numeric_limits<double>::lowest();

  for (const auto & inspection : inspections) {
    min_x = std::min(min_x, inspection.pose_x);
    max_x = std::max(max_x, inspection.pose_x);
    min_y = std::min(min_y, inspection.pose_y);
    max_y = std::max(max_y, inspection.pose_y);
  }

  const double width = 640.0;
  const double height = 280.0;
  const double margin = 36.0;
  const double span_x = std::max(1.0, max_x - min_x);
  const double span_y = std::max(1.0, max_y - min_y);

  auto scaled_x = [&](const double x) {
      return margin + ((x - min_x) / span_x) * (width - margin * 2.0);
    };
  auto scaled_y = [&](const double y) {
      return height - margin - ((y - min_y) / span_y) * (height - margin * 2.0);
    };

  std::ostringstream svg;
  svg << "<svg viewBox=\"0 0 640 280\" role=\"img\" aria-label=\"Factory inspection site map\">";
  svg << "<rect x=\"8\" y=\"8\" width=\"624\" height=\"264\" rx=\"22\" fill=\"#f6f0e5\" stroke=\"#d9cfbf\"/>";
  svg << "<path d=\"M 36 220 L 604 220\" stroke=\"#c8b9a1\" stroke-dasharray=\"10 8\" fill=\"none\"/>";
  svg << "<path d=\"M 120 40 L 120 240 M 320 40 L 320 240 M 520 40 L 520 240\" "
      << "stroke=\"#ebe0d0\" fill=\"none\"/>";

  for (const auto & inspection : inspections) {
    const std::string fill =
      severity_rank(inspection.inspection_severity) >= 2 ? "#c53030" :
      severity_rank(inspection.inspection_severity) == 1 ? "#d69e2e" : "#2f855a";
    const double cx = scaled_x(inspection.pose_x);
    const double cy = scaled_y(inspection.pose_y);

    svg << "<circle cx=\"" << format_fixed(cx, 1) << "\" cy=\"" << format_fixed(cy, 1)
        << "\" r=\"12\" fill=\"" << fill << "\" stroke=\"#20303a\" stroke-width=\"2\"/>";
    svg << "<text x=\"" << format_fixed(cx + 16.0, 1) << "\" y=\"" << format_fixed(cy + 4.0, 1)
        << "\" font-size=\"12\" font-family=\"Arial,sans-serif\" fill=\"#1e1d1b\">"
        << html_escape(inspection.asset_id) << "</text>";
  }

  svg << "</svg>";
  return svg.str();
}

std::string report_key(const std::string & run_id, const std::uint32_t round_number)
{
  return run_id + "::" + std::to_string(round_number);
}

std::string sanitize_filename(std::string value)
{
  std::transform(
    value.begin(),
    value.end(),
    value.begin(),
    [](const unsigned char character) {
      return std::isalnum(character) ? static_cast<char>(character) : '_';
    });
  return value.empty() ? std::string("run") : value;
}

std::string site_alert_level(const PatrolRoundSummary & summary)
{
  if (summary.critical_count > 0U) {
    return "critical";
  }
  if (summary.anomaly_count > 0U) {
    return "warning";
  }
  if (summary.review_required_count > 0U) {
    return "review";
  }
  return "nominal";
}

}  // namespace

class MissionReportNode : public rclcpp::Node
{
public:
  MissionReportNode()
  : Node("mission_report_node")
  {
    declare_parameter<std::string>("report_dir", "");

    const auto report_dir = get_parameter("report_dir").as_string();
    if (report_dir.empty()) {
      throw std::runtime_error("Parameter 'report_dir' must point to a writable report folder.");
    }

    report_dir_ = std::filesystem::path(report_dir);
    std::filesystem::create_directories(report_dir_);

    inspection_subscription_ = create_subscription<InspectionResult>(
      "inspection_results",
      rclcpp::QoS(50).reliable(),
      [this](const InspectionResult::SharedPtr message) {
        handle_inspection_result(*message);
      });

    summary_subscription_ = create_subscription<PatrolRoundSummary>(
      "patrol_round_summaries",
      rclcpp::QoS(10).reliable(),
      [this](const PatrolRoundSummary::SharedPtr message) {
        handle_round_summary(*message);
      });

    RCLCPP_INFO(
      get_logger(),
      "Mission report node ready. Writing round reports under %s",
      report_dir_.string().c_str());
  }

private:
  void handle_inspection_result(const InspectionResult & message)
  {
    auto & inspections = inspections_by_round_[report_key(message.run_id, message.round_number)];
    inspections.push_back(message);

    std::sort(
      inspections.begin(),
      inspections.end(),
      [](const InspectionResult & left, const InspectionResult & right) {
        return left.waypoint_index < right.waypoint_index;
      });
  }

  void handle_round_summary(const PatrolRoundSummary & message)
  {
    const auto key = report_key(message.run_id, message.round_number);
    round_summaries_[key] = message;
    schedule_report_write(key);
  }

  void schedule_report_write(const std::string & key)
  {
    auto existing = pending_report_timers_.find(key);
    if (existing != pending_report_timers_.end()) {
      existing->second->cancel();
    }

    pending_report_timers_[key] = create_wall_timer(
      500ms,
      [this, key]() {
        auto timer_it = pending_report_timers_.find(key);
        if (timer_it != pending_report_timers_.end()) {
          timer_it->second->cancel();
          pending_report_timers_.erase(timer_it);
        }
        write_round_report(key);
      });
  }

  void write_round_report(const std::string & key)
  {
    const auto summary_it = round_summaries_.find(key);
    if (summary_it == round_summaries_.end()) {
      return;
    }

    const auto inspections_it = inspections_by_round_.find(key);
    const std::vector<InspectionResult> inspections =
      inspections_it == inspections_by_round_.end() ?
      std::vector<InspectionResult>{} : inspections_it->second;
    const auto & summary = summary_it->second;
    const auto round_number = summary.round_number;
    const auto run_dir = report_dir_ / sanitize_filename(summary.run_id);
    std::filesystem::create_directories(run_dir);

    const auto stem = report_file_stem(round_number);
    const auto json_path = run_dir / (stem + ".json");
    const auto markdown_path = run_dir / (stem + ".md");
    const auto html_path = run_dir / (stem + ".html");
    const auto legacy_json_path = report_dir_ / (stem + ".json");
    const auto legacy_markdown_path = report_dir_ / (stem + ".md");
    const auto legacy_html_path = report_dir_ / (stem + ".html");
    const auto latest_json_path = report_dir_ / "latest_report.json";
    const auto latest_markdown_path = report_dir_ / "latest_report.md";
    const auto latest_html_path = report_dir_ / "latest_dashboard.html";
    const auto latest_state_path = report_dir_ / "latest_dashboard_state.json";
    const auto latest_run_manifest_path = run_dir / "dashboard_state.json";
    const auto latest_campaign_state_path = report_dir_ / "latest_campaign_state.json";
    const auto run_campaign_state_path = run_dir / "campaign_state.json";

    const auto json_content = build_json_report(summary, inspections);
    const auto markdown_content = build_markdown_report(summary, inspections);
    const auto html_content = build_html_report(summary, inspections);
    const auto state_content = build_dashboard_state_json(summary, inspections);
    const auto campaign_state_content = build_campaign_state_json(summary);

    try {
      append_asset_history(summary, inspections);
      write_file(json_path, json_content);
      write_file(markdown_path, markdown_content);
      write_file(html_path, html_content);
      write_file(legacy_json_path, json_content);
      write_file(legacy_markdown_path, markdown_content);
      write_file(legacy_html_path, html_content);
      write_file(latest_json_path, json_content);
      write_file(latest_markdown_path, markdown_content);
      write_file(latest_html_path, html_content);
      write_file(latest_state_path, state_content);
      write_file(latest_run_manifest_path, state_content);
      write_file(latest_campaign_state_path, campaign_state_content);
      write_file(run_campaign_state_path, campaign_state_content);
    } catch (const std::exception & error) {
      RCLCPP_ERROR(
        get_logger(),
        "Failed to write round %u report: %s",
        round_number,
        error.what());
      return;
    }

    RCLCPP_INFO(
      get_logger(),
      "Wrote round %u report with %u inspections, %u anomalies, lowest health %.1f -> %s",
      round_number,
      summary.inspection_count,
      summary.anomaly_count,
      summary.lowest_health_score,
      json_path.string().c_str());
  }

  std::vector<PatrolRoundSummary> round_timeline_for_run(const std::string & run_id) const
  {
    std::vector<PatrolRoundSummary> timeline;
    for (const auto & entry : round_summaries_) {
      if (entry.second.run_id != run_id) {
        continue;
      }
      timeline.push_back(entry.second);
    }

    std::sort(
      timeline.begin(),
      timeline.end(),
      [](const PatrolRoundSummary & left, const PatrolRoundSummary & right) {
        return left.round_number < right.round_number;
      });
    return timeline;
  }

  void append_asset_history(
    const PatrolRoundSummary & summary,
    const std::vector<InspectionResult> & inspections)
  {
    const auto key = report_key(summary.run_id, summary.round_number);
    if (history_written_keys_.count(key) > 0U) {
      return;
    }

    const auto history_path = report_dir_ / "asset_history.csv";
    const bool write_header = !std::filesystem::exists(history_path);
    std::ofstream output(history_path, std::ios::out | std::ios::app);
    if (!output.is_open()) {
      throw std::runtime_error("Unable to append asset history: " + history_path.string());
    }

    if (write_header) {
      output
        << "run_id,round_number,mission_id,mission_source,mission_type,mission_profile,"
        << "mission_decision,selected_assets,follow_up_assets,"
        << "asset_id,asset_display_name,asset_type,zone,inspection_label,inspection_severity,"
        << "inspection_confidence,review_required,review_reason,health_score,is_anomaly,"
        << "matches_ground_truth,ground_truth_label,ground_truth_severity,image_path,annotated_image_path\n";
    }

    const auto selected_assets = join_strings(summary.selected_assets, "|");
    const auto follow_up_assets = join_strings(summary.follow_up_assets, "|");

    for (const auto & inspection : inspections) {
      output
        << csv_escape(summary.run_id) << ","
        << summary.round_number << ","
        << csv_escape(summary.mission_id) << ","
        << csv_escape(summary.mission_source) << ","
        << csv_escape(summary.mission_type) << ","
        << csv_escape(summary.mission_profile) << ","
        << csv_escape(summary.mission_decision) << ","
        << csv_escape(selected_assets) << ","
        << csv_escape(follow_up_assets) << ","
        << csv_escape(inspection.asset_id) << ","
        << csv_escape(inspection.asset_display_name) << ","
        << csv_escape(inspection.asset_type) << ","
        << csv_escape(inspection.zone) << ","
        << csv_escape(inspection.inspection_label) << ","
        << csv_escape(inspection.inspection_severity) << ","
        << inspection.inspection_confidence << ","
        << (inspection.review_required ? "true" : "false") << ","
        << csv_escape(inspection.review_reason) << ","
        << inspection.health_score << ","
        << (inspection.is_anomaly ? "true" : "false") << ","
        << (inspection.matches_ground_truth ? "true" : "false") << ","
        << csv_escape(inspection.ground_truth_label) << ","
        << csv_escape(inspection.ground_truth_severity) << ","
        << csv_escape(inspection.image_path) << ","
        << csv_escape(inspection.annotated_image_path) << "\n";
    }

    history_written_keys_.insert(key);
  }

  std::string build_campaign_state_json(const PatrolRoundSummary & latest_summary) const
  {
    const auto timeline = round_timeline_for_run(latest_summary.run_id);
    std::map<std::string, std::vector<InspectionResult>> asset_history;

    for (const auto & round_summary : timeline) {
      const auto key = report_key(round_summary.run_id, round_summary.round_number);
      const auto inspections_it = inspections_by_round_.find(key);
      if (inspections_it == inspections_by_round_.end()) {
        continue;
      }
      for (const auto & inspection : inspections_it->second) {
        asset_history[inspection.asset_id].push_back(inspection);
      }
    }

    std::ostringstream json;
    json << "{\n";
    json << "  \"schema_version\": \"" << kCampaignStateSchemaVersion << "\",\n";
    json << "  \"run_id\": \"" << json_escape(latest_summary.run_id) << "\",\n";
    json << "  \"scenario_id\": \"" << json_escape(latest_summary.scenario_id) << "\",\n";
    json << "  \"latest_round_number\": " << latest_summary.round_number << ",\n";
    json << "  \"latest_mission_decision\": \"" << json_escape(latest_summary.mission_decision) << "\",\n";
    json << "  \"site_alert_level\": \"" << json_escape(site_alert_level(latest_summary)) << "\",\n";
    json << "  \"round_timeline\": [\n";
    for (std::size_t index = 0; index < timeline.size(); ++index) {
      const auto & round = timeline.at(index);
      json << "    {\n";
      json << "      \"round_number\": " << round.round_number << ",\n";
      json << "      \"mission_id\": \"" << json_escape(round.mission_id) << "\",\n";
      json << "      \"mission_source\": \"" << json_escape(round.mission_source) << "\",\n";
      json << "      \"mission_type\": \"" << json_escape(round.mission_type) << "\",\n";
      json << "      \"mission_profile\": \"" << json_escape(round.mission_profile) << "\",\n";
      json << "      \"mission_decision\": \"" << json_escape(round.mission_decision) << "\",\n";
      json << "      \"selected_assets\": [";
      for (std::size_t asset_index = 0; asset_index < round.selected_assets.size(); ++asset_index) {
        json << "\"" << json_escape(round.selected_assets.at(asset_index)) << "\"";
        if (asset_index + 1U < round.selected_assets.size()) {
          json << ", ";
        }
      }
      json << "],\n";
      json << "      \"follow_up_assets\": [";
      for (std::size_t asset_index = 0; asset_index < round.follow_up_assets.size(); ++asset_index) {
        json << "\"" << json_escape(round.follow_up_assets.at(asset_index)) << "\"";
        if (asset_index + 1U < round.follow_up_assets.size()) {
          json << ", ";
        }
      }
      json << "],\n";
      json << "      \"anomaly_count\": " << round.anomaly_count << ",\n";
      json << "      \"critical_count\": " << round.critical_count << ",\n";
      json << "      \"review_required_count\": " << round.review_required_count << ",\n";
      json << "      \"average_health_score\": " << round.average_health_score << ",\n";
      json << "      \"average_inspection_confidence\": " << round.average_inspection_confidence << ",\n";
      json << "      \"success\": " << (round.success ? "true" : "false") << "\n";
      json << "    }";
      if (index + 1U < timeline.size()) {
        json << ",";
      }
      json << "\n";
    }
    json << "  ],\n";
    json << "  \"asset_trends\": [\n";
    std::size_t asset_index = 0U;
    for (const auto & entry : asset_history) {
      const auto & history = entry.second;
      if (history.empty()) {
        continue;
      }

      std::uint32_t anomaly_rounds = 0U;
      std::uint32_t review_rounds = 0U;
      float health_sum = 0.0F;
      float confidence_sum = 0.0F;
      float lowest_health = 100.0F;
      for (const auto & inspection : history) {
        if (inspection.is_anomaly) {
          ++anomaly_rounds;
        }
        if (inspection.review_required) {
          ++review_rounds;
        }
        health_sum += inspection.health_score;
        confidence_sum += inspection.inspection_confidence;
        lowest_health = std::min(lowest_health, inspection.health_score);
      }

      const auto & latest = history.back();
      const bool outstanding =
        latest.is_anomaly ||
        latest.review_required ||
        lowercase_copy(latest.asset_status) != "healthy";

      json << "    {\n";
      json << "      \"asset_id\": \"" << json_escape(latest.asset_id) << "\",\n";
      json << "      \"asset_display_name\": \"" << json_escape(latest.asset_display_name) << "\",\n";
      json << "      \"zone\": \"" << json_escape(latest.zone) << "\",\n";
      json << "      \"inspection_count\": " << history.size() << ",\n";
      json << "      \"anomaly_rounds\": " << anomaly_rounds << ",\n";
      json << "      \"review_rounds\": " << review_rounds << ",\n";
      json << "      \"latest_label\": \"" << json_escape(latest.inspection_label) << "\",\n";
      json << "      \"latest_severity\": \"" << json_escape(latest.inspection_severity) << "\",\n";
      json << "      \"latest_health_score\": " << latest.health_score << ",\n";
      json << "      \"lowest_health_score\": " << lowest_health << ",\n";
      json << "      \"average_health_score\": " << (health_sum / static_cast<float>(history.size())) << ",\n";
      json << "      \"average_confidence\": " << (confidence_sum / static_cast<float>(history.size())) << ",\n";
      json << "      \"outstanding\": " << (outstanding ? "true" : "false") << ",\n";
      json << "      \"latest_image_path\": \"" << json_escape(latest.image_path) << "\",\n";
      json << "      \"latest_annotated_image_path\": \"" << json_escape(latest.annotated_image_path) << "\"\n";
      json << "    }";
      if (asset_index + 1U < asset_history.size()) {
        json << ",";
      }
      json << "\n";
      ++asset_index;
    }
    json << "  ]\n";
    json << "}\n";
    return json.str();
  }

  std::string build_json_report(
    const PatrolRoundSummary & summary,
    const std::vector<InspectionResult> & inspections) const
  {
    const auto evaluation = evaluate_inspections(inspections);
    const auto metrics = compute_detection_metrics(evaluation);
    const auto zone_summaries = summarize_zones(inspections);
    const auto prioritized = prioritized_inspections(inspections);

    std::ostringstream json;
    json << "{\n";
    json << "  \"schema_version\": \"" << kRoundReportSchemaVersion << "\",\n";
    json << "  \"round_number\": " << summary.round_number << ",\n";
    json << "  \"mission_id\": \"" << json_escape(summary.mission_id) << "\",\n";
    json << "  \"mission_source\": \"" << json_escape(summary.mission_source) << "\",\n";
    json << "  \"mission_type\": \"" << json_escape(summary.mission_type) << "\",\n";
    json << "  \"mission_profile\": \"" << json_escape(summary.mission_profile) << "\",\n";
    json << "  \"scenario_id\": \"" << json_escape(summary.scenario_id) << "\",\n";
    json << "  \"run_id\": \"" << json_escape(summary.run_id) << "\",\n";
    json << "  \"timestamp_ns\": "
         << summary.stamp.sec * 1000000000LL + summary.stamp.nanosec << ",\n";
    json << "  \"success\": " << (summary.success ? "true" : "false") << ",\n";
    json << "  \"duration_seconds\": " << summary.duration_seconds << ",\n";
    json << "  \"action_result\": \"" << json_escape(summary.action_result) << "\",\n";
    json << "  \"nav2_error_code\": " << summary.nav2_error_code << ",\n";
    json << "  \"inspection_count\": " << summary.inspection_count << ",\n";
    json << "  \"anomaly_count\": " << summary.anomaly_count << ",\n";
    json << "  \"warning_count\": " << summary.warning_count << ",\n";
    json << "  \"critical_count\": " << summary.critical_count << ",\n";
    json << "  \"review_required_count\": " << summary.review_required_count << ",\n";
    json << "  \"degraded_asset_count\": " << summary.degraded_asset_count << ",\n";
    json << "  \"thermal_alert_count\": " << summary.thermal_alert_count << ",\n";
    json << "  \"acoustic_alert_count\": " << summary.acoustic_alert_count << ",\n";
    json << "  \"gas_alert_count\": " << summary.gas_alert_count << ",\n";
    json << "  \"capture_failures\": " << summary.capture_failures << ",\n";
    json << "  \"average_health_score\": " << summary.average_health_score << ",\n";
    json << "  \"lowest_health_score\": " << summary.lowest_health_score << ",\n";
    json << "  \"average_inspection_confidence\": " << summary.average_inspection_confidence << ",\n";
    json << "  \"ground_truth_count\": " << evaluation.known_truth_count << ",\n";
    json << "  \"ground_truth_anomaly_count\": " << evaluation.ground_truth_anomaly_count << ",\n";
    json << "  \"matched_count\": " << evaluation.matched_count << ",\n";
    json << "  \"mismatch_count\": " << evaluation.mismatch_count << ",\n";
    json << "  \"false_positive_count\": " << evaluation.false_positive_count << ",\n";
    json << "  \"false_negative_count\": " << evaluation.false_negative_count << ",\n";
    json << "  \"accuracy_percent\": " << metrics.accuracy_percent << ",\n";
    json << "  \"precision_percent\": " << metrics.precision_percent << ",\n";
    json << "  \"recall_percent\": " << metrics.recall_percent << ",\n";
    json << "  \"f1_percent\": " << metrics.f1_percent << ",\n";
    json << "  \"site_alert_level\": \"" << json_escape(site_alert_level(summary)) << "\",\n";
    json << "  \"mission_decision\": \"" << json_escape(summary.mission_decision) << "\",\n";
    json << "  \"decision_reason\": \"" << json_escape(summary.decision_reason) << "\",\n";
    json << "  \"selected_assets\": [";
    for (std::size_t index = 0; index < summary.selected_assets.size(); ++index) {
      json << "\"" << json_escape(summary.selected_assets.at(index)) << "\"";
      if (index + 1U < summary.selected_assets.size()) {
        json << ", ";
      }
    }
    json << "],\n";
    json << "  \"follow_up_assets\": [";
    for (std::size_t index = 0; index < summary.follow_up_assets.size(); ++index) {
      json << "\"" << json_escape(summary.follow_up_assets.at(index)) << "\"";
      if (index + 1U < summary.follow_up_assets.size()) {
        json << ", ";
      }
    }
    json << "],\n";
    json << "  \"zone_summary\": {\n";
    std::size_t zone_index = 0U;
    for (const auto & zone_entry : zone_summaries) {
      const auto average_health = zone_entry.second.inspection_count == 0U ? 100.0 :
        zone_entry.second.health_sum / static_cast<float>(zone_entry.second.inspection_count);
      json << "    \"" << json_escape(zone_entry.first) << "\": {\n";
      json << "      \"inspection_count\": " << zone_entry.second.inspection_count << ",\n";
      json << "      \"anomaly_count\": " << zone_entry.second.anomaly_count << ",\n";
      json << "      \"critical_count\": " << zone_entry.second.critical_count << ",\n";
      json << "      \"average_health_score\": " << average_health << "\n";
      json << "    }";
      if (zone_index + 1U < zone_summaries.size()) {
        json << ",";
      }
      json << "\n";
      ++zone_index;
    }
    json << "  },\n";
    json << "  \"prioritized_assets\": [\n";
    for (std::size_t index = 0; index < prioritized.size(); ++index) {
      const auto & inspection = prioritized.at(index);
      json << "    {\n";
      json << "      \"asset_id\": \"" << json_escape(inspection.asset_id) << "\",\n";
      json << "      \"asset_display_name\": \"" << json_escape(inspection.asset_display_name) << "\",\n";
      json << "      \"zone\": \"" << json_escape(inspection.zone) << "\",\n";
      json << "      \"inspection_label\": \"" << json_escape(inspection.inspection_label) << "\",\n";
      json << "      \"inspection_severity\": \"" << json_escape(inspection.inspection_severity) << "\",\n";
      json << "      \"inspection_confidence\": " << inspection.inspection_confidence << ",\n";
      json << "      \"review_required\": " << (inspection.review_required ? "true" : "false") << ",\n";
      json << "      \"review_reason\": \"" << json_escape(inspection.review_reason) << "\",\n";
      json << "      \"health_score\": " << inspection.health_score << "\n";
      json << "    }";
      if (index + 1U < prioritized.size()) {
        json << ",";
      }
      json << "\n";
    }
    json << "  ],\n";
    json << "  \"checkpoints\": [\n";
    for (std::size_t index = 0; index < inspections.size(); ++index) {
      const auto & inspection = inspections.at(index);
      json << "    {\n";
      json << "      \"waypoint_index\": " << inspection.waypoint_index << ",\n";
      json << "      \"checkpoint_name\": \"" << json_escape(inspection.checkpoint_name) << "\",\n";
      json << "      \"asset_id\": \"" << json_escape(inspection.asset_id) << "\",\n";
      json << "      \"asset_display_name\": \"" << json_escape(inspection.asset_display_name) << "\",\n";
      json << "      \"asset_type\": \"" << json_escape(inspection.asset_type) << "\",\n";
      json << "      \"zone\": \"" << json_escape(inspection.zone) << "\",\n";
      json << "      \"asset_priority\": " << inspection.asset_priority << ",\n";
      json << "      \"enabled_modalities\": [";
      for (std::size_t m = 0; m < inspection.enabled_modalities.size(); ++m) {
        json << "\"" << json_escape(inspection.enabled_modalities.at(m)) << "\"";
        if (m + 1U < inspection.enabled_modalities.size()) {
          json << ", ";
        }
      }
      json << "],\n";
      json << "      \"anomaly_sources\": [";
      for (std::size_t a = 0; a < inspection.anomaly_sources.size(); ++a) {
        json << "\"" << json_escape(inspection.anomaly_sources.at(a)) << "\"";
        if (a + 1U < inspection.anomaly_sources.size()) {
          json << ", ";
        }
      }
      json << "],\n";
      json << "      \"inspection_label\": \"" << json_escape(inspection.inspection_label) << "\",\n";
      json << "      \"inspection_severity\": \"" << json_escape(inspection.inspection_severity) << "\",\n";
      json << "      \"inspection_confidence\": " << inspection.inspection_confidence << ",\n";
      json << "      \"review_required\": " << (inspection.review_required ? "true" : "false") << ",\n";
      json << "      \"review_reason\": \"" << json_escape(inspection.review_reason) << "\",\n";
      json << "      \"recommended_action\": \"" << json_escape(inspection.recommended_action) << "\",\n";
      json << "      \"asset_status\": \"" << json_escape(inspection.asset_status) << "\",\n";
      json << "      \"health_score\": " << inspection.health_score << ",\n";
      json << "      \"thermal_delta_c\": " << inspection.thermal_delta_c << ",\n";
      json << "      \"acoustic_db\": " << inspection.acoustic_db << ",\n";
      json << "      \"gas_ppm\": " << inspection.gas_ppm << ",\n";
      json << "      \"thermal_alert\": " << (inspection.thermal_alert ? "true" : "false") << ",\n";
      json << "      \"acoustic_alert\": " << (inspection.acoustic_alert ? "true" : "false") << ",\n";
      json << "      \"gas_alert\": " << (inspection.gas_alert ? "true" : "false") << ",\n";
      json << "      \"is_anomaly\": " << (inspection.is_anomaly ? "true" : "false") << ",\n";
      json << "      \"capture_ok\": " << (inspection.capture_ok ? "true" : "false") << ",\n";
      json << "      \"image_path\": \"" << json_escape(inspection.image_path) << "\",\n";
      json << "      \"raw_image_path\": \"" << json_escape(inspection.raw_image_path) << "\",\n";
      json << "      \"annotated_image_path\": \"" << json_escape(inspection.annotated_image_path) << "\",\n";
      json << "      \"ground_truth_label\": \"" << json_escape(inspection.ground_truth_label) << "\",\n";
      json << "      \"ground_truth_severity\": \"" << json_escape(inspection.ground_truth_severity) << "\",\n";
      json << "      \"matches_ground_truth\": "
           << (inspection.matches_ground_truth ? "true" : "false") << ",\n";
      json << "      \"pose\": {\n";
      json << "        \"x\": " << inspection.pose_x << ",\n";
      json << "        \"y\": " << inspection.pose_y << ",\n";
      json << "        \"yaw\": " << inspection.pose_yaw << "\n";
      json << "      },\n";
      json << "      \"note\": \"" << json_escape(inspection.note) << "\"\n";
      json << "    }";
      if (index + 1U < inspections.size()) {
        json << ",";
      }
      json << "\n";
    }
    json << "  ]\n";
    json << "}\n";
    return json.str();
  }

  std::string build_markdown_report(
    const PatrolRoundSummary & summary,
    const std::vector<InspectionResult> & inspections) const
  {
    const auto evaluation = evaluate_inspections(inspections);
    const auto metrics = compute_detection_metrics(evaluation);
    const auto zone_summaries = summarize_zones(inspections);
    
    std::ostringstream markdown;
    markdown << "# Patrol Round " << summary.round_number << " Report\n\n";
    markdown << "- Mission ID: " << (summary.mission_id.empty() ? "n/a" : summary.mission_id) << "\n";
    markdown << "- Mission Source: " << summary.mission_source << "\n";
    markdown << "- Mission Type: " << summary.mission_type << "\n";
    markdown << "- Mission Profile: " << summary.mission_profile << "\n";
    markdown << "- Scenario ID: " << summary.scenario_id << "\n";
    markdown << "- Run ID: " << summary.run_id << "\n";
    markdown << "- Status: " << (summary.success ? "SUCCESS" : "FAILURE") << "\n";
    markdown << "- Duration: " << format_fixed(summary.duration_seconds) << " s\n";
    markdown << "- Action Result: " << summary.action_result << "\n";
    markdown << "- Nav2 Error Code: " << summary.nav2_error_code << "\n";
    markdown << "- Site Alert Level: " << site_alert_level(summary) << "\n";
    markdown << "- Inspections: " << summary.inspection_count << "\n";
    markdown << "- Anomalies: " << summary.anomaly_count << "\n";
    markdown << "- Review Required: " << summary.review_required_count << "\n";
    markdown << "- Degraded Assets: " << summary.degraded_asset_count << "\n";
    markdown << "- Thermal / Acoustic / Gas Alerts: "
             << summary.thermal_alert_count << " / "
             << summary.acoustic_alert_count << " / "
             << summary.gas_alert_count << "\n";
    markdown << "- Average Health Score: " << format_fixed(summary.average_health_score) << "\n";
    markdown << "- Lowest Health Score: " << format_fixed(summary.lowest_health_score) << "\n";
    markdown << "- Average Confidence: " << format_fixed(summary.average_inspection_confidence, 2) << "\n";
    markdown << "- Detection Accuracy: " << format_fixed(metrics.accuracy_percent) << "%\n";
    markdown << "- Detection Precision / Recall / F1: "
             << format_fixed(metrics.precision_percent) << "% / "
             << format_fixed(metrics.recall_percent) << "% / "
             << format_fixed(metrics.f1_percent) << "%\n";
    markdown << "- Mission Decision: " << summary.mission_decision << "\n";
    markdown << "- Decision Reason: " << summary.decision_reason << "\n";

    if (!summary.follow_up_assets.empty()) {
      markdown << "- Follow-Up Assets: " << join_strings(summary.follow_up_assets, ", ") << "\n";
    }

    markdown << "\n## Zones\n\n";
    for (const auto & zone_entry : zone_summaries) {
      const auto average_health = zone_entry.second.inspection_count == 0U ? 100.0 :
        zone_entry.second.health_sum / static_cast<float>(zone_entry.second.inspection_count);
      markdown << "- " << zone_entry.first
               << " | inspections=" << zone_entry.second.inspection_count
               << " | anomalies=" << zone_entry.second.anomaly_count
               << " | critical=" << zone_entry.second.critical_count
               << " | avg_health=" << format_fixed(average_health) << "\n";
    }

    markdown << "\n## Assets\n\n";
    for (const auto & inspection : inspections) {
      markdown << "- [" << inspection.asset_id << "] "
               << inspection.asset_display_name
               << " | zone=" << inspection.zone
               << " | severity=" << inspection.inspection_severity
               << " | label=" << inspection.inspection_label
               << " | confidence=" << format_fixed(inspection.inspection_confidence, 2)
               << " | review=" << (inspection.review_required ? inspection.review_reason : "none")
               << " | health=" << format_fixed(inspection.health_score)
               << " | sources=" << join_strings(inspection.anomaly_sources, "+")
               << " | image=" << inspection.image_path
               << " | raw=" << inspection.raw_image_path << "\n";
    }

    return markdown.str();
  }

  std::string build_dashboard_state_json(
    const PatrolRoundSummary & summary,
    const std::vector<InspectionResult> & inspections) const
  {
    const auto prioritized = prioritized_inspections(inspections);
    std::ostringstream json;
    json << "{\n";
    json << "  \"schema_version\": \"" << kDashboardStateSchemaVersion << "\",\n";
    json << "  \"run_id\": \"" << json_escape(summary.run_id) << "\",\n";
    json << "  \"round_number\": " << summary.round_number << ",\n";
    json << "  \"mission_id\": \"" << json_escape(summary.mission_id) << "\",\n";
    json << "  \"mission_source\": \"" << json_escape(summary.mission_source) << "\",\n";
    json << "  \"mission_type\": \"" << json_escape(summary.mission_type) << "\",\n";
    json << "  \"scenario_id\": \"" << json_escape(summary.scenario_id) << "\",\n";
    json << "  \"mission_profile\": \"" << json_escape(summary.mission_profile) << "\",\n";
    json << "  \"mission_decision\": \"" << json_escape(summary.mission_decision) << "\",\n";
    json << "  \"site_alert_level\": \"" << json_escape(site_alert_level(summary)) << "\",\n";
    json << "  \"inspection_count\": " << summary.inspection_count << ",\n";
    json << "  \"anomaly_count\": " << summary.anomaly_count << ",\n";
    json << "  \"review_required_count\": " << summary.review_required_count << ",\n";
    json << "  \"average_health_score\": " << summary.average_health_score << ",\n";
    json << "  \"average_inspection_confidence\": " << summary.average_inspection_confidence << ",\n";
    json << "  \"follow_up_assets\": [";
    for (std::size_t index = 0; index < summary.follow_up_assets.size(); ++index) {
      json << "\"" << json_escape(summary.follow_up_assets.at(index)) << "\"";
      if (index + 1U < summary.follow_up_assets.size()) {
        json << ", ";
      }
    }
    json << "],\n";
    json << "  \"top_findings\": [\n";
    const auto top_count = std::min<std::size_t>(prioritized.size(), 3U);
    for (std::size_t index = 0; index < top_count; ++index) {
      const auto & inspection = prioritized.at(index);
      json << "    {\n";
      json << "      \"asset_id\": \"" << json_escape(inspection.asset_id) << "\",\n";
      json << "      \"inspection_label\": \"" << json_escape(inspection.inspection_label) << "\",\n";
      json << "      \"inspection_severity\": \"" << json_escape(inspection.inspection_severity) << "\",\n";
      json << "      \"inspection_confidence\": " << inspection.inspection_confidence << ",\n";
      json << "      \"review_required\": " << (inspection.review_required ? "true" : "false") << "\n";
      json << "    }";
      if (index + 1U < top_count) {
        json << ",";
      }
      json << "\n";
    }
    json << "  ]\n";
    json << "}\n";
    return json.str();
  }

  std::string build_html_report(
    const PatrolRoundSummary & summary,
    const std::vector<InspectionResult> & inspections) const
  {
    const auto evaluation = evaluate_inspections(inspections);
    const auto metrics = compute_detection_metrics(evaluation);
    const auto zone_summaries = summarize_zones(inspections);
    const auto prioritized = prioritized_inspections(inspections);

    std::ostringstream html;
    html << "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n";
    html << "<meta charset=\"utf-8\" />\n";
    html << "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n";
    html << "<title>Factory Inspection Round " << summary.round_number << "</title>\n";
    html << "<style>\n";
    html << ":root{--bg:#f4efe7;--panel:#fffdf8;--ink:#161a1d;--muted:#61676f;--line:#d8d2c8;"
            "--ok:#2f855a;--warn:#b7791f;--critical:#c53030;--accent:#0f4c5c;--teal:#2c7a7b;}\n";
    html << "*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;"
            "background:radial-gradient(circle at top left,#f8f3ea 0%,#efe6d8 45%,#e5ece7 100%);color:var(--ink);}\n";
    html << ".page{max-width:1320px;margin:0 auto;padding:28px 18px 48px;display:grid;gap:22px;}\n";
    html << ".hero{display:grid;grid-template-columns:2.2fr 1fr;gap:18px;align-items:stretch;}\n";
    html << ".hero-card,.panel,.tile,.asset-card,.zone-card{background:rgba(255,253,248,.94);"
            "border:1px solid var(--line);border-radius:22px;box-shadow:0 22px 54px rgba(27,21,15,.08);}\n";
    html << ".hero-card{padding:28px;background:linear-gradient(135deg,#0f4c5c 0%,#216869 58%,#f7ebd5 180%);color:#fff;}\n";
    html << ".eyebrow{font:700 .78rem/1.1 Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#dff1ec;}\n";
    html << ".hero-card h1{margin:10px 0 12px;font-size:clamp(2rem,4vw,3.4rem);line-height:1.02;}\n";
    html << ".hero-card p{margin:0;max-width:46rem;color:rgba(255,255,255,.86);font-family:Arial,sans-serif;line-height:1.45;}\n";
    html << ".meta-row{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap;}\n";
    html << ".badge{display:inline-flex;align-items:center;padding:6px 12px;border-radius:999px;font:700 .77rem/1 Arial,sans-serif;letter-spacing:.05em;text-transform:uppercase;}\n";
    html << ".badge-normal{background:#e3f4ea;color:var(--ok);} .badge-warning{background:#fff1d7;color:var(--warn);} .badge-critical{background:#fde2e2;color:var(--critical);} .badge-accent{background:#dceff1;color:var(--accent);}\n";
    html << ".decision{padding:22px;display:grid;gap:12px;}\n";
    html << ".decision .note{padding:14px 16px;border-radius:16px;background:#f5efe6;border:1px dashed #d9cdb8;color:#554c42;font-family:Arial,sans-serif;line-height:1.5;}\n";
    html << ".stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;}\n";
    html << ".tile{padding:18px}.tile .k{font:600 .78rem/1.2 Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}.tile .v{margin-top:10px;font-size:1.72rem;font-weight:700}\n";
    html << ".split{display:grid;grid-template-columns:1.4fr .9fr;gap:18px;}\n";
    html << ".panel{padding:22px;display:grid;gap:16px;}\n";
    html << ".panel h2{margin:0;font-size:1.2rem;letter-spacing:.02em;}\n";
    html << ".zones{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;}\n";
    html << ".zone-card{padding:16px;background:#fffdfa;}\n";
    html << ".zone-card strong{display:block;font-size:1rem;margin-bottom:8px;}\n";
    html << ".zone-card p{margin:0;color:var(--muted);font-family:Arial,sans-serif;line-height:1.5;}\n";
    html << ".follow-up{display:grid;gap:12px;}\n";
    html << ".asset-card{padding:16px;display:grid;gap:10px;background:#fffdfa;}\n";
    html << ".asset-card p{margin:0;color:var(--muted);font-family:Arial,sans-serif;line-height:1.45;}\n";
    html << ".evidence-list{display:grid;gap:14px;}\n";
    html << ".evidence{display:grid;grid-template-columns:170px 1fr;gap:14px;padding:16px;border:1px solid var(--line);border-radius:18px;background:#fffdf9;}\n";
    html << ".evidence img{width:170px;height:128px;object-fit:cover;border-radius:14px;border:1px solid var(--line);background:#ece7df;}\n";
    html << ".evidence-body{display:grid;gap:8px;}\n";
    html << ".evidence-body p{margin:0;color:var(--muted);font-family:Arial,sans-serif;line-height:1.45;}\n";
    html << ".site-map{padding:8px;border-radius:18px;background:#fff9ef;border:1px solid #e7dbc8;}\n";
    html << "@media (max-width:960px){.hero,.split{grid-template-columns:1fr}.evidence{grid-template-columns:1fr}.evidence img{width:100%;height:auto;max-height:280px;}}\n";
    html << "</style>\n</head>\n<body>\n<div class=\"page\">\n";

    html << "<section class=\"hero\">\n";
    html << "<div class=\"hero-card\">\n";
    html << "<div class=\"eyebrow\">Autonomous Factory Inspection Robot</div>\n";
    html << "<h1>Mission Round " << summary.round_number << "</h1>\n";
    html << "<p>Scenario <strong>" << html_escape(summary.scenario_id) << "</strong> ran with profile "
         << "<strong>" << html_escape(summary.mission_profile)
         << "</strong>. The robot fused visual, thermal, acoustic, and gas-style inspection signals to prioritize follow-up assets and decide whether to continue the patrol.</p>\n";
    html << "<div class=\"meta-row\">\n";
    html << "<span class=\"badge badge-accent\">" << html_escape(summary.action_result) << "</span>\n";
    html << "<span class=\"badge badge-accent\">Decision: " << html_escape(summary.mission_decision) << "</span>\n";
    html << "<span class=\"badge badge-accent\">Mission: "
         << html_escape(summary.mission_id.empty() ? std::string("autonomous") : summary.mission_id)
         << "</span>\n";
    html << "<span class=\"badge badge-accent\">Source: " << html_escape(summary.mission_source) << "</span>\n";
    html << "<span class=\"badge badge-accent\">Type: " << html_escape(summary.mission_type) << "</span>\n";
    html << "<span class=\"badge badge-accent\">Run: " << html_escape(summary.run_id) << "</span>\n";
    html << "<span class=\"badge badge-accent\">Targets: " << html_escape(join_strings(summary.selected_assets, ", ")) << "</span>\n";
    html << "</div>\n</div>\n";

    html << "<aside class=\"panel decision\">\n";
    html << "<h2>Operator Decision</h2>\n";
    html << "<span class=\"badge badge-accent\">" << html_escape(summary.mission_decision) << "</span>\n";
    html << "<div class=\"note\">" << html_escape(summary.decision_reason) << "</div>\n";
    html << "<p><strong>Follow-up assets:</strong> "
         << html_escape(summary.follow_up_assets.empty() ? std::string("none") : join_strings(summary.follow_up_assets, ", "))
         << "<br/><strong>Average health:</strong> " << format_fixed(summary.average_health_score)
         << "<br/><strong>Average confidence:</strong> " << format_fixed(summary.average_inspection_confidence, 2)
         << "<br/><strong>Review queue:</strong> " << summary.review_required_count
         << "<br/><strong>Lowest health:</strong> " << format_fixed(summary.lowest_health_score)
         << "</p>\n";
    html << "</aside>\n";
    html << "</section>\n";

    html << "<section class=\"stats\">\n";
    html << stat_tile("Duration", format_fixed(summary.duration_seconds) + " s");
    html << stat_tile("Inspections", std::to_string(summary.inspection_count));
    html << stat_tile("Anomalies", std::to_string(summary.anomaly_count));
    html << stat_tile("Critical", std::to_string(summary.critical_count));
    html << stat_tile("Review Queue", std::to_string(summary.review_required_count));
    html << stat_tile("Avg Health", format_fixed(summary.average_health_score));
    html << stat_tile("Confidence", format_fixed(summary.average_inspection_confidence, 2));
    html << stat_tile("Accuracy", format_fixed(metrics.accuracy_percent, 0) + "%");
    html << stat_tile("Thermal Alerts", std::to_string(summary.thermal_alert_count));
    html << stat_tile("Gas Alerts", std::to_string(summary.gas_alert_count));
    html << "</section>\n";

    html << "<section class=\"split\">\n";
    html << "<div class=\"panel\">\n";
    html << "<h2>Digital Twin View</h2>\n";
    html << "<div class=\"site-map\">" << build_site_map_svg(inspections) << "</div>\n";
    html << "</div>\n";

    html << "<div class=\"panel\">\n";
    html << "<h2>Zone Summary</h2>\n<div class=\"zones\">\n";
    for (const auto & zone_entry : zone_summaries) {
      const auto average_health = zone_entry.second.inspection_count == 0U ? 100.0 :
        zone_entry.second.health_sum / static_cast<float>(zone_entry.second.inspection_count);
      html << "<article class=\"zone-card\"><strong>" << html_escape(zone_entry.first) << "</strong>";
      html << "<p>Inspections: " << zone_entry.second.inspection_count
           << "<br/>Anomalies: " << zone_entry.second.anomaly_count
           << "<br/>Critical: " << zone_entry.second.critical_count
           << "<br/>Avg Health: " << format_fixed(average_health) << "</p></article>\n";
    }
    html << "</div>\n</div>\n";
    html << "</section>\n";

    html << "<section class=\"split\">\n";
    html << "<div class=\"panel\">\n<h2>Prioritized Assets</h2>\n<div class=\"follow-up\">\n";
    for (const auto & inspection : prioritized) {
      html << "<article class=\"asset-card\">";
      html << "<div><strong>" << html_escape(inspection.asset_display_name) << "</strong> "
           << "<span class=\"badge " << severity_badge_class(inspection.inspection_severity) << "\">"
           << html_escape(inspection.inspection_severity) << "</span></div>\n";
      html << "<p>ID: " << html_escape(inspection.asset_id)
           << " | Zone: " << html_escape(inspection.zone)
           << " | Type: " << html_escape(inspection.asset_type)
           << " | Priority: " << inspection.asset_priority << "</p>\n";
      html << "<p>Label: " << html_escape(inspection.inspection_label)
           << " | Confidence: " << format_fixed(inspection.inspection_confidence, 2)
           << " | Health: " << format_fixed(inspection.health_score)
           << " | Sources: " << html_escape(join_strings(inspection.anomaly_sources, "+")) << "</p>\n";
      if (inspection.review_required) {
        html << "<p>Review reason: " << html_escape(inspection.review_reason) << "</p>\n";
      }
      html << "<p>Modalities: " << html_escape(join_strings(inspection.enabled_modalities, ", "))
           << " | Thermal " << format_fixed(inspection.thermal_delta_c)
           << " C | Acoustic " << format_fixed(inspection.acoustic_db)
           << " dB | Gas " << format_fixed(inspection.gas_ppm) << " ppm</p>\n";
      html << "</article>\n";
    }
    html << "</div>\n</div>\n";

    html << "<div class=\"panel\">\n<h2>Mission Integrity</h2>\n";
    html << "<p style=\"margin:0;color:var(--muted);font-family:Arial,sans-serif;line-height:1.55;\">"
         << "Matched " << evaluation.matched_count << " of " << evaluation.known_truth_count
         << " labeled assets. False positives: " << evaluation.false_positive_count
         << ". False negatives: " << evaluation.false_negative_count
         << ". Precision / Recall / F1: " << format_fixed(metrics.precision_percent, 0)
         << "% / " << format_fixed(metrics.recall_percent, 0)
         << "% / " << format_fixed(metrics.f1_percent, 0)
         << "%"
         << ". Capture failures: " << summary.capture_failures
         << ". Nav2 error code: " << summary.nav2_error_code << ".</p>\n";
    html << "<p style=\"margin:0;color:var(--muted);font-family:Arial,sans-serif;line-height:1.55;\">"
         << "Recommended follow-up: "
         << html_escape(summary.follow_up_assets.empty() ? std::string("none") : join_strings(summary.follow_up_assets, ", "))
         << ".</p>\n";
    html << "</div>\n";
    html << "</section>\n";

    html << "<section class=\"panel\">\n<h2>Checkpoint Evidence</h2>\n<div class=\"evidence-list\">\n";
    for (const auto & inspection : inspections) {
      html << "<article class=\"evidence\">\n";
      if (!inspection.image_path.empty() && inspection.capture_ok) {
        html << "<img src=\"" << html_escape(file_url_for_path(inspection.image_path))
             << "\" alt=\"Evidence image for " << html_escape(inspection.checkpoint_name) << "\" />\n";
      } else {
        html << "<div class=\"asset-card\"><p>No evidence image saved for this checkpoint.</p></div>\n";
      }
      html << "<div class=\"evidence-body\">\n";
      html << "<div><strong>" << html_escape(inspection.checkpoint_name) << "</strong> "
           << "<span class=\"badge " << severity_badge_class(inspection.inspection_severity) << "\">"
           << html_escape(inspection.inspection_severity) << "</span></div>\n";
      html << "<p>Asset: " << html_escape(inspection.asset_display_name)
           << " (" << html_escape(inspection.asset_id) << ")"
           << " | Zone: " << html_escape(inspection.zone)
           << " | Status: " << html_escape(inspection.asset_status) << "</p>\n";
      html << "<p>Label: " << html_escape(inspection.inspection_label)
           << " | Truth: " << html_escape(inspection.ground_truth_label)
           << " | Match: " << (inspection.matches_ground_truth ? "true" : "false")
           << " | Sources: " << html_escape(join_strings(inspection.anomaly_sources, "+")) << "</p>\n";
      html << "<p>Thermal " << format_fixed(inspection.thermal_delta_c)
           << " C | Acoustic " << format_fixed(inspection.acoustic_db)
           << " dB | Gas " << format_fixed(inspection.gas_ppm)
           << " ppm | Health " << format_fixed(inspection.health_score)
           << " | Confidence " << format_fixed(inspection.inspection_confidence, 2) << "</p>\n";
      html << "<p>Recommended action: " << html_escape(inspection.recommended_action)
           << " | Image path: " << html_escape(inspection.image_path) << "</p>\n";
      if (!inspection.raw_image_path.empty()) {
        html << "<p>Raw evidence: " << html_escape(inspection.raw_image_path) << "</p>\n";
      }
      if (inspection.review_required) {
        html << "<p>Review reason: " << html_escape(inspection.review_reason) << "</p>\n";
      }
      html << "<p>Note: " << html_escape(inspection.note) << "</p>\n";
      html << "</div>\n</article>\n";
    }
    html << "</div>\n</section>\n";

    html << "</div>\n</body>\n</html>\n";
    return html.str();
  }

  std::string stat_tile(const std::string & label, const std::string & value) const
  {
    std::ostringstream tile;
    tile << "<div class=\"tile\"><div class=\"k\">" << html_escape(label)
         << "</div><div class=\"v\">" << html_escape(value) << "</div></div>\n";
    return tile.str();
  }

  void write_file(const std::filesystem::path & path, const std::string & content) const
  {
    std::ofstream output(path, std::ios::out | std::ios::trunc);
    if (!output.is_open()) {
      throw std::runtime_error("Unable to write report file: " + path.string());
    }

    output << content;
  }

  std::filesystem::path report_dir_;
  rclcpp::Subscription<InspectionResult>::SharedPtr inspection_subscription_;
  rclcpp::Subscription<PatrolRoundSummary>::SharedPtr summary_subscription_;
  std::map<std::string, std::vector<InspectionResult>> inspections_by_round_;
  std::map<std::string, PatrolRoundSummary> round_summaries_;
  std::map<std::string, rclcpp::TimerBase::SharedPtr> pending_report_timers_;
  std::set<std::string> history_written_keys_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  try {
    auto node = std::make_shared<MissionReportNode>();
    rclcpp::spin(node);
  } catch (const std::exception & error) {
    RCLCPP_FATAL(
      rclcpp::get_logger("mission_report_node"),
      "Failed to start mission report node: %s",
      error.what());
    rclcpp::shutdown();
    return 1;
  }

  rclcpp::shutdown();
  return 0;
}
