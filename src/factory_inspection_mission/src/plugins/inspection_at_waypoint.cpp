#include "factory_inspection_mission/inspection_at_waypoint.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <exception>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <vector>

#include "cv_bridge/cv_bridge.hpp"
#include "factory_inspection_interfaces/msg/inspection_result.hpp"
#include "opencv2/imgcodecs.hpp"
#include "opencv2/imgproc.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "sensor_msgs/image_encodings.hpp"
#include "visualization_msgs/msg/marker.hpp"
#include "yaml-cpp/yaml.h"

namespace factory_inspection_mission
{

namespace
{

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

std::string normalize_severity(const std::string & value)
{
  const auto normalized = lowercase_copy(value);
  if (normalized == "critical") {
    return "critical";
  }
  if (normalized == "warning" || normalized == "warn") {
    return "warning";
  }
  return "normal";
}

bool is_anomaly_severity(const std::string & severity)
{
  return normalize_severity(severity) != "normal";
}

int severity_rank_local(const std::string & severity)
{
  const auto normalized = normalize_severity(severity);
  if (normalized == "critical") {
    return 2;
  }
  if (normalized == "warning") {
    return 1;
  }
  return 0;
}

std::string normalize_inspection_mode(const std::string & value)
{
  const auto normalized = lowercase_copy(value);
  if (
    normalized == "visual_station" || normalized == "station" || normalized == "stack_light" ||
    normalized == "signal_station")
  {
    return "visual_station";
  }
  if (normalized == "visual_gauge" || normalized == "vision_gauge" || normalized == "gauge") {
    return "visual_gauge";
  }
  return "fixed";
}

std::string action_for_severity(const std::string & severity)
{
  const auto normalized = normalize_severity(severity);
  if (normalized == "critical") {
    return "dispatch_operator_immediately";
  }
  if (normalized == "warning") {
    return "schedule_recheck";
  }
  return "continue_patrol";
}

bool matches_ground_truth_condition(
  const std::string & ground_truth_label,
  const std::string & ground_truth_severity,
  const std::string & predicted_label,
  const std::string & predicted_severity)
{
  if (ground_truth_label.empty()) {
    return false;
  }

  const auto truth_severity = normalize_severity(ground_truth_severity);
  const auto predicted = normalize_severity(predicted_severity);
  if (truth_severity == "normal") {
    return predicted == "normal";
  }

  return predicted_label == ground_truth_label || predicted == truth_severity;
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

std::vector<std::string> parse_string_list(const YAML::Node & node)
{
  std::vector<std::string> values;
  if (!node) {
    return values;
  }

  if (node.IsSequence()) {
    values.reserve(node.size());
    for (const auto & entry : node) {
      values.push_back(entry.as<std::string>());
    }
    return values;
  }

  if (node.IsScalar()) {
    values.push_back(node.as<std::string>());
  }
  return values;
}

bool has_value(const std::vector<std::string> & values, const std::string & expected)
{
  return std::find(values.begin(), values.end(), expected) != values.end();
}

float clamp_confidence(const double value)
{
  return static_cast<float>(std::clamp(value, 0.05, 0.99));
}

bool is_visual_only_anomaly(const std::vector<std::string> & anomaly_sources)
{
  return anomaly_sources.size() == 1U && anomaly_sources.front() == "visual";
}

bool asset_requires_multimodal_confirmation(const std::string & asset_type)
{
  const auto normalized_type = lowercase_copy(asset_type);
  return
    normalized_type == "pump" ||
    normalized_type == "compressor" ||
    normalized_type == "electrical_panel" ||
    normalized_type == "conveyor_drive";
}

std::string worst_severity(
  const std::string & a,
  const std::string & b,
  const std::string & c = "normal",
  const std::string & d = "normal")
{
  const std::vector<std::string> values = {
    normalize_severity(a),
    normalize_severity(b),
    normalize_severity(c),
    normalize_severity(d),
  };

  std::string best = "normal";
  int best_rank = severity_rank_local(best);
  for (const auto & value : values) {
    const int rank = severity_rank_local(value);
    if (rank > best_rank) {
      best_rank = rank;
      best = value;
    }
  }
  return best;
}

float compute_health_score(
  const std::string & severity,
  const bool thermal_alert,
  const bool acoustic_alert,
  const bool gas_alert,
  const double thermal_delta_c,
  const double acoustic_db,
  const double gas_ppm)
{
  double score = 100.0;

  const auto normalized = normalize_severity(severity);
  if (normalized == "critical") {
    score -= 38.0;
  } else if (normalized == "warning") {
    score -= 18.0;
  }

  if (thermal_alert) {
    score -= std::min(20.0, std::max(6.0, thermal_delta_c * 0.55));
  }
  if (acoustic_alert) {
    score -= std::min(16.0, std::max(5.0, (acoustic_db - 60.0) * 0.45));
  }
  if (gas_alert) {
    score -= std::min(28.0, std::max(8.0, gas_ppm * 0.28));
  }

  if (score < 0.0) {
    score = 0.0;
  }
  return static_cast<float>(score);
}

float compute_inspection_confidence(
  const std::string & severity,
  const bool capture_ok,
  const bool visual_confident,
  const std::vector<std::string> & anomaly_sources,
  const bool review_required)
{
  double confidence = 0.18;

  if (capture_ok) {
    confidence += 0.28;
  }
  if (visual_confident) {
    confidence += 0.12;
  }

  const auto normalized_severity = normalize_severity(severity);
  if (normalized_severity == "normal") {
    confidence += anomaly_sources.empty() ? 0.24 : 0.12;
  } else {
    confidence += 0.10;
    confidence += 0.16 * static_cast<double>(std::min<std::size_t>(anomaly_sources.size(), 3U));
  }

  if (review_required) {
    confidence -= 0.28;
  }

  return clamp_confidence(confidence);
}

std::string asset_status_for_score(const std::string & severity, const float health_score)
{
  const auto normalized = normalize_severity(severity);
  if (normalized == "critical" || health_score < 35.0F) {
    return "critical_shutdown";
  }
  if (normalized == "warning" || health_score < 65.0F) {
    return "needs_service";
  }
  if (health_score < 82.0F) {
    return "watchlist";
  }
  return "healthy";
}

std::string infer_issue_label(
  const std::string & asset_type,
  const std::string & fused_severity,
  const bool thermal_alert,
  const bool acoustic_alert,
  const bool gas_alert,
  const std::string & visual_label)
{
  const auto normalized_type = lowercase_copy(asset_type);
  const auto normalized_severity = normalize_severity(fused_severity);
  if (normalized_severity == "normal") {
    return "asset_nominal";
  }

  if (normalized_type == "pump") {
    return normalized_severity == "critical" ? "bearing_overheat" : "bearing_warmup";
  }
  if (normalized_type == "compressor") {
    return gas_alert ? "gas_leak_detected" : "belt_slip";
  }
  if (normalized_type == "electrical_panel") {
    return normalized_severity == "critical" ? "panel_arc_risk" : "cabinet_hotspot";
  }
  if (normalized_type == "valve_manifold") {
    return gas_alert ? "seal_leak" : "actuator_hunt";
  }
  if (normalized_type == "conveyor_drive") {
    return normalized_severity == "critical" ? "motor_overtemp" : "roller_imbalance";
  }

  if (gas_alert) {
    return "gas_leak_detected";
  }
  if (thermal_alert && acoustic_alert) {
    return normalized_severity == "critical" ? "equipment_distress" : "equipment_warning";
  }
  return visual_label.empty() ? "asset_attention_required" : visual_label;
}

void apply_review_policy(
  const std::string & asset_type,
  const bool capture_ok,
  std::vector<std::string> & anomaly_sources,
  std::string & inspection_label,
  std::string & inspection_severity,
  std::string & recommended_action,
  std::string & asset_status,
  bool & review_required,
  std::string & review_reason)
{
  if (!capture_ok) {
    review_required = true;
    review_reason = "capture_failed";
    return;
  }

  if (
    !anomaly_sources.empty() &&
    is_visual_only_anomaly(anomaly_sources) &&
    asset_requires_multimodal_confirmation(asset_type))
  {
    const auto original_label = inspection_label;
    review_required = true;
    review_reason =
      "visual_only_" + original_label + "_needs_multimodal_confirmation";
    inspection_label = "unconfirmed_visual_finding";
    inspection_severity = "normal";
    recommended_action = "schedule_targeted_rescan";
    asset_status = "watchlist";
  }
}

std::string channel_severity(
  const double value,
  const double warning_threshold,
  const double critical_multiplier = 1.35)
{
  if (warning_threshold <= 0.0) {
    return "normal";
  }

  if (value >= warning_threshold * critical_multiplier) {
    return "critical";
  }
  if (value >= warning_threshold) {
    return "warning";
  }
  return "normal";
}

struct GaugeClassification
{
  bool success{false};
  double angle_deg{0.0};
  cv::Rect roi;
  cv::Point center;
  cv::Point tip;
  std::string inspection_label{"gauge_unreadable"};
  std::string inspection_severity{"warning"};
  std::string recommended_action{"manual_review"};
  std::string debug_note{"visual_gauge_unreadable"};
};

struct StationClassification
{
  bool success{false};
  cv::Rect roi;
  cv::Rect dominant_bbox;
  std::string dominant_color{"unknown"};
  int red_pixels{0};
  int yellow_pixels{0};
  int green_pixels{0};
  std::string inspection_label{"station_unreadable"};
  std::string inspection_severity{"warning"};
  std::string recommended_action{"manual_review"};
  std::string debug_note{"visual_station_unreadable"};
};

cv::Mat color_mask(
  const cv::Mat & hsv_image,
  const cv::Scalar & low_a,
  const cv::Scalar & high_a,
  const bool use_second_range = false,
  const cv::Scalar & low_b = cv::Scalar(),
  const cv::Scalar & high_b = cv::Scalar())
{
  cv::Mat first;
  cv::inRange(hsv_image, low_a, high_a, first);

  if (!use_second_range) {
    return first;
  }

  cv::Mat second;
  cv::inRange(hsv_image, low_b, high_b, second);
  return first | second;
}

cv::Rect dominant_component_bbox(const cv::Mat & mask)
{
  cv::Mat labels;
  cv::Mat stats;
  cv::Mat centroids;
  const int components =
    cv::connectedComponentsWithStats(mask, labels, stats, centroids, 8, CV_32S);

  int best_component = -1;
  int best_area = 0;
  for (int index = 1; index < components; ++index) {
    const int area = stats.at<int>(index, cv::CC_STAT_AREA);
    if (area > best_area) {
      best_area = area;
      best_component = index;
    }
  }

  if (best_component < 0) {
    return cv::Rect();
  }

  return cv::Rect(
    stats.at<int>(best_component, cv::CC_STAT_LEFT),
    stats.at<int>(best_component, cv::CC_STAT_TOP),
    stats.at<int>(best_component, cv::CC_STAT_WIDTH),
    stats.at<int>(best_component, cv::CC_STAT_HEIGHT));
}

StationClassification classify_visual_station(const cv::Mat & image)
{
  StationClassification result;
  if (image.empty()) {
    result.debug_note = "visual_station_unreadable:image_empty";
    return result;
  }

  struct Candidate
  {
    std::string color{"unknown"};
    cv::Rect roi;
    cv::Rect local_bbox;
    int red_pixels{0};
    int yellow_pixels{0};
    int green_pixels{0};
    int dominant_pixels{0};
    double score{0.0};
  };

  auto clamp_roi = [&image](const double x_ratio, const double y_ratio, const double w_ratio,
    const double h_ratio) {
      const int roi_x = static_cast<int>(std::round(image.cols * x_ratio));
      const int roi_y = static_cast<int>(std::round(image.rows * y_ratio));
      const int roi_w = std::min(
        static_cast<int>(std::round(image.cols * w_ratio)),
        image.cols - roi_x);
      const int roi_h = std::min(
        static_cast<int>(std::round(image.rows * h_ratio)),
        image.rows - roi_y);
      return cv::Rect(
        std::max(0, roi_x),
        std::max(0, roi_y),
        std::max(1, roi_w),
        std::max(1, roi_h));
    };

  auto score_component = [](const int pixel_count, const cv::Rect & bbox, const cv::Rect & roi) {
      if (pixel_count <= 0 || bbox.area() <= 0) {
        return 0.0;
      }

      const double center_x = bbox.x + (bbox.width * 0.5);
      const double center_y = bbox.y + (bbox.height * 0.5);
      const double horizontal_distance = std::abs(center_x - (roi.width * 0.5)) /
        std::max(roi.width * 0.5, 1.0);
      const double vertical_position = center_y / std::max<double>(roi.height, 1.0);
      const double compactness = static_cast<double>(bbox.area()) /
        std::max<double>(pixel_count, 1.0);
      const double vertical_distance = std::abs(vertical_position - 0.42);
      const double position_bonus = (1.45 - (0.55 * horizontal_distance)) *
        (1.55 - (1.10 * vertical_distance));
      return pixel_count * std::max(0.35, position_bonus) * std::max(0.55, compactness);
    };

  auto evaluate_roi = [&](const cv::Rect & roi) {
      Candidate candidate;
      candidate.roi = roi;

      const cv::Mat roi_image = image(roi);
      cv::Mat hsv_image;
      cv::cvtColor(roi_image, hsv_image, cv::COLOR_BGR2HSV);

      auto red_mask = color_mask(
        hsv_image,
        cv::Scalar(0, 120, 110),
        cv::Scalar(12, 255, 255),
        true,
        cv::Scalar(168, 120, 110),
        cv::Scalar(180, 255, 255));
      auto yellow_mask = color_mask(
        hsv_image,
        cv::Scalar(16, 100, 120),
        cv::Scalar(42, 255, 255));
      auto green_mask = color_mask(
        hsv_image,
        cv::Scalar(42, 70, 80),
        cv::Scalar(96, 255, 255));

      const auto kernel = cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(3, 3));
      for (cv::Mat * mask : {&red_mask, &yellow_mask, &green_mask}) {
        cv::morphologyEx(*mask, *mask, cv::MORPH_OPEN, kernel);
        cv::dilate(*mask, *mask, kernel);
      }

      candidate.red_pixels = cv::countNonZero(red_mask);
      candidate.yellow_pixels = cv::countNonZero(yellow_mask);
      candidate.green_pixels = cv::countNonZero(green_mask);

      const cv::Rect red_bbox = dominant_component_bbox(red_mask);
      const cv::Rect yellow_bbox = dominant_component_bbox(yellow_mask);
      const cv::Rect green_bbox = dominant_component_bbox(green_mask);

      const double red_score = score_component(candidate.red_pixels, red_bbox, roi);
      const double yellow_score = score_component(candidate.yellow_pixels, yellow_bbox, roi);
      const double green_score = score_component(candidate.green_pixels, green_bbox, roi);

      if (red_score >= yellow_score && red_score >= green_score) {
        candidate.color = "red";
        candidate.local_bbox = red_bbox;
        candidate.dominant_pixels = candidate.red_pixels;
        candidate.score = red_score;
      } else if (yellow_score >= red_score && yellow_score >= green_score) {
        candidate.color = "yellow";
        candidate.local_bbox = yellow_bbox;
        candidate.dominant_pixels = candidate.yellow_pixels;
        candidate.score = yellow_score;
      } else {
        candidate.color = "green";
        candidate.local_bbox = green_bbox;
        candidate.dominant_pixels = candidate.green_pixels;
        candidate.score = green_score;
      }

      return candidate;
    };

  const std::vector<cv::Rect> candidate_rois = {
    clamp_roi(0.24, 0.16, 0.52, 0.42),
    clamp_roi(0.18, 0.12, 0.64, 0.54),
  };

  Candidate best_candidate;
  for (const auto & roi : candidate_rois) {
    const Candidate candidate = evaluate_roi(roi);
    if (candidate.score > best_candidate.score) {
      best_candidate = candidate;
    }
  }

  result.roi = best_candidate.roi;
  result.red_pixels = best_candidate.red_pixels;
  result.yellow_pixels = best_candidate.yellow_pixels;
  result.green_pixels = best_candidate.green_pixels;

  if (best_candidate.dominant_pixels < 60 || best_candidate.score < 70.0) {
    std::ostringstream debug;
    debug << "visual_station_unreadable"
          << ":red=" << result.red_pixels
          << " yellow=" << result.yellow_pixels
          << " green=" << result.green_pixels
          << " score=" << std::fixed << std::setprecision(1) << best_candidate.score;
    result.debug_note = debug.str();
    return result;
  }

  result.dominant_color = best_candidate.color;
  if (best_candidate.color == "red") {
    result.inspection_label = "red_stack_alarm";
    result.inspection_severity = "critical";
  } else if (best_candidate.color == "yellow") {
    result.inspection_label = "yellow_stack_alert";
    result.inspection_severity = "warning";
  } else {
    result.inspection_label = "station_nominal";
    result.inspection_severity = "normal";
  }

  result.recommended_action = action_for_severity(result.inspection_severity);
  result.success = true;
  if (best_candidate.local_bbox.area() > 0) {
    result.dominant_bbox = cv::Rect(
      best_candidate.local_bbox.x + result.roi.x,
      best_candidate.local_bbox.y + result.roi.y,
      best_candidate.local_bbox.width,
      best_candidate.local_bbox.height);
  }

  std::ostringstream debug;
  debug << "visual_station color=" << result.dominant_color
        << " red=" << result.red_pixels
        << " yellow=" << result.yellow_pixels
        << " green=" << result.green_pixels
        << " score=" << std::fixed << std::setprecision(1) << best_candidate.score;
  result.debug_note = debug.str();
  return result;
}

void annotate_visual_station(
  cv::Mat & image,
  const StationClassification & classification,
  const std::string & predicted_label,
  const std::string & ground_truth_label,
  const std::string & note)
{
  if (image.empty()) {
    return;
  }

  if (classification.roi.area() > 0) {
    cv::rectangle(image, classification.roi, cv::Scalar(0, 255, 255), 2);
  }
  if (classification.dominant_bbox.area() > 0) {
    cv::rectangle(image, classification.dominant_bbox, cv::Scalar(0, 255, 0), 2);
  }

  cv::rectangle(image, cv::Rect(4, 4, image.cols - 8, 42), cv::Scalar(18, 33, 45), cv::FILLED);
  cv::putText(
    image,
    "predicted=" + predicted_label + " truth=" + ground_truth_label,
    cv::Point(12, 22),
    cv::FONT_HERSHEY_SIMPLEX,
    0.45,
    cv::Scalar(245, 246, 248),
    1,
    cv::LINE_AA);
  cv::putText(
    image,
    note,
    cv::Point(12, 39),
    cv::FONT_HERSHEY_SIMPLEX,
    0.40,
    cv::Scalar(220, 226, 232),
    1,
    cv::LINE_AA);
}

GaugeClassification classify_visual_gauge(const cv::Mat & image)
{
  GaugeClassification result;
  if (image.empty()) {
    result.debug_note = "visual_gauge_unreadable:image_empty";
    return result;
  }

  cv::Mat hsv_image;
  cv::cvtColor(image, hsv_image, cv::COLOR_BGR2HSV);

  cv::Mat lower_red_mask;
  cv::Mat upper_red_mask;
  cv::inRange(hsv_image, cv::Scalar(0, 110, 70), cv::Scalar(12, 255, 255), lower_red_mask);
  cv::inRange(hsv_image, cv::Scalar(170, 110, 70), cv::Scalar(180, 255, 255), upper_red_mask);

  cv::Mat red_mask = lower_red_mask | upper_red_mask;
  cv::morphologyEx(
    red_mask,
    red_mask,
    cv::MORPH_OPEN,
    cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(3, 3)));
  cv::dilate(
    red_mask,
    red_mask,
    cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(3, 3)));

