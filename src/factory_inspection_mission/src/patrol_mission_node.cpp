#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "factory_inspection_interfaces/msg/inspection_result.hpp"
#include "factory_inspection_interfaces/msg/patrol_round_summary.hpp"
#include "nav2_msgs/action/follow_waypoints.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "yaml-cpp/yaml.h"

using namespace std::chrono_literals;

namespace
{

geometry_msgs::msg::Quaternion yaw_to_quaternion(const double yaw)
{
  geometry_msgs::msg::Quaternion quaternion;
  quaternion.x = 0.0;
  quaternion.y = 0.0;
  quaternion.z = std::sin(yaw * 0.5);
  quaternion.w = std::cos(yaw * 0.5);
  return quaternion;
}

std::string action_result_code_to_string(const rclcpp_action::ResultCode code)
{
  switch (code) {
    case rclcpp_action::ResultCode::SUCCEEDED:
      return "SUCCEEDED";
    case rclcpp_action::ResultCode::ABORTED:
      return "ABORTED";
    case rclcpp_action::ResultCode::CANCELED:
      return "CANCELED";
    default:
      return "UNKNOWN";
  }
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

std::string uppercase_copy(std::string value)
{
  std::transform(
    value.begin(),
    value.end(),
    value.begin(),
    [](const unsigned char character) { return static_cast<char>(std::toupper(character)); });
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
  if (normalized == "off" || normalized == "none" || normalized == "disabled") {
    return -1;
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

std::vector<std::string> yaml_string_list(const YAML::Node & node)
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
  } else if (node.IsScalar()) {
    values.push_back(node.as<std::string>());
  }
  return values;
}

std::string utc_now_iso8601()
{
  const auto now = std::chrono::system_clock::now();
  const auto time_value = std::chrono::system_clock::to_time_t(now);
  const auto fractional = std::chrono::duration_cast<std::chrono::milliseconds>(
    now.time_since_epoch()) % 1000;
  std::tm utc_time{};
#ifdef _WIN32
  gmtime_s(&utc_time, &time_value);
#else
  gmtime_r(&time_value, &utc_time);
#endif
  std::ostringstream stream;
  stream << std::put_time(&utc_time, "%Y-%m-%dT%H:%M:%S")
         << '.' << std::setw(3) << std::setfill('0') << fractional.count() << "Z";
  return stream.str();
}

}  // namespace

class PatrolMissionNode : public rclcpp::Node
{
public:
  using FollowWaypoints = nav2_msgs::action::FollowWaypoints;
  using GoalHandleFollowWaypoints = rclcpp_action::ClientGoalHandle<FollowWaypoints>;
  using InspectionResult = factory_inspection_interfaces::msg::InspectionResult;

  PatrolMissionNode()
  : Node("patrol_mission_node"),
    round_number_(0),
    last_feedback_index_(std::numeric_limits<std::size_t>::max()),
    mission_enabled_(false),
    goal_in_flight_(false)
  {
    declare_parameter<std::string>("config_file", "");
    declare_parameter<double>("round_pause_seconds", 3.0);
    declare_parameter<double>("recovery_pause_seconds", 8.0);
    declare_parameter<double>("round_sync_delay_seconds", 0.35);
    declare_parameter<bool>("autostart", true);
    declare_parameter<bool>("stop_on_failure", true);
    declare_parameter<std::string>("hold_on_severity_at_or_above", "critical");
    declare_parameter<int>("max_capture_failures_per_round", 1);
    declare_parameter<int>("max_consecutive_failed_rounds", 2);
    declare_parameter<int>("max_follow_up_assets", 3);
    declare_parameter<bool>("enable_targeted_follow_up", true);
    declare_parameter<double>("follow_up_round_pause_seconds", 2.0);
    declare_parameter<int>("max_follow_up_rounds_per_campaign", 2);
    declare_parameter<int>("stable_follow_up_required_rounds", 1);
    declare_parameter<double>("stable_follow_up_health_delta_threshold", 2.0);
    declare_parameter<std::string>("operator_mission_queue_file", "");

    load_checkpoint_config();
    const auto operator_mission_queue_file =
      get_parameter("operator_mission_queue_file").as_string();
    if (!operator_mission_queue_file.empty()) {
      operator_mission_queue_path_ = operator_mission_queue_file;
    }

    action_client_ = rclcpp_action::create_client<FollowWaypoints>(this, "follow_waypoints");
    inspection_subscription_ = create_subscription<InspectionResult>(
      "inspection_results",
      rclcpp::QoS(50).reliable(),
      [this](const InspectionResult::SharedPtr message) {
        handle_inspection_result(*message);
      });
    round_summary_publisher_ =
      create_publisher<factory_inspection_interfaces::msg::PatrolRoundSummary>(
      "patrol_round_summaries",
      rclcpp::QoS(10).reliable());

    RCLCPP_INFO(
      get_logger(),
      "Loaded %zu checkpoints for scenario %s with mission profile %s. Mission node owns rounds; Nav2 owns movement.",
      checkpoints_.size(),
      scenario_id_.c_str(),
      mission_profile_.c_str());

    for (std::size_t index = 0; index < checkpoints_.size(); ++index) {
      const auto & checkpoint = checkpoints_.at(index);
      RCLCPP_INFO(
        get_logger(),
        "  [%zu] %s (%s, zone=%s, modalities=%s) -> (%.2f, %.2f, yaw %.2f rad)",
        index,
        checkpoint.name.c_str(),
        checkpoint.asset_id.c_str(),
        checkpoint.zone.c_str(),
        join_strings(checkpoint.enabled_modalities, "/").c_str(),
        checkpoint.pose.pose.position.x,
        checkpoint.pose.pose.position.y,
        checkpoint.yaw);
    }

    if (get_parameter("autostart").as_bool()) {
      startup_timer_ = create_wall_timer(
        500ms,
        [this]() {
          startup_timer_->cancel();
          startup_timer_.reset();
          start_mission();
        });
    }
  }

private:
  struct Checkpoint
  {
    std::string name;
    std::string asset_id;
    std::string asset_display_name;
    std::string asset_type;
    std::string zone;
    std::uint32_t asset_priority{1U};
    std::vector<std::string> enabled_modalities;
    double yaw;
    geometry_msgs::msg::PoseStamped pose;
  };

