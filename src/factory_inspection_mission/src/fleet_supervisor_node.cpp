#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "factory_inspection_interfaces/msg/inspection_result.hpp"
#include "factory_inspection_interfaces/msg/patrol_round_summary.hpp"
#include "rclcpp/rclcpp.hpp"

namespace
{

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

std::string fleet_topic(const std::string & robot_name, const std::string & leaf_topic)
{
  return "/" + robot_name + "/" + leaf_topic;
}

}  // namespace

class FleetSupervisorNode : public rclcpp::Node
{
public:
  using InspectionResult = factory_inspection_interfaces::msg::InspectionResult;
  using PatrolRoundSummary = factory_inspection_interfaces::msg::PatrolRoundSummary;

  FleetSupervisorNode()
  : Node("fleet_supervisor_node")
  {
    if (!has_parameter("use_sim_time")) {
      declare_parameter<bool>("use_sim_time", false);
    }
    declare_parameter<std::vector<std::string>>("robot_names", std::vector<std::string>{});
    declare_parameter<std::string>("report_dir", "");

    robot_names_ = get_parameter("robot_names").as_string_array();
    const auto report_dir = get_parameter("report_dir").as_string();
    if (robot_names_.empty()) {
      throw std::runtime_error("Parameter 'robot_names' must contain at least one fleet robot name.");
    }
    if (report_dir.empty()) {
      throw std::runtime_error("Parameter 'report_dir' must point to a writable folder.");
    }

    report_dir_ = std::filesystem::path(report_dir);
    std::filesystem::create_directories(report_dir_);

    for (const auto & robot_name : robot_names_) {
      inspection_subscriptions_.push_back(
        create_subscription<InspectionResult>(
          fleet_topic(robot_name, "inspection_results"),
          rclcpp::QoS(50).reliable(),
          [this, robot_name](const InspectionResult::SharedPtr message) {
            handle_inspection(robot_name, *message);
          }));

      summary_subscriptions_.push_back(
        create_subscription<PatrolRoundSummary>(
          fleet_topic(robot_name, "patrol_round_summaries"),
          rclcpp::QoS(10).reliable(),
          [this, robot_name](const PatrolRoundSummary::SharedPtr message) {
            handle_summary(robot_name, *message);
          }));
    }

    RCLCPP_INFO(
      get_logger(),
      "Fleet supervisor ready for robots [%s]. Writing aggregate fleet state under %s",
      join_strings(robot_names_).c_str(),
      report_dir_.string().c_str());
  }

private:
  struct RobotState
  {
    bool has_summary{false};
    bool has_inspection{false};
    PatrolRoundSummary summary;
    InspectionResult inspection;
  };

  std::string join_strings(const std::vector<std::string> & values) const
  {
    std::ostringstream stream;
    for (std::size_t index = 0; index < values.size(); ++index) {
      stream << values.at(index);
      if (index + 1U < values.size()) {
        stream << ", ";
      }
    }
    return stream.str();
  }

  void handle_inspection(const std::string & robot_name, const InspectionResult & inspection)
  {
    auto & state = robot_states_[robot_name];
    state.has_inspection = true;
    state.inspection = inspection;
    write_outputs();
  }

  void handle_summary(const std::string & robot_name, const PatrolRoundSummary & summary)
  {
    auto & state = robot_states_[robot_name];
    state.has_summary = true;
    state.summary = summary;
    write_outputs();

    RCLCPP_INFO(
      get_logger(),
      "Fleet update from %s: round=%u decision=%s anomalies=%u critical=%u success=%s",
      robot_name.c_str(),
      summary.round_number,
      summary.mission_decision.c_str(),
      summary.anomaly_count,
      summary.critical_count,
      summary.success ? "true" : "false");
  }