  const int red_pixels = cv::countNonZero(red_mask);
  if (red_pixels < 45) {
    std::ostringstream debug;
    debug << "visual_gauge_unreadable:red_pixels=" << red_pixels;
    result.debug_note = debug.str();
    return result;
  }

  cv::Mat distance_map;
  cv::distanceTransform(red_mask, distance_map, cv::DIST_L2, 3);

  double max_distance = 0.0;
  cv::Point pivot;
  cv::minMaxLoc(distance_map, nullptr, &max_distance, nullptr, &pivot);
  if (max_distance < 2.0) {
    std::ostringstream debug;
    debug << "visual_gauge_unreadable:distance_peak=" << std::fixed << std::setprecision(2) <<
      max_distance;
    result.debug_note = debug.str();
    return result;
  }

  result.center = pivot;

  const double min_radius = std::max(max_distance * 2.0, 10.0);
  const double max_radius = std::min(
    std::hypot(static_cast<double>(image.cols), static_cast<double>(image.rows)) * 0.55,
    180.0);

  double best_radius = -1.0;
  cv::Point best_tip = pivot;
  std::vector<cv::Point> red_points;
  red_points.reserve(static_cast<std::size_t>(red_pixels));

  for (int y = 0; y < red_mask.rows; ++y) {
    for (int x = 0; x < red_mask.cols; ++x) {
      if (red_mask.at<std::uint8_t>(y, x) == 0U) {
        continue;
      }

      red_points.emplace_back(x, y);
      const double radius = std::hypot(
        static_cast<double>(x - pivot.x),
        static_cast<double>(y - pivot.y));
      if (radius >= min_radius && radius <= max_radius && radius > best_radius) {
        best_radius = radius;
        best_tip = cv::Point(x, y);
      }
    }
  }