  struct RoundInspectionStats
  {
    std::uint32_t inspection_count{0U};
    std::uint32_t anomaly_count{0U};
    std::uint32_t warning_count{0U};
    std::uint32_t critical_count{0U};
    std::uint32_t review_required_count{0U};
    std::uint32_t degraded_asset_count{0U};
    std::uint32_t thermal_alert_count{0U};
    std::uint32_t acoustic_alert_count{0U};
    std::uint32_t gas_alert_count{0U};
    std::uint32_t capture_failures{0U};
    float health_score_sum{0.0F};
    float confidence_sum{0.0F};
    float lowest_health_score{100.0F};
    std::vector<InspectionResult> results;
  };

  struct PendingRoundResult
  {
    std::uint32_t round_number{0U};
    double duration_seconds{0.0};
    std::string action_result{"UNKNOWN"};
    std::int16_t nav2_error_code{-1};
    std::vector<std::string> missed_checkpoint_names;
    std::vector<std::string> selected_assets;
    std::string route_phase{"routine"};
    std::uint32_t follow_up_round_index{0U};
    bool nav_round_success{false};
  };

  struct OperatorMissionDispatch
  {
    std::string mission_id;
    std::string tenant_id;
    std::string site_id;
    std::string mission_source{"operator_requested"};
    std::string mission_type{"manual_inspection"};
    std::string priority{"normal"};
    std::vector<std::string> selected_assets;
    std::vector<std::string> follow_up_assets;
    std::string linked_finding_id;
    std::string requested_by;
    std::string reason;
  };

  struct FollowUpTrendAssessment
  {
    bool has_previous_baseline{false};
    bool any_improved{false};
    bool any_worsened{false};
    bool stable_persistent_watchlist{false};
    std::vector<std::string> persistent_assets;
  };

  bool asset_needs_follow_up(const InspectionResult & result) const
  {
    return
      result.is_anomaly || result.review_required || !result.capture_ok ||
      lowercase_copy(result.asset_status) != "healthy";
  }

  std::vector<std::string> selected_asset_ids_for_route(const std::vector<Checkpoint> & route) const
  {
    std::vector<std::string> assets;
    assets.reserve(route.size());
    for (const auto & checkpoint : route) {
      if (std::find(assets.begin(), assets.end(), checkpoint.asset_id) != assets.end()) {
        continue;
      }
      assets.push_back(checkpoint.asset_id);
    }
    return assets;
  }

  std::vector<Checkpoint> build_route_checkpoints(const std::vector<std::string> & asset_ids) const
  {
    if (asset_ids.empty()) {
      return checkpoints_;
    }

    std::vector<Checkpoint> route;
    route.reserve(asset_ids.size());
    for (const auto & checkpoint : checkpoints_) {
      if (std::find(asset_ids.begin(), asset_ids.end(), checkpoint.asset_id) == asset_ids.end()) {
        continue;
      }
      route.push_back(checkpoint);
    }
    return route;
  }

  std::vector<std::string> unresolved_asset_ids(
    const std::vector<std::string> & requested_asset_ids,
    const std::vector<std::string> & resolved_asset_ids) const
  {
    std::vector<std::string> missing_assets;
    for (const auto & asset_id : requested_asset_ids) {
      if (std::find(resolved_asset_ids.begin(), resolved_asset_ids.end(), asset_id) !=
        resolved_asset_ids.end())
      {
        continue;
      }
      missing_assets.push_back(asset_id);
    }
    return missing_assets;
  }

  bool write_operator_queue_document(const YAML::Node & document) const
  {
    if (operator_mission_queue_path_.empty()) {
      return false;
    }

    try {
      std::filesystem::create_directories(operator_mission_queue_path_.parent_path());
      YAML::Emitter emitter;
      emitter << document;
      if (!emitter.good()) {
        throw std::runtime_error("YAML emitter failed while writing operator mission queue.");
      }

      const auto temporary_path =
        operator_mission_queue_path_.string() + ".tmp";
      {
        std::ofstream output(temporary_path, std::ios::out | std::ios::trunc);
        if (!output.is_open()) {
          throw std::runtime_error("Unable to open temporary operator queue file for writing.");
        }
        output << emitter.c_str();
      }

      if (std::rename(temporary_path.c_str(), operator_mission_queue_path_.c_str()) != 0) {
        std::filesystem::remove(operator_mission_queue_path_);
        if (std::rename(temporary_path.c_str(), operator_mission_queue_path_.c_str()) != 0) {
          throw std::runtime_error("Atomic rename failed for operator mission queue file.");
        }
      }
      return true;
    } catch (const std::exception & error) {
      RCLCPP_ERROR(
        get_logger(),
        "Failed to write operator mission queue %s: %s",
        operator_mission_queue_path_.string().c_str(),
        error.what());
      return false;
    }
  }