  void write_outputs()
  {
    std::size_t reporting_robots = 0U;
    std::size_t holding_robots = 0U;
    std::uint32_t total_anomalies = 0U;
    std::uint32_t total_critical = 0U;
    std::uint32_t total_reviews = 0U;

    std::ostringstream robots_json;
    std::ostringstream rows_html;
    bool first_robot = true;

    for (const auto & robot_name : robot_names_) {
      const auto state_it = robot_states_.find(robot_name);
      RobotState empty_state;
      const auto & state = state_it == robot_states_.end() ? empty_state : state_it->second;

      if (state.has_summary) {
        ++reporting_robots;
        total_anomalies += state.summary.anomaly_count;
        total_critical += state.summary.critical_count;
        total_reviews += state.summary.review_required_count;
        if (state.summary.mission_decision == "HOLD") {
          ++holding_robots;
        }
      }

      if (!first_robot) {
        robots_json << ",";
      }
      first_robot = false;

      robots_json << "\n    {"
                 << "\"robot_name\":\"" << json_escape(robot_name) << "\","
                 << "\"has_summary\":" << (state.has_summary ? "true" : "false") << ","
                 << "\"round_number\":" << (state.has_summary ? std::to_string(state.summary.round_number) : "0") << ","
                 << "\"mission_decision\":\"" <<
        json_escape(state.has_summary ? state.summary.mission_decision : "pending") << "\","
                 << "\"anomaly_count\":" <<
        (state.has_summary ? std::to_string(state.summary.anomaly_count) : "0") << ","
                 << "\"critical_count\":" <<
        (state.has_summary ? std::to_string(state.summary.critical_count) : "0") << ","
                 << "\"lowest_health_score\":" <<
        (state.has_summary ? std::to_string(state.summary.lowest_health_score) : "100.0") << ","
                 << "\"last_checkpoint\":\"" <<
        json_escape(state.has_inspection ? state.inspection.checkpoint_name : "waiting") << "\","
                 << "\"last_label\":\"" <<
        json_escape(state.has_inspection ? state.inspection.inspection_label : "waiting") << "\""
                 << "}";

      rows_html
        << "<tr>"
        << "<td>" << html_escape(robot_name) << "</td>"
        << "<td>" << (state.has_summary ? std::to_string(state.summary.round_number) : "-") << "</td>"
        << "<td>" << html_escape(state.has_summary ? state.summary.mission_decision : "pending") << "</td>"
        << "<td>" << (state.has_summary ? std::to_string(state.summary.anomaly_count) : "-") << "</td>"
        << "<td>" << (state.has_summary ? std::to_string(state.summary.critical_count) : "-") << "</td>"
        << "<td>" << html_escape(state.has_inspection ? state.inspection.checkpoint_name : "waiting") << "</td>"
        << "<td>" << html_escape(state.has_inspection ? state.inspection.inspection_label : "waiting") << "</td>"
        << "</tr>\n";
    }

    std::ofstream json_file(report_dir_ / "latest_fleet_state.json");
    json_file
      << "{\n"
      << "  \"reporting_robot_count\": " << reporting_robots << ",\n"
      << "  \"holding_robot_count\": " << holding_robots << ",\n"
      << "  \"total_anomalies\": " << total_anomalies << ",\n"
      << "  \"total_critical\": " << total_critical << ",\n"
      << "  \"total_reviews\": " << total_reviews << ",\n"
      << "  \"robots\": [" << robots_json.str() << "\n  ]\n"
      << "}\n";

    std::ofstream html_file(report_dir_ / "latest_fleet_dashboard.html");
    html_file
      << "<!doctype html><html><head><meta charset='utf-8'>"
      << "<title>Fleet Dashboard</title>"
      << "<style>"
      << "body{font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:24px;}"
      << ".cards{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px;}"
      << ".card{background:#1e293b;padding:16px 20px;border-radius:12px;min-width:180px;}"
      << "table{width:100%;border-collapse:collapse;background:#111827;border-radius:12px;overflow:hidden;}"
      << "th,td{padding:12px 14px;border-bottom:1px solid #1f2937;text-align:left;}"
      << "th{background:#1f2937;color:#93c5fd;}"
      << "</style></head><body>"
      << "<h1>Factory Inspection Fleet Dashboard</h1>"
      << "<div class='cards'>"
      << "<div class='card'><strong>Reporting Robots</strong><br/>" << reporting_robots << "</div>"
      << "<div class='card'><strong>Holding Robots</strong><br/>" << holding_robots << "</div>"
      << "<div class='card'><strong>Total Anomalies</strong><br/>" << total_anomalies << "</div>"
      << "<div class='card'><strong>Total Critical</strong><br/>" << total_critical << "</div>"
      << "<div class='card'><strong>Total Reviews</strong><br/>" << total_reviews << "</div>"
      << "</div>"
      << "<table><thead><tr>"
      << "<th>Robot</th><th>Round</th><th>Decision</th><th>Anomalies</th><th>Critical</th>"
      << "<th>Last Checkpoint</th><th>Last Label</th>"
      << "</tr></thead><tbody>"
      << rows_html.str()
      << "</tbody></table></body></html>\n";
  }

  std::vector<std::string> robot_names_;
  std::filesystem::path report_dir_;
  std::map<std::string, RobotState> robot_states_;
  std::vector<rclcpp::Subscription<InspectionResult>::SharedPtr> inspection_subscriptions_;
  std::vector<rclcpp::Subscription<PatrolRoundSummary>::SharedPtr> summary_subscriptions_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<FleetSupervisorNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