  if (best_radius < 0.0) {
    std::ostringstream debug;
    debug << "visual_gauge_unreadable:tip_not_found red_pixels=" << red_pixels;
    result.debug_note = debug.str();
    return result;
  }

  const auto red_bounds = cv::boundingRect(red_points);
  const int roi_side = std::max(
    96,
    std::max(
      red_bounds.width,
      red_bounds.height) + 110);
  const int roi_x = std::clamp(pivot.x - roi_side / 2, 0, std::max(0, image.cols - roi_side));
  const int roi_y = std::clamp(pivot.y - roi_side / 2, 0, std::max(0, image.rows - roi_side));
  result.roi = cv::Rect(
    roi_x,
    roi_y,
    std::min(roi_side, image.cols - roi_x),
    std::min(roi_side, image.rows - roi_y));

  result.tip = best_tip;
  result.angle_deg = std::atan2(
    static_cast<double>(pivot.y - best_tip.y),
    static_cast<double>(best_tip.x - pivot.x)) * 180.0 / M_PI;
  if (result.angle_deg < 0.0) {
    result.angle_deg += 360.0;
  }

  if (result.angle_deg >= 140.0) {
    result.inspection_label = "gauge_nominal";
    result.inspection_severity = "normal";
  } else if (result.angle_deg >= 60.0) {
    result.inspection_label = "needle_drift";
    result.inspection_severity = "warning";
  } else {
    result.inspection_label = "gauge_high_alarm";
    result.inspection_severity = "critical";
  }

  result.recommended_action = action_for_severity(result.inspection_severity);
  std::ostringstream debug;
  debug << "visual_gauge angle_deg=" << std::fixed << std::setprecision(1) << result.angle_deg;
  result.debug_note = debug.str();
  result.success = true;
  return result;
}

void annotate_visual_gauge(
  cv::Mat & image,
  const GaugeClassification & classification,
  const std::string & predicted_label,
  const std::string & expected_label,
  const std::string & note)
{
  if (image.empty()) {
    return;
  }

  if (classification.roi.area() > 0) {
    cv::rectangle(image, classification.roi, cv::Scalar(0, 255, 255), 2);
  }
  if (classification.success) {
    cv::circle(image, classification.center, 4, cv::Scalar(255, 255, 0), cv::FILLED);
    cv::circle(image, classification.tip, 5, cv::Scalar(0, 255, 0), cv::FILLED);
    cv::line(image, classification.center, classification.tip, cv::Scalar(0, 255, 255), 2);
  }

  cv::rectangle(image, cv::Rect(4, 4, image.cols - 8, 42), cv::Scalar(18, 33, 45), cv::FILLED);
  cv::putText(
    image,
    "predicted=" + predicted_label + " expected=" + expected_label,
    cv::Point(12, 22),
    cv::FONT_HERSHEY_SIMPLEX,
    0.45,
    cv::Scalar(245, 246, 248),
    1,
    cv::LINE_AA);
  cv::putText(
    image,
    note,
    cv::Point(12, 39),
    cv::FONT_HERSHEY_SIMPLEX,
    0.40,
    cv::Scalar(220, 226, 232),
    1,
    cv::LINE_AA);
}

}  // namespace