  std::optional<OperatorMissionDispatch> claim_next_operator_mission()
  {
    if (operator_mission_queue_path_.empty() || !std::filesystem::exists(operator_mission_queue_path_)) {
      return std::nullopt;
    }

    YAML::Node document;
    try {
      document = YAML::LoadFile(operator_mission_queue_path_.string());
    } catch (const std::exception & error) {
      RCLCPP_ERROR(
        get_logger(),
        "Failed to load operator mission queue %s: %s",
        operator_mission_queue_path_.string().c_str(),
        error.what());
      return std::nullopt;
    }

    if (!document.IsMap()) {
      return std::nullopt;
    }

    auto missions = document["missions"];
    if (!missions || !missions.IsSequence()) {
      return std::nullopt;
    }

    bool mutated_queue = false;
    const auto now_iso = utc_now_iso8601();

    for (std::size_t mission_index = 0; mission_index < missions.size(); ++mission_index) {
      auto mission = missions[mission_index];
      if (!mission.IsMap()) {
        continue;
      }

      const auto status = uppercase_copy(
        mission["status"] ? mission["status"].as<std::string>() : "QUEUED");
      if (status != "QUEUED") {
        continue;
      }

      const auto requested_assets = yaml_string_list(mission["selected_assets"]);
      const auto route = build_route_checkpoints(requested_assets);
      const auto resolved_assets = selected_asset_ids_for_route(route);
      const auto missing_assets = unresolved_asset_ids(requested_assets, resolved_assets);

      if (requested_assets.empty() || route.empty() || !missing_assets.empty()) {
        std::ostringstream reason;
        if (requested_assets.empty()) {
          reason << "Operator mission rejected because no selected assets were provided.";
        } else if (route.empty()) {
          reason << "Operator mission rejected because none of the requested assets map to checkpoints.";
        } else {
          reason << "Operator mission rejected because checkpoint mappings are missing for assets "
                 << join_strings(missing_assets, ", ") << ".";
        }

        mission["status"] = "REJECTED";
        mission["updated_at"] = now_iso;
        mission["completed_at"] = now_iso;
        mission["decision_reason"] = reason.str();

        YAML::Node latest_result;
        latest_result["success"] = false;
        latest_result["decision_reason"] = reason.str();
        latest_result["selected_assets"] = mission["selected_assets"];
        mission["latest_result"] = latest_result;

        mutated_queue = true;
        RCLCPP_WARN(get_logger(), "%s", reason.str().c_str());
        continue;
      }

      OperatorMissionDispatch dispatch;
      dispatch.mission_id = mission["mission_id"].as<std::string>();
      dispatch.tenant_id = mission["tenant_id"] ? mission["tenant_id"].as<std::string>() : "";
      dispatch.site_id = mission["site_id"] ? mission["site_id"].as<std::string>() : "";
      dispatch.mission_source =
        mission["mission_source"] ? mission["mission_source"].as<std::string>() :
        "operator_requested";
      dispatch.mission_type =
        mission["mission_type"] ? mission["mission_type"].as<std::string>() :
        "manual_inspection";
      dispatch.priority = mission["priority"] ? mission["priority"].as<std::string>() : "normal";
      dispatch.selected_assets = requested_assets;
      dispatch.follow_up_assets = yaml_string_list(mission["follow_up_assets"]);
      dispatch.linked_finding_id =
        mission["linked_finding_id"] ? mission["linked_finding_id"].as<std::string>() : "";
      dispatch.requested_by =
        mission["requested_by"] ? mission["requested_by"].as<std::string>() : "";
      dispatch.reason = mission["reason"] ? mission["reason"].as<std::string>() : "";

      mission["status"] = "ACTIVE";
      mission["updated_at"] = now_iso;
      mission["activated_at"] = now_iso;
      mutated_queue = true;

      if (!write_operator_queue_document(document)) {
        return std::nullopt;
      }

      RCLCPP_INFO(
        get_logger(),
        "Claimed operator mission %s (%s) for assets %s.",
        dispatch.mission_id.c_str(),
        dispatch.mission_type.c_str(),
        join_strings(dispatch.selected_assets, ", ").c_str());
      return dispatch;
    }

    if (mutated_queue) {
      write_operator_queue_document(document);
    }
    return std::nullopt;
  }

  void update_operator_queue_entry(
    const OperatorMissionDispatch & mission_dispatch,
    const std::string & status,
    const factory_inspection_interfaces::msg::PatrolRoundSummary & summary_message) const
  {
    if (operator_mission_queue_path_.empty() || !std::filesystem::exists(operator_mission_queue_path_)) {
      return;
    }

    YAML::Node document;
    try {
      document = YAML::LoadFile(operator_mission_queue_path_.string());
    } catch (const std::exception & error) {
      RCLCPP_ERROR(
        get_logger(),
        "Failed to reload operator mission queue %s: %s",
        operator_mission_queue_path_.string().c_str(),
        error.what());
      return;
    }

    auto missions = document["missions"];
    if (!missions || !missions.IsSequence()) {
      return;
    }

    const auto now_iso = utc_now_iso8601();
    for (std::size_t mission_index = 0; mission_index < missions.size(); ++mission_index) {
      auto mission = missions[mission_index];
      if (!mission.IsMap()) {
        continue;
      }
      const auto queue_mission_id =
        mission["mission_id"] ? mission["mission_id"].as<std::string>() : "";
      const auto queue_tenant_id =
        mission["tenant_id"] ? mission["tenant_id"].as<std::string>() : "";
      if (
        queue_mission_id != mission_dispatch.mission_id ||
        queue_tenant_id != mission_dispatch.tenant_id)
      {
        continue;
      }

      mission["status"] = uppercase_copy(status);
      mission["updated_at"] = now_iso;
      mission["completed_at"] = now_iso;
      mission["run_id"] = summary_message.run_id;
      mission["scenario_id"] = summary_message.scenario_id;
      mission["round_number"] = summary_message.round_number;
      mission["mission_profile"] = summary_message.mission_profile;
      mission["mission_decision"] = summary_message.mission_decision;
      mission["decision_reason"] = summary_message.decision_reason;
      mission["selected_assets"] = YAML::Node(YAML::NodeType::Sequence);
      for (const auto & asset_id : summary_message.selected_assets) {
        mission["selected_assets"].push_back(asset_id);
      }
      mission["follow_up_assets"] = YAML::Node(YAML::NodeType::Sequence);
      for (const auto & asset_id : summary_message.follow_up_assets) {
        mission["follow_up_assets"].push_back(asset_id);
      }

      YAML::Node latest_result;
      latest_result["round_number"] = summary_message.round_number;
      latest_result["run_id"] = summary_message.run_id;
      latest_result["scenario_id"] = summary_message.scenario_id;
      latest_result["mission_profile"] = summary_message.mission_profile;
      latest_result["mission_type"] = summary_message.mission_type;
      latest_result["mission_source"] = summary_message.mission_source;
      latest_result["mission_decision"] = summary_message.mission_decision;
      latest_result["decision_reason"] = summary_message.decision_reason;
      latest_result["action_result"] = summary_message.action_result;
      latest_result["nav2_error_code"] = summary_message.nav2_error_code;
      latest_result["success"] = summary_message.success;
      latest_result["selected_assets"] = mission["selected_assets"];
      latest_result["follow_up_assets"] = mission["follow_up_assets"];
      mission["latest_result"] = latest_result;

      write_operator_queue_document(document);
      return;
    }
  }

  std::string current_route_phase() const
  {
    if (active_operator_mission_.has_value()) {
      return "operator_requested";
    }
    return follow_up_mode_ && !scheduled_follow_up_assets_.empty() ?
           std::string("targeted_follow_up") :
           std::string("routine");
  }

