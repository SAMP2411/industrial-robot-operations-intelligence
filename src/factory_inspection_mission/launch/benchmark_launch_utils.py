from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import yaml


DEFAULT_SINGLE_ROBOT_SPEC = "scout_alpha:tb4"
DEFAULT_FLEET_SPECS = "scout_alpha:tb4,response_beta:spot_like,utility_gamma:anymal_like"
DEFAULT_FLEET_POSES = (
    {"x": 2.12, "y": -21.30, "yaw": 1.57},
    {"x": 8.50, "y": -8.00, "yaw": 3.14},
    {"x": -4.00, "y": 21.00, "yaw": 0.00},
    {"x": -7.00, "y": -8.00, "yaw": 0.00},
)


def topic_path(namespace: str, leaf: str) -> str:
    clean_leaf = leaf.strip("/")
    clean_namespace = namespace.strip("/")
    if clean_namespace:
        return f"/{clean_namespace}/{clean_leaf}"
    return f"/{clean_leaf}"


def namespace_path(namespace: str) -> str:
    clean_namespace = namespace.strip("/")
    if clean_namespace:
        return f"/{clean_namespace}"
    return ""


def load_robot_profiles(profiles_path: str) -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(Path(profiles_path).read_text()) or {}
    profiles = data.get("profiles", {})
    if not profiles:
        raise RuntimeError(f"No robot profiles found in {profiles_path}")
    return profiles