void InspectionAtWaypoint::initialize(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  const std::string & plugin_name)
{
  parent_node_ = parent.lock();
  if (!parent_node_) {
    throw std::runtime_error("InspectionAtWaypoint failed to lock parent lifecycle node.");
  }

  logger_ = parent_node_->get_logger();

  parent_node_->declare_parameter(plugin_name + ".enabled", true);
  parent_node_->declare_parameter(plugin_name + ".image_topic", "rgbd_camera/image");
  parent_node_->declare_parameter(plugin_name + ".image_format", "png");
  parent_node_->declare_parameter(plugin_name + ".mission_config_file", "");
  parent_node_->declare_parameter(plugin_name + ".save_dir", "");
  parent_node_->declare_parameter(plugin_name + ".csv_filename", "inspection_log.csv");
  parent_node_->declare_parameter(plugin_name + ".fail_on_capture_error", false);
  parent_node_->declare_parameter(plugin_name + ".marker_topic", "inspection_markers");
  parent_node_->declare_parameter(plugin_name + ".capture_settle_seconds", 0.35);
  parent_node_->declare_parameter(plugin_name + ".checkpoint_match_distance_tolerance", 1.75);
  parent_node_->declare_parameter(plugin_name + ".checkpoint_match_yaw_weight", 0.20);

  enabled_ = parent_node_->get_parameter(plugin_name + ".enabled").as_bool();
  image_topic_ = parent_node_->get_parameter(plugin_name + ".image_topic").as_string();
  image_format_ = parent_node_->get_parameter(plugin_name + ".image_format").as_string();
  fail_on_capture_error_ =
    parent_node_->get_parameter(plugin_name + ".fail_on_capture_error").as_bool();
  marker_topic_ = parent_node_->get_parameter(plugin_name + ".marker_topic").as_string();
  capture_settle_seconds_ =
    parent_node_->get_parameter(plugin_name + ".capture_settle_seconds").as_double();
  checkpoint_match_distance_tolerance_ =
    parent_node_->get_parameter(plugin_name + ".checkpoint_match_distance_tolerance").as_double();
  checkpoint_match_yaw_weight_ =
    parent_node_->get_parameter(plugin_name + ".checkpoint_match_yaw_weight").as_double();

  const auto config_file =
    parent_node_->get_parameter(plugin_name + ".mission_config_file").as_string();
  if (config_file.empty()) {
    throw std::runtime_error(
            "InspectionAtWaypoint requires a non-empty mission_config_file parameter.");
  }

  const auto save_dir =
    parent_node_->get_parameter(plugin_name + ".save_dir").as_string();
  if (save_dir.empty()) {
    throw std::runtime_error("InspectionAtWaypoint requires a non-empty save_dir parameter.");
  }

  save_dir_ = std::filesystem::path(save_dir);
  std::filesystem::create_directories(save_dir_);
  csv_path_ = save_dir_ /
    parent_node_->get_parameter(plugin_name + ".csv_filename").as_string();

  load_checkpoint_config(config_file);
  initialize_csv();

  image_subscription_ = parent_node_->create_subscription<sensor_msgs::msg::Image>(
    image_topic_,
    rclcpp::SensorDataQoS(),
    std::bind(&InspectionAtWaypoint::image_callback, this, std::placeholders::_1));
  inspection_result_publisher_ =
    parent_node_->create_publisher<factory_inspection_interfaces::msg::InspectionResult>(
    "inspection_results",
    rclcpp::QoS(20).reliable());
  marker_publisher_ = rclcpp::create_publisher<visualization_msgs::msg::MarkerArray>(
    *parent_node_,
    marker_topic_,
    rclcpp::QoS(1).reliable().transient_local());
  publish_reset_markers();

  RCLCPP_INFO(
    logger_,
    "Inspection waypoint plugin ready. topic=%s marker_topic=%s save_dir=%s checkpoints=%zu fail_on_capture_error=%s checkpoint_match_distance=%.2f yaw_weight=%.2f",
    image_topic_.c_str(),
    marker_topic_.c_str(),
    save_dir_.string().c_str(),
    checkpoints_.size(),
    fail_on_capture_error_ ? "true" : "false",
    checkpoint_match_distance_tolerance_,
    checkpoint_match_yaw_weight_);
}

std::size_t InspectionAtWaypoint::select_checkpoint_index(
  const geometry_msgs::msg::PoseStamped & curr_pose,
  const std::size_t fallback_waypoint_index) const
{
  if (checkpoints_.empty()) {
    return std::numeric_limits<std::size_t>::max();
  }

  const double pose_x = curr_pose.pose.position.x;
  const double pose_y = curr_pose.pose.position.y;
  const double pose_yaw = quaternion_to_yaw(curr_pose.pose.orientation);

  std::size_t best_index = std::numeric_limits<std::size_t>::max();
  double best_distance = std::numeric_limits<double>::max();
  double best_score = std::numeric_limits<double>::max();

  for (std::size_t index = 0; index < checkpoints_.size(); ++index) {
    const auto & checkpoint = checkpoints_.at(index);
    const double dx = checkpoint.pose_x - pose_x;
    const double dy = checkpoint.pose_y - pose_y;
    const double distance = std::hypot(dx, dy);
    const double yaw_error = std::abs(
      std::atan2(
        std::sin(checkpoint.pose_yaw - pose_yaw),
        std::cos(checkpoint.pose_yaw - pose_yaw)));
    const double score = distance + (yaw_error * checkpoint_match_yaw_weight_);

    if (score < best_score) {
      best_score = score;
      best_distance = distance;
      best_index = index;
    }
  }

  if (
    best_index != std::numeric_limits<std::size_t>::max() &&
    (best_distance <= checkpoint_match_distance_tolerance_ || fallback_waypoint_index >= checkpoints_.size()))
  {
    return best_index;
  }

  return fallback_waypoint_index < checkpoints_.size() ?
         fallback_waypoint_index :
         std::numeric_limits<std::size_t>::max();
}