  std::vector<std::string> select_follow_up_assets(const RoundInspectionStats & stats) const
  {
    std::vector<InspectionResult> ranked = stats.results;
    std::sort(
      ranked.begin(),
      ranked.end(),
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

    const auto max_follow_up_assets = static_cast<std::size_t>(std::max<std::int64_t>(
      get_parameter("max_follow_up_assets").as_int(),
      1));
    std::vector<std::string> follow_up_assets;
    for (const auto & result : ranked) {
      const bool needs_follow_up =
        asset_needs_follow_up(result);
      if (!needs_follow_up) {
        continue;
      }
      if (std::find(follow_up_assets.begin(), follow_up_assets.end(), result.asset_id) !=
        follow_up_assets.end())
      {
        continue;
      }
      follow_up_assets.push_back(result.asset_id);
      if (follow_up_assets.size() >= max_follow_up_assets) {
        break;
      }
    }
    return follow_up_assets;
  }

  FollowUpTrendAssessment assess_follow_up_trend(
    const RoundInspectionStats & stats,
    const std::vector<std::string> & follow_up_assets) const
  {
    FollowUpTrendAssessment assessment;
    if (follow_up_assets.empty()) {
      return assessment;
    }

    std::map<std::string, InspectionResult> current_by_asset;
    for (const auto & result : stats.results) {
      current_by_asset[result.asset_id] = result;
    }

    const double health_delta_threshold =
      get_parameter("stable_follow_up_health_delta_threshold").as_double();

    bool all_persistent_assets_stable = true;
    bool saw_comparable_asset = false;
    for (const auto & asset_id : follow_up_assets) {
      const auto current_it = current_by_asset.find(asset_id);
      if (current_it == current_by_asset.end()) {
        all_persistent_assets_stable = false;
        continue;
      }

      const auto previous_it = finalized_result_by_asset_.find(asset_id);
      if (previous_it == finalized_result_by_asset_.end()) {
        all_persistent_assets_stable = false;
        continue;
      }

      assessment.has_previous_baseline = true;
      saw_comparable_asset = true;
      const auto & current = current_it->second;
      const auto & previous = previous_it->second;
      const int current_severity = severity_rank(current.inspection_severity);
      const int previous_severity = severity_rank(previous.inspection_severity);
      const double health_delta =
        static_cast<double>(current.health_score) - static_cast<double>(previous.health_score);

      if (current_severity < previous_severity || health_delta > health_delta_threshold) {
        assessment.any_improved = true;
        all_persistent_assets_stable = false;
      } else if (
        current_severity > previous_severity ||
        health_delta < (-health_delta_threshold))
      {
        assessment.any_worsened = true;
        all_persistent_assets_stable = false;
      } else {
        assessment.persistent_assets.push_back(asset_id);
      }
    }

    assessment.stable_persistent_watchlist =
      saw_comparable_asset &&
      !assessment.any_improved &&
      !assessment.any_worsened &&
      all_persistent_assets_stable &&
      assessment.persistent_assets.size() == follow_up_assets.size();
    return assessment;
  }

  void load_checkpoint_config()
  {
    const auto config_file = get_parameter("config_file").as_string();
    if (config_file.empty()) {
      throw std::runtime_error("Parameter 'config_file' must point to a checkpoint YAML file.");
    }

    YAML::Node config = YAML::LoadFile(config_file);
    const std::string map_frame =
      config["map_frame"] ? config["map_frame"].as<std::string>() : "map";
    scenario_id_ =
      config["scenario_id"] ? config["scenario_id"].as<std::string>() : "factory_inspection_demo";
    run_id_ =
      config["run_id"] ? config["run_id"].as<std::string>() : scenario_id_;
    mission_profile_ =
      config["mission_profile"] ?
      config["mission_profile"].as<std::string>() : "routine_autonomous_round";

    const YAML::Node checkpoint_nodes = config["checkpoints"];
    if (!checkpoint_nodes || !checkpoint_nodes.IsSequence() || checkpoint_nodes.size() == 0U) {
      throw std::runtime_error("Checkpoint config must contain a non-empty 'checkpoints' list.");
    }

    checkpoints_.clear();
    checkpoints_.reserve(checkpoint_nodes.size());

    auto parse_string_list = [](const YAML::Node & node) {
        return yaml_string_list(node);
      };

    for (const auto & checkpoint_node : checkpoint_nodes) {
      Checkpoint checkpoint;
      checkpoint.name = checkpoint_node["name"].as<std::string>();
      checkpoint.asset_id = checkpoint_node["asset_id"] ?
        checkpoint_node["asset_id"].as<std::string>() : checkpoint.name;
      checkpoint.asset_display_name = checkpoint_node["asset_display_name"] ?
        checkpoint_node["asset_display_name"].as<std::string>() : checkpoint.name;
      checkpoint.asset_type = checkpoint_node["asset_type"] ?
        checkpoint_node["asset_type"].as<std::string>() : "generic_asset";
      checkpoint.zone = checkpoint_node["zone"] ?
        checkpoint_node["zone"].as<std::string>() : "unknown";
      checkpoint.asset_priority = checkpoint_node["asset_priority"] ?
        checkpoint_node["asset_priority"].as<std::uint32_t>() : 1U;
      checkpoint.enabled_modalities = parse_string_list(checkpoint_node["enabled_modalities"]);
      checkpoint.yaw = checkpoint_node["yaw"].as<double>();
      checkpoint.pose.header.frame_id = map_frame;
      checkpoint.pose.pose.position.x = checkpoint_node["x"].as<double>();
      checkpoint.pose.pose.position.y = checkpoint_node["y"].as<double>();
      checkpoint.pose.pose.position.z = 0.0;
      checkpoint.pose.pose.orientation = yaw_to_quaternion(checkpoint.yaw);
      checkpoints_.push_back(checkpoint);
    }
  }

  void start_mission()
  {
    mission_enabled_ = true;
    request_next_round();
  }

  void request_next_round()
  {
    if (!mission_enabled_ || goal_in_flight_) {
      return;
    }

    if (!action_client_->wait_for_action_server(250ms)) {
      wait_for_nav2_timer();
      return;
    }

    send_round_goal();
  }

  void wait_for_nav2_timer()
  {
    if (nav2_wait_timer_) {
      return;
    }

    nav2_wait_timer_ = create_wall_timer(
      1s,
      [this]() {
        if (!action_client_->wait_for_action_server(100ms)) {
          RCLCPP_INFO_THROTTLE(
            get_logger(),
            *get_clock(),
            5000,
            "Waiting for Nav2 action server '/follow_waypoints'...");
          return;
        }

        nav2_wait_timer_->cancel();
        nav2_wait_timer_.reset();
        send_round_goal();
      });
  }

  void send_round_goal()
  {
    if (goal_in_flight_) {
      return;
    }

    if (!active_operator_mission_.has_value() && !follow_up_mode_) {
      active_operator_mission_ = claim_next_operator_mission();
    }

    active_route_phase_ = current_route_phase();
    const auto route_asset_selection =
      active_route_phase_ == "operator_requested" && active_operator_mission_.has_value() ?
      active_operator_mission_->selected_assets :
      active_route_phase_ == "targeted_follow_up" ? scheduled_follow_up_assets_ :
      std::vector<std::string>{};
    active_route_checkpoints_ = build_route_checkpoints(route_asset_selection);
    if (active_route_checkpoints_.empty()) {
      RCLCPP_WARN(
        get_logger(),
        "Follow-up route resolved to zero checkpoints. Falling back to the routine patrol route.");
      active_operator_mission_.reset();
      follow_up_mode_ = false;
      scheduled_follow_up_assets_.clear();
      current_follow_up_round_index_ = 0U;
      active_route_phase_ = "routine";
      active_route_checkpoints_ = checkpoints_;
    }
    active_route_selected_assets_ = selected_asset_ids_for_route(active_route_checkpoints_);
    active_follow_up_round_index_ =
      active_route_phase_ == "targeted_follow_up" ? current_follow_up_round_index_ : 0U;

    ++round_number_;
    goal_in_flight_ = true;
    last_feedback_index_ = std::numeric_limits<std::size_t>::max();
    round_start_time_ = now();

    FollowWaypoints::Goal goal;
    goal.number_of_loops = 0;
    goal.goal_index = 0;

    for (const auto & checkpoint : active_route_checkpoints_) {
      auto pose = checkpoint.pose;
      pose.header.stamp = now();
      goal.poses.push_back(pose);
    }

    if (active_route_phase_ == "operator_requested" && active_operator_mission_.has_value()) {
      RCLCPP_INFO(
        get_logger(),
        "Starting operator mission %s (%s) as round %zu with %zu checkpoints across assets %s.",
        active_operator_mission_->mission_id.c_str(),
        active_operator_mission_->mission_type.c_str(),
        round_number_,
        active_route_checkpoints_.size(),
        join_strings(active_route_selected_assets_, ", ").c_str());
    } else if (active_route_phase_ == "targeted_follow_up") {
      RCLCPP_INFO(
        get_logger(),
        "Starting targeted follow-up round %zu (follow-up pass %u) with %zu checkpoints across assets %s.",
        round_number_,
        active_follow_up_round_index_,
        active_route_checkpoints_.size(),
        join_strings(active_route_selected_assets_, ", ").c_str());
    } else {
      RCLCPP_INFO(
        get_logger(),
        "Starting patrol round %zu with %zu checkpoints across assets %s.",
        round_number_,
        active_route_checkpoints_.size(),
        join_strings(active_route_selected_assets_, ", ").c_str());
    }

    rclcpp_action::Client<FollowWaypoints>::SendGoalOptions options;
    options.goal_response_callback =
      [this](const GoalHandleFollowWaypoints::SharedPtr & goal_handle) {
        if (!goal_handle) {
          goal_in_flight_ = false;
          if (round_number_ > 0U) {
            --round_number_;
          }
          RCLCPP_WARN(
            get_logger(),
            "Nav2 rejected the patrol goal while waypoint follower was not ready. Retrying.");
          schedule_round_request(
            2.0,
            "Retrying patrol round request in 2.0 seconds while Nav2 finishes activating.");
          return;
        }

        if (active_route_phase_ == "targeted_follow_up") {
          RCLCPP_INFO(
            get_logger(),
            "Nav2 accepted targeted follow-up round %zu (follow-up pass %u).",
            round_number_,
            active_follow_up_round_index_);
        } else if (active_route_phase_ == "operator_requested" && active_operator_mission_.has_value()) {
          RCLCPP_INFO(
            get_logger(),
            "Nav2 accepted operator mission %s as round %zu.",
            active_operator_mission_->mission_id.c_str(),
            round_number_);
        } else {
          RCLCPP_INFO(get_logger(), "Nav2 accepted patrol round %zu.", round_number_);
        }
      };

    options.feedback_callback =
      [this](
        GoalHandleFollowWaypoints::SharedPtr,
        const std::shared_ptr<const FollowWaypoints::Feedback> feedback) {
        if (!feedback) {
          return;
        }

        const auto waypoint_index = static_cast<std::size_t>(feedback->current_waypoint);
        if (
          waypoint_index == last_feedback_index_ ||
          waypoint_index >= active_route_checkpoints_.size())
        {
          return;
        }

        last_feedback_index_ = waypoint_index;
        const auto & checkpoint = active_route_checkpoints_.at(waypoint_index);
        if (active_route_phase_ == "operator_requested" && active_operator_mission_.has_value()) {
          RCLCPP_INFO(
            get_logger(),
            "Operator mission %s heading to asset %s checkpoint %zu/%zu: %s",
            active_operator_mission_->mission_id.c_str(),
            checkpoint.asset_id.c_str(),
            waypoint_index + 1,
            active_route_checkpoints_.size(),
            checkpoint.name.c_str());
        } else if (active_route_phase_ == "targeted_follow_up") {
          RCLCPP_INFO(
            get_logger(),
            "Follow-up round %zu pass %u heading to asset %s checkpoint %zu/%zu: %s",
            round_number_,
            active_follow_up_round_index_,
            checkpoint.asset_id.c_str(),
            waypoint_index + 1,
            active_route_checkpoints_.size(),
            checkpoint.name.c_str());
        } else {
          RCLCPP_INFO(
            get_logger(),
            "Round %zu heading to checkpoint %zu/%zu: %s",
            round_number_,
            waypoint_index + 1,
            active_route_checkpoints_.size(),
            checkpoint.name.c_str());
        }
      };

    options.result_callback =
      [this](const GoalHandleFollowWaypoints::WrappedResult & result) {
        handle_round_result(result);
      };

    action_client_->async_send_goal(goal, options);
  }

  void handle_inspection_result(const InspectionResult & result)
  {
    auto & stats = round_inspection_stats_[result.round_number];
    stats.results.push_back(result);
    ++stats.inspection_count;

    if (result.is_anomaly) {
      ++stats.anomaly_count;
    }
    if (result.review_required) {
      ++stats.review_required_count;
    }
    if (lowercase_copy(result.asset_status) != "healthy") {
      ++stats.degraded_asset_count;
    }

    const auto severity = severity_rank(result.inspection_severity);
    if (severity >= 2) {
      ++stats.critical_count;
    } else if (severity == 1) {
      ++stats.warning_count;
    }

    if (!result.capture_ok) {
      ++stats.capture_failures;
    }

    if (result.thermal_alert) {
      ++stats.thermal_alert_count;
    }
    if (result.acoustic_alert) {
      ++stats.acoustic_alert_count;
    }
    if (result.gas_alert) {
      ++stats.gas_alert_count;
    }

    stats.health_score_sum += result.health_score;
    stats.confidence_sum += result.inspection_confidence;
    stats.lowest_health_score = std::min(stats.lowest_health_score, result.health_score);
  }

  void handle_round_result(const GoalHandleFollowWaypoints::WrappedResult & result)
  {
    goal_in_flight_ = false;

    PendingRoundResult pending_result;
    pending_result.round_number = static_cast<std::uint32_t>(round_number_);
    pending_result.duration_seconds = (now() - round_start_time_).seconds();
    pending_result.action_result = action_result_code_to_string(result.code);
    pending_result.selected_assets = active_route_selected_assets_;
    pending_result.route_phase = active_route_phase_;
    pending_result.follow_up_round_index = active_follow_up_round_index_;

    const auto result_message = result.result;
    if (result_message) {
      pending_result.nav2_error_code = static_cast<std::int16_t>(result_message->error_code);
      for (const auto & missed_waypoint : result_message->missed_waypoints) {
        const auto missed_index = static_cast<std::size_t>(missed_waypoint.index);
        pending_result.missed_checkpoint_names.push_back(
          missed_index < active_route_checkpoints_.size() ?
          active_route_checkpoints_.at(missed_index).name :
          "unknown");
      }
      pending_result.nav_round_success =
        result.code == rclcpp_action::ResultCode::SUCCEEDED &&
        result_message->error_code == FollowWaypoints::Result::NONE &&
        result_message->missed_waypoints.empty();
    } else {
      pending_result.nav2_error_code = -1;
      pending_result.missed_checkpoint_names.push_back("unknown");
    }

    pending_round_result_ = pending_result;

    if (round_finalization_timer_) {
      round_finalization_timer_->cancel();
      round_finalization_timer_.reset();
    }

    const auto sync_duration =
      std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::duration<double>(
        get_parameter("round_sync_delay_seconds").as_double()));

    round_finalization_timer_ = create_wall_timer(
      sync_duration,
      [this]() {
        round_finalization_timer_->cancel();
        round_finalization_timer_.reset();
        finalize_round_result();
      });
  }

