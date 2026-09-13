#ifndef FACTORY_INSPECTION_MISSION__INSPECTION_AT_WAYPOINT_HPP_
#define FACTORY_INSPECTION_MISSION__INSPECTION_AT_WAYPOINT_HPP_

#include <cstdint>
#include <filesystem>
#include <limits>
#include <memory>
#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "factory_inspection_interfaces/msg/inspection_result.hpp"
#include "nav2_core/waypoint_task_executor.hpp"
#include "rclcpp/create_publisher.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "visualization_msgs/msg/marker_array.hpp"

namespace factory_inspection_mission
{

class InspectionAtWaypoint : public nav2_core::WaypointTaskExecutor
{
public:
  InspectionAtWaypoint() = default;
  ~InspectionAtWaypoint() override = default;

  void initialize(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    const std::string & plugin_name) override;

  bool processAtWaypoint(
    const geometry_msgs::msg::PoseStamped & curr_pose,
    const int & curr_waypoint_index) override;

private:
  struct InspectionCheckpoint
  {
    std::string name;
    std::string station_id;
    std::string mission_profile;
    std::string asset_id;
    std::string asset_display_name;
    std::string asset_type;
    std::string zone;
    std::uint32_t asset_priority{1U};
    std::vector<std::string> enabled_modalities;
    std::string inspection_mode;
    std::string inspection_label;
    std::string inspection_severity;
    std::string recommended_action;
    double pose_x{0.0};
    double pose_y{0.0};
    double pose_yaw{0.0};
  };

  struct GroundTruthStation
  {
    std::string asset_id;
    std::string asset_display_name;
    std::string asset_type;
    std::string zone;
    std::uint32_t asset_priority{1U};
    std::vector<std::string> enabled_modalities;
    std::vector<std::string> anomaly_sources;
    std::string label;
    std::string severity;
    std::string recommended_action;
    std::string signal_color;
    std::string description;
    double thermal_delta_c{0.0};
    double acoustic_db{0.0};
    double gas_ppm{0.0};
    double thermal_threshold_c{18.0};
    double acoustic_threshold_db{72.0};
    double gas_threshold_ppm{45.0};
    double pose_x{0.0};
    double pose_y{0.0};
    double pose_yaw{0.0};
  };

  struct InspectionSnapshot
  {
    InspectionCheckpoint checkpoint;
    std::vector<std::string> anomaly_sources;
    std::string asset_status;
    float health_score{100.0F};
    float thermal_delta_c{0.0F};
    float acoustic_db{0.0F};
    float gas_ppm{0.0F};
    float inspection_confidence{0.0F};
    bool thermal_alert{false};
    bool acoustic_alert{false};
    bool gas_alert{false};
    bool review_required{false};
    std::string review_reason;
  };

  void image_callback(const sensor_msgs::msg::Image::SharedPtr msg);
  void load_checkpoint_config(const std::string & config_file);
  void load_ground_truth(const std::string & ground_truth_file);
  void initialize_csv();
  std::size_t select_checkpoint_index(
    const geometry_msgs::msg::PoseStamped & curr_pose,
    std::size_t fallback_waypoint_index) const;
  void publish_inspection_result(
    const rclcpp::Time & stamp,
    const std::size_t waypoint_index,
    const InspectionSnapshot & inspection,
    bool capture_ok,
    const std::string & image_path,
    const std::string & raw_image_path,
    const std::string & annotated_image_path,
    const std::string & ground_truth_label,
    const std::string & ground_truth_severity,
    bool matches_ground_truth,
    const std::string & note,
    const geometry_msgs::msg::PoseStamped & curr_pose);
  void publish_reset_markers();
  void publish_result_marker(
    const rclcpp::Time & stamp,
    const std::size_t waypoint_index,
    const InspectionSnapshot & inspection,
    bool capture_ok,
    const std::string & note,
    const geometry_msgs::msg::PoseStamped & curr_pose);
  void append_csv_row(
    const rclcpp::Time & stamp,
    const std::size_t waypoint_index,
    const InspectionSnapshot & inspection,
    bool capture_ok,
    const std::string & image_path,
    const std::string & raw_image_path,
    const std::string & annotated_image_path,
    const std::string & ground_truth_label,
    const std::string & ground_truth_severity,
    bool matches_ground_truth,
    const std::string & note,
    const geometry_msgs::msg::PoseStamped & curr_pose);

  static std::string sanitize_label(const std::string & value);
  static double quaternion_to_yaw(const geometry_msgs::msg::Quaternion & quaternion);

  rclcpp_lifecycle::LifecycleNode::SharedPtr parent_node_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_subscription_;
  rclcpp::Publisher<factory_inspection_interfaces::msg::InspectionResult>::SharedPtr
    inspection_result_publisher_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_publisher_;
  rclcpp::Logger logger_{rclcpp::get_logger("factory_inspection_mission.inspection_at_waypoint")};

  std::mutex image_mutex_;
  sensor_msgs::msg::Image::SharedPtr latest_image_msg_;

  std::mutex csv_mutex_;
  std::mutex marker_mutex_;
  std::vector<InspectionCheckpoint> checkpoints_;
  std::map<std::string, GroundTruthStation> ground_truth_by_station_;
  visualization_msgs::msg::MarkerArray result_markers_;
  std::filesystem::path save_dir_;
  std::filesystem::path csv_path_;
  std::string image_topic_;
  std::string image_format_;
  std::string marker_topic_;
  std::string mission_profile_{"routine_autonomous_round"};
  std::string scenario_id_{"factory_inspection_demo"};
  std::string run_id_{"factory_inspection_demo"};
  std::uint32_t current_round_number_{0U};
  std::size_t last_processed_waypoint_index_{std::numeric_limits<std::size_t>::max()};
  bool enabled_{true};
  bool fail_on_capture_error_{false};
  double capture_settle_seconds_{0.35};
  double checkpoint_match_distance_tolerance_{1.75};
  double checkpoint_match_yaw_weight_{0.20};
};

}  // namespace factory_inspection_mission

#endif  // FACTORY_INSPECTION_MISSION__INSPECTION_AT_WAYPOINT_HPP_