bool InspectionAtWaypoint::processAtWaypoint(
  const geometry_msgs::msg::PoseStamped & curr_pose,
  const int & curr_waypoint_index)
{
  if (!enabled_) {
    return true;
  }

  const auto waypoint_index = static_cast<std::size_t>(std::max(curr_waypoint_index, 0));
  if (waypoint_index == 0U && last_processed_waypoint_index_ != 0U) {
    ++current_round_number_;
  } else if (current_round_number_ == 0U) {
    current_round_number_ = 1U;
  }
  last_processed_waypoint_index_ = waypoint_index;

  InspectionCheckpoint checkpoint;
  checkpoint.name = "waypoint_" + std::to_string(waypoint_index);
  checkpoint.station_id = checkpoint.name;
  checkpoint.mission_profile = mission_profile_;
  checkpoint.asset_id = checkpoint.station_id;
  checkpoint.asset_display_name = checkpoint.name;
  checkpoint.asset_type = "generic_asset";
  checkpoint.zone = "unknown";
  checkpoint.asset_priority = 1U;
  checkpoint.inspection_mode = "fixed";
  checkpoint.inspection_label = "asset_nominal";
  checkpoint.inspection_severity = "normal";
  checkpoint.recommended_action = "continue_patrol";
  checkpoint.pose_x = curr_pose.pose.position.x;
  checkpoint.pose_y = curr_pose.pose.position.y;
  checkpoint.pose_yaw = quaternion_to_yaw(curr_pose.pose.orientation);
  const auto matched_checkpoint_index = select_checkpoint_index(curr_pose, waypoint_index);
  if (matched_checkpoint_index < checkpoints_.size()) {
    checkpoint = checkpoints_.at(matched_checkpoint_index);
  }

  if (capture_settle_seconds_ > 0.0) {
    rclcpp::sleep_for(std::chrono::duration_cast<std::chrono::nanoseconds>(
      std::chrono::duration<double>(capture_settle_seconds_)));
  }

  sensor_msgs::msg::Image::SharedPtr frame_msg;
  {
    std::lock_guard<std::mutex> lock(image_mutex_);
    frame_msg = latest_image_msg_;
  }

  const auto stamp = parent_node_->get_clock()->now();
  InspectionSnapshot inspection;
  inspection.checkpoint = checkpoint;
  inspection.checkpoint.inspection_label.clear();
  inspection.checkpoint.inspection_severity.clear();
  inspection.checkpoint.recommended_action.clear();
  std::string note = "mode=fixed_config";
  std::string image_path;
  std::string raw_image_path;
  std::string annotated_image_path;
  std::string ground_truth_label;
  std::string ground_truth_severity;
  bool matches_ground_truth = false;
  bool capture_ok = false;
  std::string visual_label = checkpoint.inspection_label;
  std::string visual_severity = checkpoint.inspection_severity;
  std::string visual_note = "fixed_config";
  bool visual_confident = false;
  bool annotate_station = false;
  bool annotate_gauge = false;
  StationClassification station_classification;
  GaugeClassification gauge_classification;

  GroundTruthStation truth;
  bool has_truth = false;

  const auto ground_truth_it = ground_truth_by_station_.find(checkpoint.station_id);
  if (ground_truth_it != ground_truth_by_station_.end()) {
    truth = ground_truth_it->second;
    has_truth = true;
    ground_truth_label = truth.label;
    ground_truth_severity = truth.severity;

    if (inspection.checkpoint.asset_id.empty() || inspection.checkpoint.asset_id == inspection.checkpoint.station_id) {
      inspection.checkpoint.asset_id = truth.asset_id;
    }
    if (inspection.checkpoint.asset_display_name.empty() || inspection.checkpoint.asset_display_name == inspection.checkpoint.name) {
      inspection.checkpoint.asset_display_name = truth.asset_display_name;
    }
    if (inspection.checkpoint.asset_type.empty() || inspection.checkpoint.asset_type == "generic_asset") {
      inspection.checkpoint.asset_type = truth.asset_type;
    }
    if (inspection.checkpoint.zone.empty() || inspection.checkpoint.zone == "unknown") {
      inspection.checkpoint.zone = truth.zone;
    }
    if (inspection.checkpoint.asset_priority == 1U && truth.asset_priority > 1U) {
      inspection.checkpoint.asset_priority = truth.asset_priority;
    }
    if (inspection.checkpoint.enabled_modalities.empty()) {
      inspection.checkpoint.enabled_modalities = truth.enabled_modalities;
    }

    inspection.thermal_delta_c = static_cast<float>(truth.thermal_delta_c);
    inspection.acoustic_db = static_cast<float>(truth.acoustic_db);
    inspection.gas_ppm = static_cast<float>(truth.gas_ppm);
  } else if (!checkpoint.inspection_label.empty()) {
    ground_truth_label = checkpoint.inspection_label;
    ground_truth_severity = checkpoint.inspection_severity;
  }

  if (!frame_msg) {
    note = "no frame received yet on " + image_topic_;
    visual_note = note;
  } else {
    try {
      auto cv_image = cv_bridge::toCvCopy(frame_msg, sensor_msgs::image_encodings::BGR8);
      if (cv_image->image.empty()) {
        visual_note = "received empty image matrix";
      } else {
        cv::Mat raw_image = cv_image->image.clone();
        cv::Mat annotated_image = raw_image.clone();
        if (checkpoint.inspection_mode == "visual_station") {
          station_classification = classify_visual_station(annotated_image);
          visual_confident = station_classification.success;
          visual_label = station_classification.success ? station_classification.inspection_label : "";
          visual_severity = station_classification.success ?
            station_classification.inspection_severity : "normal";
          visual_note = station_classification.debug_note;
          annotate_station = true;
        } else if (checkpoint.inspection_mode == "visual_gauge") {
          gauge_classification = classify_visual_gauge(annotated_image);
          visual_confident = gauge_classification.success;
          visual_label = gauge_classification.success ? gauge_classification.inspection_label : "";
          visual_severity = gauge_classification.success ?
            gauge_classification.inspection_severity : "normal";
          visual_note = gauge_classification.debug_note;
          annotate_gauge = true;
        } else {
          visual_confident = true;
          visual_note = "mode=fixed_config";
        }

        const bool thermal_enabled = has_value(inspection.checkpoint.enabled_modalities, "thermal");
        const bool acoustic_enabled = has_value(inspection.checkpoint.enabled_modalities, "acoustic");
        const bool gas_enabled = has_value(inspection.checkpoint.enabled_modalities, "gas");

        const std::string thermal_severity = thermal_enabled ?
          channel_severity(inspection.thermal_delta_c, has_truth ? truth.thermal_threshold_c : 18.0) :
          "normal";
        const std::string acoustic_severity = acoustic_enabled ?
          channel_severity(inspection.acoustic_db, has_truth ? truth.acoustic_threshold_db : 72.0) :
          "normal";
        const std::string gas_severity = gas_enabled ?
          channel_severity(inspection.gas_ppm, has_truth ? truth.gas_threshold_ppm : 45.0) :
          "normal";

        inspection.thermal_alert = thermal_severity != "normal";
        inspection.acoustic_alert = acoustic_severity != "normal";
        inspection.gas_alert = gas_severity != "normal";

        inspection.anomaly_sources.clear();
        if (visual_confident && is_anomaly_severity(visual_severity)) {
          inspection.anomaly_sources.push_back("visual");
        }
        if (inspection.thermal_alert) {
          inspection.anomaly_sources.push_back("thermal");
        }
        if (inspection.acoustic_alert) {
          inspection.anomaly_sources.push_back("acoustic");
        }
        if (inspection.gas_alert) {
          inspection.anomaly_sources.push_back("gas");
        }

        inspection.checkpoint.inspection_severity = worst_severity(
          visual_severity,
          thermal_severity,
          acoustic_severity,
          gas_severity);
        inspection.checkpoint.inspection_label = infer_issue_label(
          inspection.checkpoint.asset_type,
          inspection.checkpoint.inspection_severity,
          inspection.thermal_alert,
          inspection.acoustic_alert,
          inspection.gas_alert,
          visual_label);
        inspection.checkpoint.recommended_action =
          action_for_severity(inspection.checkpoint.inspection_severity);
        inspection.health_score = compute_health_score(
          inspection.checkpoint.inspection_severity,
          inspection.thermal_alert,
          inspection.acoustic_alert,
          inspection.gas_alert,
          inspection.thermal_delta_c,
          inspection.acoustic_db,
          inspection.gas_ppm);
        inspection.asset_status = asset_status_for_score(
          inspection.checkpoint.inspection_severity,
          inspection.health_score);
        apply_review_policy(
          inspection.checkpoint.asset_type,
          true,
          inspection.anomaly_sources,
          inspection.checkpoint.inspection_label,
          inspection.checkpoint.inspection_severity,
          inspection.checkpoint.recommended_action,
          inspection.asset_status,
          inspection.review_required,
          inspection.review_reason);
        inspection.inspection_confidence = compute_inspection_confidence(
          inspection.checkpoint.inspection_severity,
          true,
          visual_confident,
          inspection.anomaly_sources,
          inspection.review_required);
        matches_ground_truth = matches_ground_truth_condition(
          ground_truth_label,
          ground_truth_severity,
          inspection.checkpoint.inspection_label,
          inspection.checkpoint.inspection_severity);

        std::ostringstream note_builder;
        note_builder << visual_note
                     << " matched_checkpoint=" << checkpoint.name
                     << " fused=" << inspection.checkpoint.inspection_label
                     << " severity=" << inspection.checkpoint.inspection_severity
                     << " health=" << std::fixed << std::setprecision(1) << inspection.health_score
                     << " confidence=" << std::fixed << std::setprecision(2)
                     << inspection.inspection_confidence
                     << " sources=" <<
          (inspection.anomaly_sources.empty() ? std::string("none") :
          join_strings(inspection.anomaly_sources, "+"))
                     << " review=" << (inspection.review_required ? inspection.review_reason : "none")
                     << " truth=" << (ground_truth_label.empty() ? std::string("unknown") : ground_truth_label)
                     << " match=" << (matches_ground_truth ? "true" : "false");
        note = note_builder.str();

        if (annotate_station) {
          annotate_visual_station(
            annotated_image,
            station_classification,
            inspection.checkpoint.inspection_label,
            ground_truth_label,
            note);
        } else if (annotate_gauge) {
          annotate_visual_gauge(
            annotated_image,
            gauge_classification,
            inspection.checkpoint.inspection_label,
            ground_truth_label,
            note);
        }

        std::ostringstream file_stem;
        file_stem << std::setw(4) << std::setfill('0') << waypoint_index
                  << "_" << sanitize_label(checkpoint.name)
                  << "_" << sanitize_label(inspection.checkpoint.inspection_label)
                  << "_" << stamp.nanoseconds();

        const auto raw_output_path =
          save_dir_ / (file_stem.str() + "_raw." + image_format_);
        const auto annotated_output_path =
          save_dir_ / (file_stem.str() + "_annotated." + image_format_);
        const bool raw_saved = cv::imwrite(raw_output_path.string(), raw_image);
        const bool annotated_saved = cv::imwrite(annotated_output_path.string(), annotated_image);

        if (raw_saved) {
          raw_image_path = raw_output_path.string();
        }
        if (annotated_saved) {
          annotated_image_path = annotated_output_path.string();
        }
        capture_ok = raw_saved || annotated_saved;
        image_path = !annotated_image_path.empty() ? annotated_image_path : raw_image_path;

        if (!capture_ok) {
          note = "cv::imwrite returned false";
        } else if (!raw_saved || !annotated_saved) {
          note += " evidence_partial=true";
        }
      }
    } catch (const std::exception & error) {
      visual_note = error.what();
    }
  }

  if (inspection.checkpoint.inspection_label.empty()) {
    const bool thermal_enabled = has_value(inspection.checkpoint.enabled_modalities, "thermal");
    const bool acoustic_enabled = has_value(inspection.checkpoint.enabled_modalities, "acoustic");
    const bool gas_enabled = has_value(inspection.checkpoint.enabled_modalities, "gas");
    const std::string thermal_severity = thermal_enabled ?
      channel_severity(inspection.thermal_delta_c, has_truth ? truth.thermal_threshold_c : 18.0) :
      "normal";
    const std::string acoustic_severity = acoustic_enabled ?
      channel_severity(inspection.acoustic_db, has_truth ? truth.acoustic_threshold_db : 72.0) :
      "normal";
    const std::string gas_severity = gas_enabled ?
      channel_severity(inspection.gas_ppm, has_truth ? truth.gas_threshold_ppm : 45.0) :
      "normal";

    inspection.thermal_alert = thermal_severity != "normal";
    inspection.acoustic_alert = acoustic_severity != "normal";
    inspection.gas_alert = gas_severity != "normal";
    if (inspection.thermal_alert) {
      inspection.anomaly_sources.push_back("thermal");
    }
    if (inspection.acoustic_alert) {
      inspection.anomaly_sources.push_back("acoustic");
    }
    if (inspection.gas_alert) {
      inspection.anomaly_sources.push_back("gas");
    }
    inspection.checkpoint.inspection_severity = worst_severity(
      visual_severity,
      thermal_severity,
      acoustic_severity,
      gas_severity);
    inspection.checkpoint.inspection_label = infer_issue_label(
      inspection.checkpoint.asset_type,
      inspection.checkpoint.inspection_severity,
      inspection.thermal_alert,
      inspection.acoustic_alert,
      inspection.gas_alert,
      visual_label);
    inspection.checkpoint.recommended_action =
      action_for_severity(inspection.checkpoint.inspection_severity);
    inspection.health_score = compute_health_score(
      inspection.checkpoint.inspection_severity,
      inspection.thermal_alert,
      inspection.acoustic_alert,
      inspection.gas_alert,
      inspection.thermal_delta_c,
      inspection.acoustic_db,
      inspection.gas_ppm);
    inspection.asset_status = asset_status_for_score(
      inspection.checkpoint.inspection_severity,
      inspection.health_score);
    apply_review_policy(
      inspection.checkpoint.asset_type,
      true,
      inspection.anomaly_sources,
      inspection.checkpoint.inspection_label,
      inspection.checkpoint.inspection_severity,
      inspection.checkpoint.recommended_action,
      inspection.asset_status,
      inspection.review_required,
      inspection.review_reason);
    inspection.inspection_confidence = compute_inspection_confidence(
      inspection.checkpoint.inspection_severity,
      capture_ok,
      visual_confident,
      inspection.anomaly_sources,
      inspection.review_required);
    matches_ground_truth = matches_ground_truth_condition(
      ground_truth_label,
      ground_truth_severity,
      inspection.checkpoint.inspection_label,
      inspection.checkpoint.inspection_severity);

    std::ostringstream note_builder;
    note_builder << visual_note
                 << " fused=" << inspection.checkpoint.inspection_label
                 << " severity=" << inspection.checkpoint.inspection_severity
                 << " health=" << std::fixed << std::setprecision(1) << inspection.health_score
                 << " confidence=" << std::fixed << std::setprecision(2)
                 << inspection.inspection_confidence
                 << " sources=" <<
      (inspection.anomaly_sources.empty() ? std::string("none") :
      join_strings(inspection.anomaly_sources, "+"))
                 << " review=" << (inspection.review_required ? inspection.review_reason : "none")
                 << " truth=" << (ground_truth_label.empty() ? std::string("unknown") : ground_truth_label)
                 << " match=" << (matches_ground_truth ? "true" : "false");
    note = note_builder.str();
  }

  if (!capture_ok && !inspection.review_required) {
    inspection.review_required = true;
    inspection.review_reason = "capture_failed";
  }
  if (inspection.review_required && inspection.asset_status == "healthy") {
    inspection.asset_status = "watchlist";
  }
  if (inspection.inspection_confidence <= 0.0F) {
    inspection.inspection_confidence = compute_inspection_confidence(
      inspection.checkpoint.inspection_severity,
      capture_ok,
      visual_confident,
      inspection.anomaly_sources,
      inspection.review_required);
  }

  append_csv_row(
    stamp,
    waypoint_index,
    inspection,
    capture_ok,
    image_path,
    raw_image_path,
    annotated_image_path,
    ground_truth_label,
    ground_truth_severity,
    matches_ground_truth,
    note,
    curr_pose);
  publish_inspection_result(
    stamp,
    waypoint_index,
    inspection,
    capture_ok,
    image_path,
    raw_image_path,
    annotated_image_path,
    ground_truth_label,
    ground_truth_severity,
    matches_ground_truth,
    note,
    curr_pose);
  publish_result_marker(
    stamp,
    waypoint_index,
    inspection,
    capture_ok,
    note,
    curr_pose);

  if (capture_ok) {
    RCLCPP_INFO(
      logger_,
      "Inspection saved at checkpoint %s (index %zu) -> asset=%s label=%s severity=%s health=%.1f confidence=%.2f review=%s image=%s",
      inspection.checkpoint.name.c_str(),
      waypoint_index,
      inspection.checkpoint.asset_id.c_str(),
      inspection.checkpoint.inspection_label.c_str(),
      inspection.checkpoint.inspection_severity.c_str(),
      inspection.health_score,
      inspection.inspection_confidence,
      inspection.review_required ? inspection.review_reason.c_str() : "none",
      image_path.c_str());
    return true;
  }

  RCLCPP_WARN(
    logger_,
    "Inspection capture issue at checkpoint %s (index %zu) -> asset=%s label=%s severity=%s note=%s",
    inspection.checkpoint.name.c_str(),
    waypoint_index,
    inspection.checkpoint.asset_id.c_str(),
    inspection.checkpoint.inspection_label.c_str(),
    inspection.checkpoint.inspection_severity.c_str(),
    note.c_str());
  return !fail_on_capture_error_;
}