  void finalize_round_result()
  {
    if (!pending_round_result_.has_value()) {
      return;
    }

    const auto pending_result = *pending_round_result_;
    pending_round_result_.reset();

    const auto stats_it = round_inspection_stats_.find(pending_result.round_number);
    const RoundInspectionStats stats =
      stats_it == round_inspection_stats_.end() ? RoundInspectionStats{} : stats_it->second;
    const bool operator_requested_round = active_operator_mission_.has_value();

    factory_inspection_interfaces::msg::PatrolRoundSummary summary_message;
    summary_message.stamp = now();
    summary_message.round_number = pending_result.round_number;
    summary_message.mission_profile =
      pending_result.route_phase == "targeted_follow_up" ?
      "targeted_follow_up" :
      operator_requested_round ? "operator_requested" :
      mission_profile_;
    summary_message.scenario_id = scenario_id_;
    summary_message.run_id = run_id_;
    summary_message.mission_id =
      operator_requested_round ? active_operator_mission_->mission_id : "";
    summary_message.mission_source =
      operator_requested_round ? active_operator_mission_->mission_source : "autonomous";
    summary_message.mission_type =
      operator_requested_round ? active_operator_mission_->mission_type :
      pending_result.route_phase == "targeted_follow_up" ? "targeted_follow_up" :
      "routine_round";
    summary_message.selected_assets = pending_result.selected_assets;
    summary_message.duration_seconds = pending_result.duration_seconds;
    summary_message.action_result = pending_result.action_result;
    summary_message.nav2_error_code = pending_result.nav2_error_code;
    summary_message.missed_checkpoint_names = pending_result.missed_checkpoint_names;
    summary_message.inspection_count = stats.inspection_count;
    summary_message.anomaly_count = stats.anomaly_count;
    summary_message.warning_count = stats.warning_count;
    summary_message.critical_count = stats.critical_count;
    summary_message.review_required_count = stats.review_required_count;
    summary_message.degraded_asset_count = stats.degraded_asset_count;
    summary_message.thermal_alert_count = stats.thermal_alert_count;
    summary_message.acoustic_alert_count = stats.acoustic_alert_count;
    summary_message.gas_alert_count = stats.gas_alert_count;
    summary_message.capture_failures = stats.capture_failures;
    summary_message.average_health_score = stats.inspection_count == 0U ? 100.0F :
      stats.health_score_sum / static_cast<float>(stats.inspection_count);
    summary_message.lowest_health_score = stats.inspection_count == 0U ? 100.0F :
      stats.lowest_health_score;
    summary_message.average_inspection_confidence = stats.inspection_count == 0U ? 0.0F :
      stats.confidence_sum / static_cast<float>(stats.inspection_count);
    summary_message.follow_up_assets = select_follow_up_assets(stats);
    summary_message.success = pending_result.nav_round_success;
    summary_message.mission_decision = "CONTINUE";
    summary_message.decision_reason = "round healthy";

    std::ostringstream summary;
    summary << "Round " << pending_result.round_number << " summary: duration="
            << pending_result.duration_seconds << "s, action_result="
            << pending_result.action_result
            << ", nav2_error_code=" << pending_result.nav2_error_code
            << ", phase=" << pending_result.route_phase
            << ", mission_id="
            << (summary_message.mission_id.empty() ? std::string("none") : summary_message.mission_id)
            << ", selected_assets=" <<
      (pending_result.selected_assets.empty() ? std::string("none") :
      join_strings(pending_result.selected_assets, "|"))
            << ", missed=[";
    for (std::size_t index = 0; index < pending_result.missed_checkpoint_names.size(); ++index) {
      summary << pending_result.missed_checkpoint_names.at(index);
      if (index + 1U < pending_result.missed_checkpoint_names.size()) {
        summary << ", ";
      }
    }
    summary << "]"
            << ", inspections=" << stats.inspection_count
            << ", anomalies=" << stats.anomaly_count
            << ", warnings=" << stats.warning_count
            << ", critical=" << stats.critical_count
            << ", review_required=" << stats.review_required_count
            << ", degraded_assets=" << stats.degraded_asset_count
            << ", thermal_alerts=" << stats.thermal_alert_count
            << ", acoustic_alerts=" << stats.acoustic_alert_count
            << ", gas_alerts=" << stats.gas_alert_count
            << ", capture_failures=" << stats.capture_failures;

    if (pending_result.nav_round_success) {
      consecutive_failed_rounds_ = 0U;
    } else {
      ++consecutive_failed_rounds_;
    }

    const int hold_threshold_rank =
      severity_rank(get_parameter("hold_on_severity_at_or_above").as_string());
    const int max_detected_severity = stats.critical_count > 0U ? 2 : (stats.warning_count > 0U ? 1 : 0);
    const auto capture_failure_limit =
      std::max<std::int64_t>(get_parameter("max_capture_failures_per_round").as_int(), 0);
    const auto failed_round_limit =
      std::max<std::int64_t>(get_parameter("max_consecutive_failed_rounds").as_int(), 1);
    const auto max_capture_failures =
      static_cast<std::uint32_t>(capture_failure_limit);
    const auto max_consecutive_failed_rounds =
      static_cast<std::uint32_t>(failed_round_limit);
    const auto max_follow_up_rounds_per_campaign = static_cast<std::uint32_t>(std::max<std::int64_t>(
      get_parameter("max_follow_up_rounds_per_campaign").as_int(),
      1));
    const auto stable_follow_up_required_rounds = static_cast<std::uint32_t>(std::max<std::int64_t>(
      get_parameter("stable_follow_up_required_rounds").as_int(),
      1));
    const bool follow_up_enabled = get_parameter("enable_targeted_follow_up").as_bool();
    const bool currently_follow_up = pending_result.route_phase == "targeted_follow_up";
    const auto trend_assessment = assess_follow_up_trend(stats, summary_message.follow_up_assets);

    bool hold_mission = false;
    bool recovery_retry = false;
    bool schedule_targeted_follow_up = false;
    std::vector<std::string> next_follow_up_assets;

    if (!pending_result.nav_round_success) {
      summary_message.decision_reason = "Nav2 round execution failed.";
      if (get_parameter("stop_on_failure").as_bool()) {
        hold_mission = true;
        summary_message.mission_decision = "HOLD";
        summary_message.decision_reason = "Nav2 round execution failed and stop_on_failure=true.";
      } else if (consecutive_failed_rounds_ >= max_consecutive_failed_rounds) {
        hold_mission = true;
        summary_message.mission_decision = "HOLD";
        summary_message.decision_reason =
          "Nav2 round execution failed repeatedly and exceeded the recovery threshold.";
      } else {
        recovery_retry = true;
        summary_message.mission_decision = "RECOVERY_RETRY";
        summary_message.decision_reason =
          "Nav2 round execution failed. Cooling down before retrying another patrol round.";
      }
    } else if (hold_threshold_rank >= 0 && max_detected_severity >= hold_threshold_rank &&
      max_detected_severity > 0)
    {
      hold_mission = true;
      summary_message.mission_decision = "HOLD";
      summary_message.decision_reason =
        hold_threshold_rank == 1 ?
        "A warning-or-higher inspection result triggered the safety hold policy." :
        "A critical inspection result triggered the safety hold policy.";
    } else if (stats.capture_failures > max_capture_failures) {
      hold_mission = true;
      summary_message.mission_decision = "HOLD";
      summary_message.decision_reason =
        "Inspection capture failures exceeded the configured per-round threshold.";
    } else if (stats.capture_failures > 0U) {
      recovery_retry = true;
      summary_message.mission_decision = "RECOVERY_RETRY";
      summary_message.decision_reason =
        "Inspection capture issues were detected. Cooling down before the next patrol round.";
    } else if (follow_up_enabled && !summary_message.follow_up_assets.empty()) {
      next_follow_up_assets = summary_message.follow_up_assets;
      if (
        currently_follow_up &&
        pending_result.follow_up_round_index >= stable_follow_up_required_rounds &&
        trend_assessment.stable_persistent_watchlist)
      {
        summary_message.mission_decision = "RESUME_WATCHLIST";
        summary_message.decision_reason =
          "Follow-up assets remained stable across repeated passes. Resuming routine patrol while keeping them on the watchlist.";
      } else if (!currently_follow_up) {
        schedule_targeted_follow_up = true;
        summary_message.mission_decision = "TARGETED_FOLLOW_UP";
        summary_message.decision_reason =
          "Routine patrol detected assets that require a targeted follow-up inspection pass.";
      } else if (pending_result.follow_up_round_index < max_follow_up_rounds_per_campaign) {
        schedule_targeted_follow_up = true;
        summary_message.mission_decision = "TARGETED_FOLLOW_UP";
        summary_message.decision_reason =
          "Follow-up assets still require attention after the latest targeted inspection pass.";
      } else {
        summary_message.mission_decision = "CONTINUE";
        summary_message.decision_reason =
          "Follow-up asset budget exhausted. Resuming routine patrol with unresolved assets logged for operators.";
      }
    } else if (currently_follow_up) {
      summary_message.mission_decision = "CONTINUE";
      summary_message.decision_reason =
        "Targeted follow-up round cleared the current watchlist. Resuming routine patrol.";
    }

    round_summary_publisher_->publish(summary_message);
    if (active_operator_mission_.has_value()) {
      update_operator_queue_entry(
        *active_operator_mission_,
        pending_result.nav_round_success ? "COMPLETED" : "FAILED",
        summary_message);
      active_operator_mission_.reset();
    }

    summary << ", decision=" << summary_message.mission_decision
            << ", avg_health=" << summary_message.average_health_score
            << ", avg_confidence=" << summary_message.average_inspection_confidence
            << ", lowest_health=" << summary_message.lowest_health_score
            << ", follow_up_assets=" <<
      (summary_message.follow_up_assets.empty() ? std::string("none") :
      join_strings(summary_message.follow_up_assets, "|"))
            << ", reason=" << summary_message.decision_reason;

    if (pending_result.nav_round_success) {
      summary << ", status=SUCCESS";
    } else {
      summary << ", status=FAILURE";
    }

    if (hold_mission) {
      follow_up_mode_ = false;
      scheduled_follow_up_assets_.clear();
      current_follow_up_round_index_ = 0U;
      mission_enabled_ = false;
      RCLCPP_ERROR(get_logger(), "%s", summary.str().c_str());
      RCLCPP_ERROR(
        get_logger(),
        "Mission placed in HOLD after round %u. Reason: %s",
        pending_result.round_number,
        summary_message.decision_reason.c_str());
    } else if (recovery_retry) {
      RCLCPP_WARN(get_logger(), "%s", summary.str().c_str());
      schedule_recovery_retry(summary_message.decision_reason);
    } else if (schedule_targeted_follow_up) {
      follow_up_mode_ = true;
      scheduled_follow_up_assets_ = next_follow_up_assets;
      current_follow_up_round_index_ =
        currently_follow_up ? pending_result.follow_up_round_index + 1U : 1U;
      RCLCPP_WARN(get_logger(), "%s", summary.str().c_str());
      schedule_follow_up_round();
    } else {
      follow_up_mode_ = false;
      scheduled_follow_up_assets_.clear();
      current_follow_up_round_index_ = 0U;
      RCLCPP_INFO(get_logger(), "%s", summary.str().c_str());
      schedule_next_round();
    }

    for (const auto & result : stats.results) {
      finalized_result_by_asset_[result.asset_id] = result;
    }
    round_inspection_stats_.erase(pending_result.round_number);
  }