def parse_robot_specs(raw_specs: str, profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw_specs.strip():
        raise RuntimeError("Robot specification list cannot be empty.")

    instances: list[dict[str, Any]] = []
    for index, token in enumerate(raw_specs.split(",")):
        entry = token.strip()
        if not entry:
            continue

        parts = [piece.strip() for piece in entry.split(":") if piece.strip()]
        if len(parts) == 1:
            robot_name = f"robot_{index + 1}"
            profile_name = parts[0]
        elif len(parts) == 2:
            robot_name, profile_name = parts
        else:
            raise RuntimeError(
                f"Invalid robot specification '{entry}'. Use 'robot_name:profile_name'.")

        if profile_name not in profiles:
            known_profiles = ", ".join(sorted(profiles.keys()))
            raise RuntimeError(
                f"Unknown robot profile '{profile_name}'. Known profiles: {known_profiles}")

        pose = DEFAULT_FLEET_POSES[index % len(DEFAULT_FLEET_POSES)]
        profile = profiles[profile_name]
        instances.append({
            "index": index,
            "name": robot_name,
            "namespace": robot_name,
            "profile_name": profile_name,
            "profile": profile,
            "robot_name": f"{profile.get('robot_name_prefix', profile_name)}_{robot_name}",
            "spawn_pose": pose,
        })

    if not instances:
        raise RuntimeError("No valid robot specifications were parsed.")
    return instances


def build_robot_topics(namespace: str) -> dict[str, str]:
    image_base = topic_path(namespace, "rgbd_camera")
    return {
        "joint_states": topic_path(namespace, "joint_states"),
        "odom": topic_path(namespace, "odom"),
        "tf": topic_path(namespace, "tf"),
        "imu": topic_path(namespace, "imu"),
        "scan": topic_path(namespace, "scan"),
        "cmd_vel": topic_path(namespace, "cmd_vel"),
        "camera_base": image_base,
        "camera_image": f"{image_base}/image",
        "camera_depth": f"{image_base}/depth_image",
        "camera_info": f"{image_base}/camera_info",
    }


def build_sim_topics(namespace: str) -> dict[str, str]:
    clean_namespace = namespace.strip("/")
    if clean_namespace:
        image_base = "rgbd_camera"
        return {
            "joint_states": "joint_states",
            "odom": "odom",
            "tf": "tf",
            "imu": "imu",
            "scan": "scan",
            "cmd_vel": "cmd_vel",
            "camera_base": image_base,
            "camera_image": f"{image_base}/image",
            "camera_depth": f"{image_base}/depth_image",
            "camera_info": f"{image_base}/camera_info",
        }

    image_base = "/rgbd_camera"
    return {
        "joint_states": "joint_states",
        "odom": "/odom",
        "tf": "tf",
        "imu": "/imu",
        "scan": "/scan",
        "cmd_vel": "/cmd_vel",
        "camera_base": image_base,
        "camera_image": f"{image_base}/image",
        "camera_depth": f"{image_base}/depth_image",
        "camera_info": f"{image_base}/camera_info",
    }


def write_bridge_config(path: str, namespace: str) -> str:
    topics = build_robot_topics(namespace)
    entries = [
        {
            "ros_topic_name": topics["joint_states"],
            "gz_topic_name": topics["joint_states"],
            "ros_type_name": "sensor_msgs/msg/JointState",
            "gz_type_name": "gz.msgs.Model",
            "direction": "GZ_TO_ROS",
        },
        {
            "ros_topic_name": topics["odom"],
            "gz_topic_name": topics["odom"],
            "ros_type_name": "nav_msgs/msg/Odometry",
            "gz_type_name": "gz.msgs.Odometry",
            "direction": "GZ_TO_ROS",
        },
        {
            "ros_topic_name": topics["tf"],
            "gz_topic_name": topics["tf"],
            "ros_type_name": "tf2_msgs/msg/TFMessage",
            "gz_type_name": "gz.msgs.Pose_V",
            "direction": "GZ_TO_ROS",
        },
        {
            "ros_topic_name": topics["imu"],
            "gz_topic_name": topics["imu"],
            "ros_type_name": "sensor_msgs/msg/Imu",
            "gz_type_name": "gz.msgs.IMU",
            "direction": "GZ_TO_ROS",
        },
        {
            "ros_topic_name": topics["scan"],
            "gz_topic_name": topics["scan"],
            "ros_type_name": "sensor_msgs/msg/LaserScan",
            "gz_type_name": "gz.msgs.LaserScan",
            "direction": "GZ_TO_ROS",
        },
        {
            "ros_topic_name": topics["cmd_vel"],
            "gz_topic_name": topics["cmd_vel"],
            "ros_type_name": "geometry_msgs/msg/Twist",
            "gz_type_name": "gz.msgs.Twist",
            "direction": "ROS_TO_GZ",
        },
        {
            "ros_topic_name": topics["camera_info"],
            "gz_topic_name": topics["camera_info"],
            "ros_type_name": "sensor_msgs/msg/CameraInfo",
            "gz_type_name": "gz.msgs.CameraInfo",
            "direction": "GZ_TO_ROS",
        },
    ]
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(yaml.safe_dump(entries, sort_keys=False))
    return str(path_obj)


def _distance_squared(checkpoint: dict[str, Any], pose: dict[str, float]) -> float:
    dx = float(checkpoint["x"]) - float(pose["x"])
    dy = float(checkpoint["y"]) - float(pose["y"])
    return dx * dx + dy * dy


def _ensure_non_empty_assignments(
    checkpoints: list[dict[str, Any]],
    assignments: dict[str, list[dict[str, Any]]],
    instances: list[dict[str, Any]],
) -> None:
    if not checkpoints:
        return

    for instance in instances:
        if assignments[instance["name"]]:
            continue

        donor = max(assignments.items(), key=lambda item: len(item[1]))[0]
        if not assignments[donor]:
            continue

        candidate = min(
            assignments[donor],
            key=lambda checkpoint: _distance_squared(checkpoint, instance["spawn_pose"]))
        assignments[donor].remove(candidate)
        assignments[instance["name"]].append(candidate)


def partition_checkpoints(checkpoints: list[dict[str, Any]], instances: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    assignments = {instance["name"]: [] for instance in instances}
    for checkpoint in checkpoints:
        owner = min(
            instances,
            key=lambda instance: _distance_squared(checkpoint, instance["spawn_pose"]))
        assignments[owner["name"]].append(checkpoint)

    _ensure_non_empty_assignments(checkpoints, assignments, instances)

    for name, robot_checkpoints in assignments.items():
        robot_checkpoints.sort(key=lambda checkpoint: checkpoint.get("asset_priority", 0), reverse=True)
        robot_checkpoints.sort(key=lambda checkpoint: checkpoint.get("name", ""))
    return assignments


def write_robot_checkpoint_config(
    base_config_path: str,
    output_path: str,
    instance: dict[str, Any],
    checkpoints: list[dict[str, Any]],
    route_role: str,
) -> str:
    base_config = yaml.safe_load(Path(base_config_path).read_text())
    selected_asset_ids = [checkpoint["asset_id"] for checkpoint in checkpoints]
    config = {
        "map_frame": base_config.get("map_frame", "map"),
        "scenario_id": base_config.get("scenario_id", ""),
        "run_id": base_config.get("run_id", ""),
        "mission_profile": route_role,
        "seed": base_config.get("seed", 0),
        "ground_truth_file": base_config.get("ground_truth_file", ""),
        "selected_asset_ids": selected_asset_ids,
        "fleet_robot_id": instance["name"],
        "fleet_robot_profile": instance["profile_name"],
        "fleet_robot_display_name": instance["profile"].get("display_name", instance["profile_name"]),
        "checkpoints": checkpoints,
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(config, sort_keys=False))
    return str(output)


def prepare_single_robot_instance(
    scenario_config_path: str,
    output_dir: str,
    instance: dict[str, Any],
) -> dict[str, Any]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    runtime_dir = output_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    mission_config_path = runtime_dir / f"{instance['name']}_checkpoints.yaml"
    bridge_config_path = runtime_dir / f"{instance['name']}_bridge.yaml"

    write_robot_checkpoint_config(
        base_config_path=scenario_config_path,
        output_path=str(mission_config_path),
        instance=instance,
        checkpoints=(yaml.safe_load(Path(scenario_config_path).read_text()) or {}).get("checkpoints", []),
        route_role="single_robot_profile_validation",
    )
    write_bridge_config(str(bridge_config_path), instance["namespace"])

    prepared = dict(instance)
    prepared["mission_config_path"] = str(mission_config_path)
    prepared["bridge_config_path"] = str(bridge_config_path)
    prepared["report_dir"] = str(output_root)
    prepared["topics"] = build_robot_topics(instance["namespace"])
    prepared["sim_topics"] = build_sim_topics(instance["namespace"])
    return prepared


def prepare_fleet_instances(
    scenario_config_path: str,
    output_dir: str,
    instances: list[dict[str, Any]],
) -> dict[str, Any]:
    base_config = yaml.safe_load(Path(scenario_config_path).read_text()) or {}
    checkpoints = list(base_config.get("checkpoints", []))
    assignments = partition_checkpoints(checkpoints, instances)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    prepared_instances: list[dict[str, Any]] = []
    for instance in instances:
        mission_config_path = output_root / f"{instance['name']}_checkpoints.yaml"
        bridge_config_path = output_root / f"{instance['name']}_bridge.yaml"
        report_dir = output_root / instance["name"]
        report_dir.mkdir(parents=True, exist_ok=True)

        route_role = f"fleet_zone_partition::{instance['profile'].get('default_route_role', 'general_patrol')}"
        write_robot_checkpoint_config(
            base_config_path=scenario_config_path,
            output_path=str(mission_config_path),
            instance=instance,
            checkpoints=assignments[instance["name"]],
            route_role=route_role,
        )
        write_bridge_config(str(bridge_config_path), instance["namespace"])

        prepared = dict(instance)
        prepared["mission_config_path"] = str(mission_config_path)
        prepared["bridge_config_path"] = str(bridge_config_path)
        prepared["report_dir"] = str(report_dir)
        prepared["topics"] = build_robot_topics(instance["namespace"])
        prepared["sim_topics"] = build_sim_topics(instance["namespace"])
        prepared["assigned_assets"] = [checkpoint["asset_id"] for checkpoint in assignments[instance["name"]]]
        prepared_instances.append(prepared)

    manifest = {
        "scenario_id": base_config.get("scenario_id", ""),
        "run_id": base_config.get("run_id", ""),
        "fleet_robot_ids": [instance["name"] for instance in prepared_instances],
        "fleet_profiles": {
            instance["name"]: instance["profile_name"]
            for instance in prepared_instances
        },
        "assignments": {
            instance["name"]: instance["assigned_assets"]
            for instance in prepared_instances
        },
    }
    manifest_path = output_root / "fleet_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "manifest_path": str(manifest_path),
        "instances": prepared_instances,
    }