void InspectionAtWaypoint::image_callback(const sensor_msgs::msg::Image::SharedPtr msg)
{
  std::lock_guard<std::mutex> lock(image_mutex_);
  latest_image_msg_ = msg;
}

void InspectionAtWaypoint::load_checkpoint_config(const std::string & config_file)
{
  const YAML::Node config = YAML::LoadFile(config_file);
  scenario_id_ = config["scenario_id"] ?
    config["scenario_id"].as<std::string>() : "factory_inspection_demo";
  run_id_ = config["run_id"] ?
    config["run_id"].as<std::string>() : scenario_id_;
  mission_profile_ = config["mission_profile"] ?
    config["mission_profile"].as<std::string>() : "routine_autonomous_round";
  const YAML::Node ground_truth_file = config["ground_truth_file"];
  ground_truth_by_station_.clear();
  if (ground_truth_file && !ground_truth_file.as<std::string>().empty()) {
    load_ground_truth(ground_truth_file.as<std::string>());
  }

  const YAML::Node checkpoint_nodes = config["checkpoints"];
  if (!checkpoint_nodes || !checkpoint_nodes.IsSequence() || checkpoint_nodes.size() == 0U) {
    throw std::runtime_error(
            "InspectionAtWaypoint checkpoint config must contain a non-empty 'checkpoints' list.");
  }

  checkpoints_.clear();
  checkpoints_.reserve(checkpoint_nodes.size());

  for (const auto & checkpoint_node : checkpoint_nodes) {
    InspectionCheckpoint checkpoint;
    checkpoint.name = checkpoint_node["name"].as<std::string>();
    checkpoint.station_id = checkpoint_node["station_id"] ?
      checkpoint_node["station_id"].as<std::string>() : checkpoint.name;
    checkpoint.mission_profile = mission_profile_;
    checkpoint.asset_id = checkpoint_node["asset_id"] ?
      checkpoint_node["asset_id"].as<std::string>() : checkpoint.station_id;
    checkpoint.asset_display_name = checkpoint_node["asset_display_name"] ?
      checkpoint_node["asset_display_name"].as<std::string>() : checkpoint.name;
    checkpoint.asset_type = checkpoint_node["asset_type"] ?
      checkpoint_node["asset_type"].as<std::string>() : "generic_asset";
    checkpoint.zone = checkpoint_node["zone"] ?
      checkpoint_node["zone"].as<std::string>() : "unknown";
    checkpoint.asset_priority = checkpoint_node["asset_priority"] ?
      checkpoint_node["asset_priority"].as<std::uint32_t>() : 1U;
    checkpoint.enabled_modalities = parse_string_list(checkpoint_node["enabled_modalities"]);
    checkpoint.inspection_mode = checkpoint_node["inspection_mode"] ?
      normalize_inspection_mode(checkpoint_node["inspection_mode"].as<std::string>()) : "fixed";
    checkpoint.inspection_label = checkpoint_node["inspection_label"] ?
      checkpoint_node["inspection_label"].as<std::string>() : "asset_nominal";
    checkpoint.inspection_severity = checkpoint_node["inspection_severity"] ?
      normalize_severity(checkpoint_node["inspection_severity"].as<std::string>()) : "normal";
    checkpoint.recommended_action = checkpoint_node["recommended_action"] ?
      checkpoint_node["recommended_action"].as<std::string>() : "continue_patrol";
    checkpoint.pose_x = checkpoint_node["x"] ? checkpoint_node["x"].as<double>() : 0.0;
    checkpoint.pose_y = checkpoint_node["y"] ? checkpoint_node["y"].as<double>() : 0.0;
    checkpoint.pose_yaw = checkpoint_node["yaw"] ? checkpoint_node["yaw"].as<double>() : 0.0;
    checkpoints_.push_back(checkpoint);
  }
}