  void schedule_round_request(const double delay_seconds, const std::string & message)
  {
    if (inter_round_timer_) {
      inter_round_timer_->cancel();
      inter_round_timer_.reset();
    }

    const auto pause_duration =
      std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::duration<double>(
        delay_seconds));

    RCLCPP_INFO(get_logger(), "%s", message.c_str());

    inter_round_timer_ = create_wall_timer(
      pause_duration,
      [this]() {
        inter_round_timer_->cancel();
        inter_round_timer_.reset();
        request_next_round();
      });
  }

  void schedule_next_round()
  {
    const double pause_seconds = get_parameter("round_pause_seconds").as_double();
    std::ostringstream message;
    message << "Pausing for " << pause_seconds
            << " seconds before patrol round " << round_number_ + 1U << ".";
    schedule_round_request(pause_seconds, message.str());
  }

  void schedule_follow_up_round()
  {
    const double pause_seconds = get_parameter("follow_up_round_pause_seconds").as_double();
    std::ostringstream message;
    message << "Pausing for " << pause_seconds
            << " seconds before targeted follow-up round " << round_number_ + 1U
            << " on assets "
            << (scheduled_follow_up_assets_.empty() ? std::string("none") :
            join_strings(scheduled_follow_up_assets_, ", "))
            << ".";
    schedule_round_request(pause_seconds, message.str());
  }

  void schedule_recovery_retry(const std::string & reason)
  {
    const double pause_seconds = get_parameter("recovery_pause_seconds").as_double();
    std::ostringstream message;
    message << "Recovery cooldown: " << reason
            << " Retrying patrol in " << pause_seconds << " seconds.";
    schedule_round_request(pause_seconds, message.str());
  }

  rclcpp_action::Client<FollowWaypoints>::SharedPtr action_client_;
  rclcpp::Subscription<InspectionResult>::SharedPtr inspection_subscription_;
  rclcpp::Publisher<factory_inspection_interfaces::msg::PatrolRoundSummary>::SharedPtr
    round_summary_publisher_;
  std::string mission_profile_{"routine_autonomous_round"};
  std::string scenario_id_{"factory_inspection_demo"};
  std::string run_id_{"factory_inspection_demo"};
  std::vector<Checkpoint> checkpoints_;
  std::map<std::uint32_t, RoundInspectionStats> round_inspection_stats_;
  std::map<std::string, InspectionResult> finalized_result_by_asset_;
  std::vector<Checkpoint> active_route_checkpoints_;
  std::vector<std::string> active_route_selected_assets_;
  std::vector<std::string> scheduled_follow_up_assets_;
  std::string active_route_phase_{"routine"};
  std::filesystem::path operator_mission_queue_path_;
  std::optional<OperatorMissionDispatch> active_operator_mission_;

  std::size_t round_number_;
  std::size_t last_feedback_index_;
  std::uint32_t consecutive_failed_rounds_{0U};
  std::uint32_t current_follow_up_round_index_{0U};
  std::uint32_t active_follow_up_round_index_{0U};
  bool mission_enabled_;
  bool goal_in_flight_;
  bool follow_up_mode_{false};
  rclcpp::Time round_start_time_;
  std::optional<PendingRoundResult> pending_round_result_;

  rclcpp::TimerBase::SharedPtr startup_timer_;
  rclcpp::TimerBase::SharedPtr nav2_wait_timer_;
  rclcpp::TimerBase::SharedPtr inter_round_timer_;
  rclcpp::TimerBase::SharedPtr round_finalization_timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  try {
    auto node = std::make_shared<PatrolMissionNode>();
    rclcpp::spin(node);
  } catch (const std::exception & error) {
    RCLCPP_FATAL(
      rclcpp::get_logger("patrol_mission_node"),
      "Failed to start patrol mission node: %s",
      error.what());
    rclcpp::shutdown();
    return 1;
  }

  rclcpp::shutdown();
  return 0;
}