void InspectionAtWaypoint::load_ground_truth(const std::string & ground_truth_file)
{
  const YAML::Node ground_truth = YAML::LoadFile(ground_truth_file);
  const YAML::Node stations = ground_truth["stations"];
  if (!stations || !stations.IsMap()) {
    RCLCPP_WARN(
      logger_,
      "Ground truth file %s did not contain a 'stations' map. Continuing without truth comparison.",
      ground_truth_file.c_str());
    return;
  }

  for (const auto & station_node : stations) {
    const auto station_id = station_node.first.as<std::string>();
    const auto & station_config = station_node.second;

    GroundTruthStation station;
    station.asset_id = station_config["asset_id"] ? station_config["asset_id"].as<std::string>() : station_id;
    station.asset_display_name = station_config["asset_display_name"] ?
      station_config["asset_display_name"].as<std::string>() : station_id;
    station.asset_type = station_config["asset_type"] ?
      station_config["asset_type"].as<std::string>() : "generic_asset";
    station.zone = station_config["zone"] ? station_config["zone"].as<std::string>() : "unknown";
    station.asset_priority = station_config["asset_priority"] ?
      station_config["asset_priority"].as<std::uint32_t>() : 1U;
    station.enabled_modalities = parse_string_list(station_config["enabled_modalities"]);
    station.anomaly_sources = parse_string_list(station_config["anomaly_sources"]);
    station.label = station_config["label"] ? station_config["label"].as<std::string>() : "";
    station.severity = station_config["severity"] ?
      normalize_severity(station_config["severity"].as<std::string>()) : "";
    station.recommended_action = station_config["recommended_action"] ?
      station_config["recommended_action"].as<std::string>() : "";
    station.signal_color = station_config["signal_color"] ?
      station_config["signal_color"].as<std::string>() : "";
    station.description = station_config["description"] ?
      station_config["description"].as<std::string>() : "";
    station.thermal_delta_c = station_config["thermal_delta_c"] ?
      station_config["thermal_delta_c"].as<double>() : 0.0;
    station.acoustic_db = station_config["acoustic_db"] ?
      station_config["acoustic_db"].as<double>() : 0.0;
    station.gas_ppm = station_config["gas_ppm"] ?
      station_config["gas_ppm"].as<double>() : 0.0;
    station.thermal_threshold_c = station_config["thermal_threshold_c"] ?
      station_config["thermal_threshold_c"].as<double>() : 18.0;
    station.acoustic_threshold_db = station_config["acoustic_threshold_db"] ?
      station_config["acoustic_threshold_db"].as<double>() : 72.0;
    station.gas_threshold_ppm = station_config["gas_threshold_ppm"] ?
      station_config["gas_threshold_ppm"].as<double>() : 45.0;
    const YAML::Node pose_node = station_config["pose"];
    station.pose_x = pose_node && pose_node["x"] ? pose_node["x"].as<double>() : 0.0;
    station.pose_y = pose_node && pose_node["y"] ? pose_node["y"].as<double>() : 0.0;
    station.pose_yaw = pose_node && pose_node["yaw"] ? pose_node["yaw"].as<double>() : 0.0;
    ground_truth_by_station_[station_id] = station;
  }
}

void InspectionAtWaypoint::initialize_csv()
{
  const std::string expected_header =
    "stamp_ns,round_number,waypoint_index,mission_profile,asset_id,asset_display_name,"
    "asset_type,zone,asset_priority,enabled_modalities,anomaly_sources,checkpoint_name,"
    "inspection_label,inspection_severity,recommended_action,inspection_confidence,"
    "review_required,review_reason,asset_status,health_score,"
    "thermal_delta_c,acoustic_db,gas_ppm,thermal_alert,acoustic_alert,gas_alert,is_anomaly,"
    "capture_ok,image_path,raw_image_path,annotated_image_path,"
    "ground_truth_label,ground_truth_severity,matches_ground_truth,"
    "pose_x,pose_y,pose_yaw,note";

  if (std::filesystem::exists(csv_path_)) {
    std::ifstream existing_csv(csv_path_);
    std::string header_line;
    std::getline(existing_csv, header_line);

    if (header_line == expected_header) {
      return;
    }

    const auto legacy_path =
      csv_path_.parent_path() /
      (csv_path_.stem().string() + "_legacy_" +
      std::to_string(parent_node_->get_clock()->now().nanoseconds()) + csv_path_.extension().string());

    std::filesystem::rename(csv_path_, legacy_path);
    RCLCPP_WARN(
      logger_,
      "Inspection CSV schema changed. Rotated legacy log to %s and created a fresh CSV.",
      legacy_path.string().c_str());
  }

  std::ofstream csv_file(csv_path_, std::ios::out);
  if (!csv_file.is_open()) {
    throw std::runtime_error("Unable to create inspection CSV at " + csv_path_.string());
  }

  csv_file << expected_header << "\n";
}

void InspectionAtWaypoint::publish_inspection_result(
  const rclcpp::Time & stamp,
  const std::size_t waypoint_index,
  const InspectionSnapshot & inspection,
  const bool capture_ok,
  const std::string & image_path,
  const std::string & raw_image_path,
  const std::string & annotated_image_path,
  const std::string & ground_truth_label,
  const std::string & ground_truth_severity,
  const bool matches_ground_truth,
  const std::string & note,
  const geometry_msgs::msg::PoseStamped & curr_pose)
{
  if (!inspection_result_publisher_) {
    return;
  }

  factory_inspection_interfaces::msg::InspectionResult message;
  message.stamp = stamp;
  message.round_number = current_round_number_;
  message.waypoint_index = static_cast<std::uint32_t>(waypoint_index);
  message.mission_profile = inspection.checkpoint.mission_profile;
  message.scenario_id = scenario_id_;
  message.run_id = run_id_;
  message.asset_id = inspection.checkpoint.asset_id;
  message.asset_display_name = inspection.checkpoint.asset_display_name;
  message.asset_type = inspection.checkpoint.asset_type;
  message.zone = inspection.checkpoint.zone;
  message.asset_priority = inspection.checkpoint.asset_priority;
  message.enabled_modalities = inspection.checkpoint.enabled_modalities;
  message.anomaly_sources = inspection.anomaly_sources;
  message.checkpoint_name = inspection.checkpoint.name;
  message.inspection_label = inspection.checkpoint.inspection_label;
  message.inspection_severity = inspection.checkpoint.inspection_severity;
  message.recommended_action = inspection.checkpoint.recommended_action;
  message.inspection_confidence = inspection.inspection_confidence;
  message.review_required = inspection.review_required;
  message.review_reason = inspection.review_reason;
  message.is_anomaly = is_anomaly_severity(inspection.checkpoint.inspection_severity);
  message.capture_ok = capture_ok;
  message.image_path = image_path;
  message.raw_image_path = raw_image_path;
  message.annotated_image_path = annotated_image_path;
  message.ground_truth_label = ground_truth_label;
  message.ground_truth_severity = ground_truth_severity;
  message.matches_ground_truth = matches_ground_truth;
  message.asset_status = inspection.asset_status;
  message.health_score = inspection.health_score;
  message.thermal_delta_c = inspection.thermal_delta_c;
  message.acoustic_db = inspection.acoustic_db;
  message.gas_ppm = inspection.gas_ppm;
  message.thermal_alert = inspection.thermal_alert;
  message.acoustic_alert = inspection.acoustic_alert;
  message.gas_alert = inspection.gas_alert;
  message.pose_x = curr_pose.pose.position.x;
  message.pose_y = curr_pose.pose.position.y;
  message.pose_yaw = quaternion_to_yaw(curr_pose.pose.orientation);
  message.note = note;
  inspection_result_publisher_->publish(message);
}

void InspectionAtWaypoint::publish_reset_markers()
{
  if (!marker_publisher_) {
    return;
  }

  std::lock_guard<std::mutex> lock(marker_mutex_);
  result_markers_.markers.clear();

  visualization_msgs::msg::MarkerArray reset_message;
  visualization_msgs::msg::Marker reset_marker;
  reset_marker.header.frame_id = "map";
  reset_marker.header.stamp = parent_node_->get_clock()->now();
  reset_marker.action = visualization_msgs::msg::Marker::DELETEALL;
  reset_message.markers.push_back(reset_marker);
  marker_publisher_->publish(reset_message);
}

void InspectionAtWaypoint::publish_result_marker(
  const rclcpp::Time & stamp,
  const std::size_t waypoint_index,
  const InspectionSnapshot & inspection,
  const bool capture_ok,
  const std::string & note,
  const geometry_msgs::msg::PoseStamped & curr_pose)
{
  if (!marker_publisher_) {
    return;
  }

  const auto frame_id = curr_pose.header.frame_id.empty() ? "map" : curr_pose.header.frame_id;
  const auto base_id = static_cast<int32_t>(waypoint_index * 10U);
  const auto severity = normalize_severity(inspection.checkpoint.inspection_severity);
  const bool show_marker = !capture_ok || severity != "normal" || inspection.review_required;

  std::lock_guard<std::mutex> lock(marker_mutex_);
  auto & markers = result_markers_.markers;
  markers.erase(
    std::remove_if(
      markers.begin(),
      markers.end(),
      [base_id](const visualization_msgs::msg::Marker & marker) {
        return marker.id == base_id || marker.id == base_id + 1;
      }),
    markers.end());

  if (!show_marker) {
    marker_publisher_->publish(result_markers_);
    return;
  }

  visualization_msgs::msg::Marker state_marker;
  state_marker.header.frame_id = frame_id;
  state_marker.header.stamp = stamp;
  state_marker.ns = "inspection_states";
  state_marker.id = base_id;
  state_marker.action = visualization_msgs::msg::Marker::ADD;
  state_marker.pose = curr_pose.pose;
  state_marker.pose.position.z = 0.30;
  state_marker.scale.x = 0.45;
  state_marker.scale.y = 0.45;
  state_marker.scale.z = 0.45;
  state_marker.color.a = 0.90F;

  visualization_msgs::msg::Marker text_marker;
  text_marker.header.frame_id = frame_id;
  text_marker.header.stamp = stamp;
  text_marker.ns = "inspection_labels";
  text_marker.id = base_id + 1;
  text_marker.type = visualization_msgs::msg::Marker::TEXT_VIEW_FACING;
  text_marker.action = visualization_msgs::msg::Marker::ADD;
  text_marker.pose = curr_pose.pose;
  text_marker.pose.position.z = 0.85;
  text_marker.scale.z = 0.26;
  text_marker.color.a = 1.0F;

  if (!capture_ok) {
    state_marker.type = visualization_msgs::msg::Marker::CYLINDER;
    state_marker.color.r = 0.98F;
    state_marker.color.g = 0.52F;
    state_marker.color.b = 0.12F;
    text_marker.color.r = 0.98F;
    text_marker.color.g = 0.84F;
    text_marker.color.b = 0.36F;
    text_marker.text = "CAPTURE ERR: " + inspection.checkpoint.asset_id;
  } else if (severity == "critical") {
    state_marker.type = visualization_msgs::msg::Marker::SPHERE;
    state_marker.color.r = 0.95F;
    state_marker.color.g = 0.15F;
    state_marker.color.b = 0.10F;
    text_marker.color.r = 1.0F;
    text_marker.color.g = 0.95F;
    text_marker.color.b = 0.20F;
    text_marker.text = "CRITICAL: " + inspection.checkpoint.asset_id;
  } else if (inspection.review_required) {
    state_marker.type = visualization_msgs::msg::Marker::CYLINDER;
    state_marker.color.r = 0.10F;
    state_marker.color.g = 0.52F;
    state_marker.color.b = 0.80F;
    text_marker.color.r = 0.78F;
    text_marker.color.g = 0.92F;
    text_marker.color.b = 1.00F;
    text_marker.text = "REVIEW: " + inspection.checkpoint.asset_id;
  } else {
    state_marker.type = visualization_msgs::msg::Marker::CUBE;
    state_marker.color.r = 0.96F;
    state_marker.color.g = 0.72F;
    state_marker.color.b = 0.16F;
    text_marker.color.r = 0.95F;
    text_marker.color.g = 0.88F;
    text_marker.color.b = 0.35F;
    text_marker.text = "WARNING: " + inspection.checkpoint.asset_id;
  }

  if (capture_ok) {
    text_marker.text += " " + inspection.checkpoint.inspection_label;
    text_marker.text += " H=" + std::to_string(static_cast<int>(std::round(inspection.health_score)));
    text_marker.text += " C=" +
      std::to_string(static_cast<int>(std::round(inspection.inspection_confidence * 100.0F)));
    if (!inspection.anomaly_sources.empty()) {
      text_marker.text += " [" + join_strings(inspection.anomaly_sources, "+") + "]";
    }
    if (inspection.review_required) {
      text_marker.text += " {" + inspection.review_reason + "}";
    }
  }

  if (!capture_ok && !note.empty()) {
    text_marker.text += " (" + note + ")";
  }

  markers.push_back(state_marker);
  markers.push_back(text_marker);
  marker_publisher_->publish(result_markers_);
}

void InspectionAtWaypoint::append_csv_row(
  const rclcpp::Time & stamp,
  const std::size_t waypoint_index,
  const InspectionSnapshot & inspection,
  const bool capture_ok,
  const std::string & image_path,
  const std::string & raw_image_path,
  const std::string & annotated_image_path,
  const std::string & ground_truth_label,
  const std::string & ground_truth_severity,
  const bool matches_ground_truth,
  const std::string & note,
  const geometry_msgs::msg::PoseStamped & curr_pose)
{
  std::lock_guard<std::mutex> lock(csv_mutex_);

  std::ofstream csv_file(csv_path_, std::ios::app);
  if (!csv_file.is_open()) {
    RCLCPP_ERROR(logger_, "Unable to append inspection CSV at %s", csv_path_.string().c_str());
    return;
  }

  const bool is_anomaly = is_anomaly_severity(inspection.checkpoint.inspection_severity);
  const double pose_yaw = quaternion_to_yaw(curr_pose.pose.orientation);

  csv_file
    << stamp.nanoseconds() << ","
    << current_round_number_ << ","
    << waypoint_index << ","
    << csv_escape(inspection.checkpoint.mission_profile) << ","
    << csv_escape(inspection.checkpoint.asset_id) << ","
    << csv_escape(inspection.checkpoint.asset_display_name) << ","
    << csv_escape(inspection.checkpoint.asset_type) << ","
    << csv_escape(inspection.checkpoint.zone) << ","
    << inspection.checkpoint.asset_priority << ","
    << csv_escape(join_strings(inspection.checkpoint.enabled_modalities, "|")) << ","
    << csv_escape(join_strings(inspection.anomaly_sources, "|")) << ","
    << csv_escape(inspection.checkpoint.name) << ","
    << csv_escape(inspection.checkpoint.inspection_label) << ","
    << csv_escape(inspection.checkpoint.inspection_severity) << ","
    << csv_escape(inspection.checkpoint.recommended_action) << ","
    << inspection.inspection_confidence << ","
    << (inspection.review_required ? "true" : "false") << ","
    << csv_escape(inspection.review_reason) << ","
    << csv_escape(inspection.asset_status) << ","
    << inspection.health_score << ","
    << inspection.thermal_delta_c << ","
    << inspection.acoustic_db << ","
    << inspection.gas_ppm << ","
    << (inspection.thermal_alert ? "true" : "false") << ","
    << (inspection.acoustic_alert ? "true" : "false") << ","
    << (inspection.gas_alert ? "true" : "false") << ","
    << (is_anomaly ? "true" : "false") << ","
    << (capture_ok ? "true" : "false") << ","
    << csv_escape(image_path) << ","
    << csv_escape(raw_image_path) << ","
    << csv_escape(annotated_image_path) << ","
    << csv_escape(ground_truth_label) << ","
    << csv_escape(ground_truth_severity) << ","
    << (matches_ground_truth ? "true" : "false") << ","
    << curr_pose.pose.position.x << ","
    << curr_pose.pose.position.y << ","
    << pose_yaw << ","
    << csv_escape(note) << "\n";
}

std::string InspectionAtWaypoint::sanitize_label(const std::string & value)
{
  std::string sanitized;
  sanitized.reserve(value.size());

  for (const char character : value) {
    if (std::isalnum(static_cast<unsigned char>(character)) || character == '_') {
      sanitized.push_back(character);
    } else {
      sanitized.push_back('_');
    }
  }

  return sanitized;
}

double InspectionAtWaypoint::quaternion_to_yaw(const geometry_msgs::msg::Quaternion & quaternion)
{
  const double siny_cosp =
    2.0 * ((quaternion.w * quaternion.z) + (quaternion.x * quaternion.y));
  const double cosy_cosp =
    1.0 - 2.0 * ((quaternion.y * quaternion.y) + (quaternion.z * quaternion.z));
  return std::atan2(siny_cosp, cosy_cosp);
}

}  // namespace factory_inspection_mission

PLUGINLIB_EXPORT_CLASS(
  factory_inspection_mission::InspectionAtWaypoint,
  nav2_core::WaypointTaskExecutor)
