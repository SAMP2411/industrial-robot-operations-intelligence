#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Checkpoint:
    name: str
    x: float
    y: float
    yaw: float


@dataclass(frozen=True)
class AssetProfile:
    checkpoint: Checkpoint
    asset_id: str
    display_name: str
    asset_type: str
    zone: str
    priority: int
    enabled_modalities: tuple[str, ...]
    criticality: str = "HIGH"
    owner_team: str = "unassigned"
    inspection_profile_id: str = ""
    status: str = "ACTIVE"
    tags: tuple[str, ...] = ()
    viewpoint_id: str = ""
    position_tolerance_m: float = 1.75
    orientation_tolerance_rad: float = 0.35


@dataclass(frozen=True)
class SiteConfig:
    schema_version: str
    site_id: str
    name: str
    timezone: str
    map_id: str
    coordinate_frame: str
    status: str
    metadata: dict


@dataclass(frozen=True)
class IssueTemplate:
    label: str
    severity: str
    recommended_action: str
    visual_state: str
    anomaly_sources: tuple[str, ...]
    description: str
    thermal_range: tuple[float, float]
    acoustic_range: tuple[float, float]
    gas_range: tuple[float, float]


ASSET_PROFILES = [
    AssetProfile(
        Checkpoint("spawn_lane", 2.12, -21.30, 1.57),
        "CNV-510",
        "Packing Conveyor Drive",
        "conveyor_drive",
        "packing_lane",
        3,
        ("visual", "thermal", "acoustic"),
    ),
    AssetProfile(
        Checkpoint("east_aisle", 4.20, -21.30, 0.00),
        "PMP-101",
        "Feed Pump Skid",
        "pump",
        "mixing_line",
        5,
        ("visual", "thermal", "acoustic"),
    ),
    AssetProfile(
        Checkpoint("upper_right_turn", 4.20, -18.50, 1.57),
        "CMP-220",
        "Compressor Cell",
        "compressor",
        "utilities_bay",
        5,
        ("visual", "thermal", "acoustic", "gas"),
    ),
    AssetProfile(
        Checkpoint("upper_left_turn", 1.00, -18.50, 3.14),
        "PNL-315",
        "Power Distribution Panel",
        "electrical_panel",
        "power_room",
        4,
        ("visual", "thermal"),
    ),
    AssetProfile(
        Checkpoint("west_aisle", 1.00, -21.30, -1.57),
        "VLV-410",
        "Process Valve Cluster",
        "valve_manifold",
        "reactor_loop",
        4,
        ("visual", "gas"),
    ),
    AssetProfile(
        Checkpoint("mid_east_service_bay", 8.50, -8.00, 3.14),
        "DRV-610",
        "Palletizer Drive Pack",
        "conveyor_drive",
        "dispatch_bay",
        4,
        ("visual", "thermal", "acoustic"),
    ),
    AssetProfile(
        Checkpoint("upper_east_utility_lane", 10.00, 5.00, 3.14),
        "UTL-720",
        "Utilities Pump Bay",
        "pump",
        "utility_corridor",
        4,
        ("visual", "thermal", "acoustic"),
    ),
    AssetProfile(
        Checkpoint("north_center_crossing", -1.00, 15.00, 1.57),
        "QCS-810",
        "Quality Check Manifold",
        "valve_manifold",
        "quality_line",
        4,
        ("visual", "gas"),
    ),
    AssetProfile(
        Checkpoint("north_west_return", -4.00, 21.00, 0.00),
        "PWR-905",
        "North Power Cabinet",
        "electrical_panel",
        "north_return",
        4,
        ("visual", "thermal"),
    ),
    AssetProfile(
        Checkpoint("mid_west_aisle", -7.00, -8.00, 0.00),
        "VLV-455",
        "West Valve Cluster",
        "valve_manifold",
        "reactor_return",
        3,
        ("visual", "gas"),
    ),
]

STATE_LIBRARY = {
    "nominal": {
        "signal_color": "green",
        "description": "Nominal asset condition. Green status fascia active.",
        "color": (0.12, 0.82, 0.32),
        "accent": (0.06, 0.32, 0.12),
    },
    "warning": {
        "signal_color": "yellow",
        "description": "Warning condition. Amber alert fascia active.",
        "color": (0.96, 0.77, 0.16),
        "accent": (0.52, 0.31, 0.06),
    },
    "critical": {
        "signal_color": "red",
        "description": "Critical condition. Red alarm fascia active.",
        "color": (0.92, 0.18, 0.14),
        "accent": (0.44, 0.08, 0.08),
    },
}

THERMAL_ALERT_C = 18.0
ACOUSTIC_ALERT_DB = 72.0
GAS_ALERT_PPM = 45.0

NOMINAL_ISSUE = IssueTemplate(
    label="asset_nominal",
    severity="normal",
    recommended_action="continue_patrol",
    visual_state="nominal",
    anomaly_sources=(),
    description="Asset healthy across the simulated inspection channels.",
    thermal_range=(4.0, 10.0),
    acoustic_range=(42.0, 56.0),
    gas_range=(0.0, 4.0),
)

ISSUE_LIBRARY = {
    "pump": {
        "warning": [
            IssueTemplate(
                label="bearing_warmup",
                severity="warning",
                recommended_action="schedule_recheck",
                visual_state="warning",
                anomaly_sources=("visual", "thermal", "acoustic"),
                description="Pump bearing temperature trending upward with mild vibration growth.",
                thermal_range=(18.5, 24.0),
                acoustic_range=(68.0, 75.0),
                gas_range=(0.0, 3.0),
            ),
        ],
        "critical": [
            IssueTemplate(
                label="bearing_overheat",
                severity="critical",
                recommended_action="dispatch_operator_immediately",
                visual_state="critical",
                anomaly_sources=("visual", "thermal", "acoustic"),
                description="Pump bearing overheating with strong mechanical distress.",
                thermal_range=(28.0, 37.0),
                acoustic_range=(78.0, 89.0),
                gas_range=(0.0, 4.0),
            ),
        ],
    },
    "compressor": {
        "warning": [
            IssueTemplate(
                label="belt_slip",
                severity="warning",
                recommended_action="schedule_recheck",
                visual_state="warning",
                anomaly_sources=("visual", "acoustic"),
                description="Compressor drive shows abnormal belt noise and amber beacon.",
                thermal_range=(9.0, 16.0),
                acoustic_range=(74.0, 82.0),
                gas_range=(0.0, 8.0),
            ),
        ],
        "critical": [
            IssueTemplate(
                label="gas_leak_detected",
                severity="critical",
                recommended_action="dispatch_operator_immediately",
                visual_state="critical",
                anomaly_sources=("visual", "gas"),
                description="Gas plume warning with red alarm beacon at the compressor cell.",
                thermal_range=(8.0, 18.0),
                acoustic_range=(55.0, 66.0),
                gas_range=(58.0, 92.0),
            ),
        ],
    },
    "electrical_panel": {
        "warning": [
            IssueTemplate(
                label="cabinet_hotspot",
                severity="warning",
                recommended_action="schedule_recheck",
                visual_state="warning",
                anomaly_sources=("visual", "thermal"),
                description="Electrical cabinet hotspot detected without trip-level severity.",
                thermal_range=(20.0, 27.0),
                acoustic_range=(42.0, 54.0),
                gas_range=(0.0, 2.0),
            ),
        ],
        "critical": [
            IssueTemplate(
                label="panel_arc_risk",
                severity="critical",
                recommended_action="dispatch_operator_immediately",
                visual_state="critical",
                anomaly_sources=("visual", "thermal"),
                description="Panel hotspot has reached arc-risk territory and requires immediate review.",
                thermal_range=(30.0, 42.0),
                acoustic_range=(43.0, 58.0),
                gas_range=(0.0, 3.0),
            ),
        ],
    },
    "valve_manifold": {
        "warning": [
            IssueTemplate(
                label="actuator_hunt",
                severity="warning",
                recommended_action="schedule_recheck",
                visual_state="warning",
                anomaly_sources=("visual",),
                description="Valve actuator is oscillating and flagged by the local warning stack.",
                thermal_range=(5.0, 10.0),
                acoustic_range=(48.0, 60.0),
                gas_range=(4.0, 14.0),
            ),
        ],
        "critical": [
            IssueTemplate(
                label="seal_leak",
                severity="critical",
                recommended_action="dispatch_operator_immediately",
                visual_state="critical",
                anomaly_sources=("visual", "gas"),
                description="Valve manifold leak signature detected with elevated gas concentration.",
                thermal_range=(4.0, 10.0),
                acoustic_range=(50.0, 63.0),
                gas_range=(52.0, 86.0),
            ),
        ],
    },
    "conveyor_drive": {
        "warning": [
            IssueTemplate(
                label="roller_imbalance",
                severity="warning",
                recommended_action="schedule_recheck",
                visual_state="warning",
                anomaly_sources=("visual", "acoustic"),
                description="Conveyor drive rollers show imbalance and audible chatter.",
                thermal_range=(8.0, 15.0),
                acoustic_range=(71.0, 79.0),
                gas_range=(0.0, 2.0),
            ),
        ],
        "critical": [
            IssueTemplate(
                label="motor_overtemp",
                severity="critical",
                recommended_action="dispatch_operator_immediately",
                visual_state="critical",
                anomaly_sources=("visual", "thermal", "acoustic"),
                description="Conveyor motor temperature has crossed the critical shutdown threshold.",
                thermal_range=(28.0, 38.0),
                acoustic_range=(74.0, 84.0),
                gas_range=(0.0, 2.0),
            ),
        ],
    },
}

CLUTTER_POINTS = [
    (-12.4, -22.8), (-10.8, -22.0), (-8.9, -21.8), (7.8, -22.5), (9.8, -21.8),
    (12.2, -22.2), (-13.6, 18.0), (-11.7, 18.5), (-9.5, 19.1), (8.6, 8.1),
    (10.5, 8.4), (12.4, 8.7), (-5.0, 11.0), (-2.0, 11.8), (1.0, 10.7), (5.2, 10.8),
]


def default_config_path(*parts: str) -> Path:
    return Path(__file__).resolve().parent.parent / "config" / Path(*parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a randomized multimodal benchmark scenario.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--template-world", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--min-anomalies", type=int, default=1)
    parser.add_argument("--max-anomalies", type=int, default=3)
    parser.add_argument("--clutter-count", type=int, default=10)
    parser.add_argument("--target-assets", default="")
    parser.add_argument("--allow-critical", default="true")
    parser.add_argument(
        "--asset-registry",
        default=str(default_config_path("assets", "benchmark_asset_registry.yaml")),
    )
    parser.add_argument(
        "--site-config",
        default=str(default_config_path("sites", "benchmark_site.yaml")),
    )
    parser.add_argument(
        "--inspection-profiles",
        default=str(default_config_path("inspection_profiles", "benchmark_inspection_profiles.yaml")),
    )
    return parser.parse_args()


def parse_target_assets(raw_value: str) -> set[str]:
    if not raw_value.strip():
        return set()
    return {
        token.strip().lower()
        for token in raw_value.split(",")
        if token.strip()
    }


def parse_bool(raw_value: str) -> bool:
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SystemExit(f"Invalid boolean value: {raw_value}")


def load_yaml_mapping(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise SystemExit(f"Expected a top-level mapping in {path}")
    return loaded


def default_site_config() -> SiteConfig:
    return SiteConfig(
        schema_version="site.v1",
        site_id="factory_demo_site",
        name="Factory Demo Warehouse",
        timezone="UTC",
        map_id="nav2_warehouse",
        coordinate_frame="map",
        status="ACTIVE",
        metadata={"environment": "simulation", "world_template": "warehouse_template.sdf"},
    )


def load_site_config(path: Path) -> SiteConfig:
    if not path.exists():
        return default_site_config()

    data = load_yaml_mapping(path)
    return SiteConfig(
        schema_version=str(data.get("schema_version", "site.v1")),
        site_id=str(data.get("site_id", "factory_demo_site")),
        name=str(data.get("name", "Factory Demo Warehouse")),
        timezone=str(data.get("timezone", "UTC")),
        map_id=str(data.get("map_id", "nav2_warehouse")),
        coordinate_frame=str(data.get("coordinate_frame", "map")),
        status=str(data.get("status", "ACTIVE")),
        metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
    )


def load_inspection_profiles(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    data = load_yaml_mapping(path)
    profiles = data.get("profiles", [])
    if not isinstance(profiles, list):
        raise SystemExit(f"Expected 'profiles' list in {path}")

    profile_map: dict[str, dict] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            raise SystemExit(f"Inspection profile entries must be mappings in {path}")
        profile_id = str(profile.get("inspection_profile_id", "")).strip()
        if not profile_id:
            raise SystemExit(f"Inspection profile missing inspection_profile_id in {path}")
        profile_map[profile_id] = profile
    return profile_map


def load_asset_profiles(path: Path, inspection_profiles: dict[str, dict]) -> list[AssetProfile]:
    if not path.exists():
        return list(ASSET_PROFILES)

    data = load_yaml_mapping(path)
    assets = data.get("assets", [])
    if not isinstance(assets, list) or not assets:
        raise SystemExit(f"Expected a non-empty 'assets' list in {path}")

    loaded_profiles: list[AssetProfile] = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise SystemExit(f"Asset entries must be mappings in {path}")
        checkpoint = asset.get("checkpoint", {})
        if not isinstance(checkpoint, dict):
            raise SystemExit(f"Asset {asset.get('asset_id', '<unknown>')} has invalid checkpoint data")

        checkpoint_name = str(checkpoint.get("name", "")).strip()
        if not checkpoint_name:
            raise SystemExit(f"Asset {asset.get('asset_id', '<unknown>')} missing checkpoint.name")

        inspection_profile_id = str(asset.get("inspection_profile_id", "")).strip()
        if inspection_profiles and inspection_profile_id and inspection_profile_id not in inspection_profiles:
            raise SystemExit(
                f"Asset {asset.get('asset_id', '<unknown>')} references unknown inspection profile "
                f"{inspection_profile_id}")

        loaded_profiles.append(
            AssetProfile(
                checkpoint=Checkpoint(
                    checkpoint_name,
                    float(checkpoint.get("x", 0.0)),
                    float(checkpoint.get("y", 0.0)),
                    float(checkpoint.get("yaw", 0.0)),
                ),
                asset_id=str(asset.get("asset_id", checkpoint_name)),
                display_name=str(asset.get("name", checkpoint_name)),
                asset_type=str(asset.get("asset_type", "generic_asset")),
                zone=str(asset.get("zone", "unknown")),
                priority=int(asset.get("priority", 1)),
                enabled_modalities=tuple(asset.get("enabled_modalities", [])),
                criticality=str(asset.get("criticality", "HIGH")),
                owner_team=str(asset.get("owner_team", "unassigned")),
                inspection_profile_id=inspection_profile_id,
                status=str(asset.get("status", "ACTIVE")),
                tags=tuple(asset.get("tags", [])),
                viewpoint_id=str(
                    checkpoint.get("viewpoint_id", f"vp_{checkpoint_name}")
                ),
                position_tolerance_m=float(checkpoint.get("position_tolerance_m", 1.75)),
                orientation_tolerance_rad=float(checkpoint.get("orientation_tolerance_rad", 0.35)),
            )
        )

    return loaded_profiles


def station_pose(checkpoint: Checkpoint) -> tuple[float, float, float]:
    offset = 1.25
    station_yaw = checkpoint.yaw + math.pi
    return (
        checkpoint.x + math.cos(checkpoint.yaw) * offset,
        checkpoint.y + math.sin(checkpoint.yaw) * offset,
        math.atan2(math.sin(station_yaw), math.cos(station_yaw)),
    )


def format_float(value: float) -> str:
    return f"{value:.3f}"


def box_visual(
    name: str,
    pose: tuple[float, float, float, float, float, float],
    size: tuple[float, float, float],
    color: tuple[float, float, float],
) -> str:
    return f"""
      <visual name='{name}'>
        <pose>{format_float(pose[0])} {format_float(pose[1])} {format_float(pose[2])} {format_float(pose[3])} {format_float(pose[4])} {format_float(pose[5])}</pose>
        <geometry>
          <box>
            <size>{format_float(size[0])} {format_float(size[1])} {format_float(size[2])}</size>
          </box>
        </geometry>
        <material>
          <ambient>{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} 1</ambient>
          <diffuse>{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} 1</diffuse>
          <specular>0.040 0.040 0.040 1</specular>
        </material>
      </visual>"""


def cylinder_visual(
    name: str,
    pose: tuple[float, float, float, float, float, float],
    radius: float,
    length: float,
    color: tuple[float, float, float],
) -> str:
    return f"""
      <visual name='{name}'>
        <pose>{format_float(pose[0])} {format_float(pose[1])} {format_float(pose[2])} {format_float(pose[3])} {format_float(pose[4])} {format_float(pose[5])}</pose>
        <geometry>
          <cylinder>
            <radius>{format_float(radius)}</radius>
            <length>{format_float(length)}</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} 1</ambient>
          <diffuse>{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} 1</diffuse>
          <specular>0.040 0.040 0.040 1</specular>
        </material>
      </visual>"""


def build_accessory_visuals(asset_type: str) -> list[str]:
    steel = (0.27, 0.34, 0.42)
    graphite = (0.19, 0.24, 0.30)
    blue = (0.16, 0.38, 0.70)
    slate = (0.50, 0.58, 0.66)
    visuals: list[str] = []

    if asset_type == "pump":
        visuals.extend([
            cylinder_visual("pump_body", (0.00, 0.18, 0.32, 1.5708, 0, 0), 0.11, 0.30, blue),
            cylinder_visual("pump_motor", (-0.02, -0.18, 0.34, 1.5708, 0, 0), 0.10, 0.24, graphite),
            box_visual("pump_skid", (0.00, 0.00, 0.18, 0, 0, 0), (0.54, 0.36, 0.08), steel),
        ])
    elif asset_type == "compressor":
        visuals.extend([
            cylinder_visual("compressor_tank_a", (0.00, 0.18, 0.34, 1.5708, 0, 0), 0.10, 0.38, blue),
            cylinder_visual("compressor_tank_b", (0.00, -0.18, 0.34, 1.5708, 0, 0), 0.10, 0.38, blue),
            box_visual("compressor_top", (0.00, 0.00, 0.62, 0, 0, 0), (0.42, 0.48, 0.10), graphite),
        ])
    elif asset_type == "electrical_panel":
        visuals.extend([
            box_visual("panel_door", (0.142, 0.0, 0.50, 0, 0, 0), (0.010, 0.48, 0.60), slate),
            box_visual("panel_breakers", (0.151, 0.0, 0.52, 0, 0, 0), (0.010, 0.26, 0.24), graphite),
        ])
    elif asset_type == "valve_manifold":
        visuals.extend([
            cylinder_visual("valve_body", (0.00, 0.00, 0.40, 1.5708, 0, 0), 0.10, 0.42, slate),
            cylinder_visual("valve_wheel", (0.16, 0.00, 0.56, 0, 1.5708, 0), 0.14, 0.04, graphite),
        ])
    elif asset_type == "conveyor_drive":
        visuals.extend([
            box_visual("conveyor_head", (0.00, 0.00, 0.42, 0, 0, 0), (0.52, 0.18, 0.14), graphite),
            cylinder_visual("roller_a", (-0.18, 0.00, 0.42, 1.5708, 0, 0), 0.08, 0.18, steel),
            cylinder_visual("roller_b", (0.18, 0.00, 0.42, 1.5708, 0, 0), 0.08, 0.18, steel),
        ])

    return visuals


def build_station_model(profile: AssetProfile, issue: IssueTemplate) -> str:
    state = STATE_LIBRARY[issue.visual_state]
    pose_x, pose_y, pose_yaw = station_pose(profile.checkpoint)
    signal = state["color"]
    body = (0.72, 0.75, 0.79)
    dark = (0.16, 0.19, 0.23)
    steel = (0.27, 0.34, 0.42)
    bezel = (0.12, 0.16, 0.21)
    fascia = (0.36, 0.42, 0.48)

    visuals = [
        box_visual("cabinet_body", (0, 0, 0.46, 0, 0, 0), (0.34, 0.66, 0.92), body),
        box_visual("base_plinth", (0, 0, 0.08, 0, 0, 0), (0.48, 0.78, 0.16), dark),
        box_visual("front_bezel", (0.162, 0, 0.58, 0, 0, 0), (0.020, 0.56, 0.54), bezel),
        box_visual("front_signal", (0.176, 0, 0.58, 0, 0, 0), (0.010, 0.40, 0.40), signal),
        box_visual("header_strip", (0, 0, 0.81, 0, 0, 0), (0.342, 0.66, 0.10), fascia),
        box_visual("service_drawer", (0.151, 0, 0.24, 0, 0, 0), (0.010, 0.40, 0.10), dark),
        cylinder_visual("signal_beacon", (0.12, 0.0, 0.92, 1.5708, 0, 0), 0.05, 0.10, signal),
        cylinder_visual("signal_beacon_base", (0.10, 0.0, 0.92, 1.5708, 0, 0), 0.07, 0.04, bezel),
        box_visual("floor_plate", (0.0, 0.0, 0.02, 0, 0, 0), (0.70, 0.80, 0.04), steel),
    ]
    visuals.extend(build_accessory_visuals(profile.asset_type))

    return f"""
    <model name='inspection_station_{profile.checkpoint.name}'>
      <static>true</static>
      <pose>{format_float(pose_x)} {format_float(pose_y)} 0 0 0 {format_float(pose_yaw)}</pose>
      <link name='cabinet'>
        <collision name='body_collision'>
          <pose>0 0 0.46 0 0 0</pose>
          <geometry>
            <box>
              <size>0.34 0.66 0.92</size>
            </box>
          </geometry>
        </collision>
        {''.join(visuals)}
      </link>
    </model>"""


def build_clutter_model(index: int, rng: random.Random, xy: tuple[float, float]) -> str:
    x, y = xy
    yaw = rng.uniform(-math.pi, math.pi)
    variant = index % 4
    if variant == 0:
        color = (0.44, 0.49, 0.56)
        return f"""
    <model name='decor_crate_{index}'>
      <static>true</static>
      <pose>{format_float(x)} {format_float(y)} 0 0 0 {format_float(yaw)}</pose>
      <link name='crate'>
        <collision name='crate_collision'>
          <pose>0 0 0.28 0 0 0</pose>
          <geometry><box><size>0.64 0.48 0.56</size></box></geometry>
        </collision>
        {box_visual("crate_visual", (0, 0, 0.28, 0, 0, 0), (0.64, 0.48, 0.56), color)}
      </link>
    </model>"""
    if variant == 1:
        color = (0.16, 0.33, 0.72)
        return f"""
    <model name='decor_drum_{index}'>
      <static>true</static>
      <pose>{format_float(x)} {format_float(y)} 0 0 0 {format_float(yaw)}</pose>
      <link name='drum'>
        <collision name='drum_collision'>
          <pose>0 0 0.43 0 0 0</pose>
          <geometry><cylinder><radius>0.22</radius><length>0.86</length></cylinder></geometry>
        </collision>
        {cylinder_visual("drum_visual", (0, 0, 0.43, 1.5708, 0, 0), 0.22, 0.86, color)}
      </link>
    </model>"""
    if variant == 2:
        cone_color = (0.18, 0.46, 0.78)
        return f"""
    <model name='decor_cone_{index}'>
      <static>true</static>
      <pose>{format_float(x)} {format_float(y)} 0 0 0 {format_float(yaw)}</pose>
      <link name='cone'>
        <collision name='cone_collision'>
          <pose>0 0 0.22 0 0 0</pose>
          <geometry><cylinder><radius>0.18</radius><length>0.44</length></cylinder></geometry>
        </collision>
        {cylinder_visual("cone_base", (0, 0, 0.06, 1.5708, 0, 0), 0.20, 0.04, (0.12, 0.12, 0.12))}
        {cylinder_visual("cone_visual", (0, 0, 0.22, 1.5708, 0, 0), 0.12, 0.36, cone_color)}
      </link>
    </model>"""
    rack_color = (0.32, 0.38, 0.46)
    return f"""
    <model name='decor_pipe_rack_{index}'>
      <static>true</static>
      <pose>{format_float(x)} {format_float(y)} 0 0 0 {format_float(yaw)}</pose>
      <link name='rack'>
        {box_visual("rack_base", (0, 0, 0.30, 0, 0, 0), (0.70, 0.20, 0.60), rack_color)}
        {cylinder_visual("pipe_a", (0.0, 0.00, 0.56, 1.5708, 0, 0), 0.06, 0.72, (0.46, 0.58, 0.66))}
        {cylinder_visual("pipe_b", (0.0, 0.00, 0.42, 1.5708, 0, 0), 0.06, 0.72, (0.16, 0.49, 0.76))}
      </link>
    </model>"""


def build_yaml_report(data: dict) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, dict):
                    lines.append(f"  {nested_key}:")
                    for child_key, child_value in nested_value.items():
                        lines.append(f"    {child_key}: {json.dumps(child_value)}")
                else:
                    lines.append(f"  {nested_key}: {json.dumps(nested_value)}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for child_key, child_value in item.items():
                        lines.append(f"      {child_key}: {json.dumps(child_value)}")
                else:
                    lines.append(f"  - {json.dumps(item)}")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    return "\n".join(lines) + "\n"


def draw_sensor_value(rng: random.Random, value_range: tuple[float, float], enabled: bool) -> float:
    if not enabled:
        return 0.0
    return round(rng.uniform(value_range[0], value_range[1]), 2)


def pick_issue(profile: AssetProfile, severity_key: str, rng: random.Random) -> IssueTemplate:
    if severity_key == "nominal":
        return NOMINAL_ISSUE
    return rng.choice(ISSUE_LIBRARY[profile.asset_type][severity_key])


def select_profiles(asset_profiles: list[AssetProfile], target_assets: set[str]) -> list[AssetProfile]:
    if not target_assets:
        return list(asset_profiles)

    selected = []
    for profile in asset_profiles:
        aliases = {
            profile.asset_id.lower(),
            profile.display_name.lower(),
            profile.checkpoint.name.lower(),
        }
        if aliases & target_assets:
            selected.append(profile)
    return selected


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    allow_critical = parse_bool(args.allow_critical)
    asset_registry_path = Path(args.asset_registry)
    site_config_path = Path(args.site_config)
    inspection_profiles_path = Path(args.inspection_profiles)
    site_config = load_site_config(site_config_path)
    inspection_profiles = load_inspection_profiles(inspection_profiles_path)
    asset_profiles = load_asset_profiles(asset_registry_path, inspection_profiles)

    target_assets = parse_target_assets(args.target_assets)
    selected_profiles = select_profiles(asset_profiles, target_assets)
    if not selected_profiles:
        available_assets = ", ".join(profile.asset_id for profile in asset_profiles)
        raise SystemExit(f"No target assets matched. Available assets: {available_assets}")

    anomaly_count = rng.randint(args.min_anomalies, min(args.max_anomalies, len(selected_profiles)))
    anomalous_indices = set(rng.sample(range(len(selected_profiles)), anomaly_count))
    critical_candidates: set[int] = set()
    if allow_critical:
        critical_candidates = {
            index for index in anomalous_indices
            if rng.random() < 0.45
        }
        if not critical_candidates and anomalous_indices:
            critical_candidates = {rng.choice(tuple(anomalous_indices))}

    station_states: dict[str, dict] = {}
    checkpoints_yaml: list[dict] = []
    dynamic_models: list[str] = []

    for index, profile in enumerate(selected_profiles):
        if index not in anomalous_indices:
            severity_key = "nominal"
        elif index in critical_candidates:
            severity_key = "critical"
        else:
            severity_key = "warning"

        issue = pick_issue(profile, severity_key, rng)
        station_state = dict(STATE_LIBRARY[issue.visual_state])
        station_state.update({
            "label": issue.label,
            "severity": issue.severity,
            "recommended_action": issue.recommended_action,
            "description": issue.description,
            "state_key": issue.visual_state,
            "asset_id": profile.asset_id,
            "asset_display_name": profile.display_name,
            "asset_type": profile.asset_type,
            "zone": profile.zone,
            "asset_priority": profile.priority,
            "enabled_modalities": list(profile.enabled_modalities),
            "anomaly_sources": list(issue.anomaly_sources),
            "thermal_threshold_c": THERMAL_ALERT_C,
            "acoustic_threshold_db": ACOUSTIC_ALERT_DB,
            "gas_threshold_ppm": GAS_ALERT_PPM,
            "thermal_delta_c": draw_sensor_value(
                rng,
                issue.thermal_range,
                "thermal" in profile.enabled_modalities,
            ),
            "acoustic_db": draw_sensor_value(
                rng,
                issue.acoustic_range,
                "acoustic" in profile.enabled_modalities,
            ),
            "gas_ppm": draw_sensor_value(
                rng,
                issue.gas_range,
                "gas" in profile.enabled_modalities,
            ),
            "pose": {
                "x": round(station_pose(profile.checkpoint)[0], 3),
                "y": round(station_pose(profile.checkpoint)[1], 3),
                "yaw": round(station_pose(profile.checkpoint)[2], 3),
            },
        })
        station_states[profile.checkpoint.name] = station_state

        checkpoints_yaml.append({
            "name": profile.checkpoint.name,
            "station_id": profile.checkpoint.name,
            "asset_id": profile.asset_id,
            "asset_display_name": profile.display_name,
            "asset_type": profile.asset_type,
            "zone": profile.zone,
            "asset_priority": profile.priority,
            "enabled_modalities": list(profile.enabled_modalities),
            "criticality": profile.criticality,
            "owner_team": profile.owner_team,
            "inspection_profile_id": profile.inspection_profile_id,
            "asset_status": profile.status,
            "asset_tags": list(profile.tags),
            "x": round(profile.checkpoint.x, 3),
            "y": round(profile.checkpoint.y, 3),
            "yaw": round(profile.checkpoint.yaw, 3),
            "viewpoint_id": profile.viewpoint_id or f"vp_{profile.checkpoint.name}",
            "position_tolerance_m": profile.position_tolerance_m,
            "orientation_tolerance_rad": profile.orientation_tolerance_rad,
            "inspection_mode": "visual_station",
        })
        dynamic_models.append(build_station_model(profile, issue))

    clutter_pool = CLUTTER_POINTS[:]
    rng.shuffle(clutter_pool)
    for index, point in enumerate(clutter_pool[: max(0, min(args.clutter_count, len(clutter_pool)))]):
        dynamic_models.append(build_clutter_model(index, rng, point))

    template_world = Path(args.template_world).read_text()
    generated_world = template_world.replace(
        "    <!-- GENERATED_DYNAMIC_MODELS -->",
        "\n".join(dynamic_models),
    )

    mission_profile = "targeted_follow_up" if target_assets else "routine_autonomous_round"
    scenario_id = f"advanced_multimodal_seed_{args.seed}"
    generated_at_utc = datetime.now(timezone.utc).isoformat()
    run_id = f"{scenario_id}_{generated_at_utc.replace(':', '').replace('-', '').replace('.', '').replace('+00:00', 'Z')}"
    generated_world_path = output_dir / "generated_world.sdf"
    generated_ground_truth_path = output_dir / "ground_truth.yaml"
    generated_manifest_path = output_dir / "scenario_manifest.json"
    generated_checkpoint_path = output_dir / "generated_checkpoints.yaml"

    generated_world_path.write_text(generated_world)

    checkpoint_yaml_lines = [
        f"schema_version: {json.dumps('benchmark_checkpoint_config.v2')}",
        "map_frame: map",
        f"site_id: {json.dumps(site_config.site_id)}",
        f"site_name: {json.dumps(site_config.name)}",
        f"site_timezone: {json.dumps(site_config.timezone)}",
        f"coordinate_frame: {json.dumps(site_config.coordinate_frame)}",
        f"scenario_id: {json.dumps(scenario_id)}",
        f"run_id: {json.dumps(run_id)}",
        f"mission_profile: {json.dumps(mission_profile)}",
        f"seed: {args.seed}",
        f"asset_registry_file: {json.dumps(str(asset_registry_path.resolve()))}",
        f"site_config_file: {json.dumps(str(site_config_path.resolve()))}",
        f"inspection_profiles_file: {json.dumps(str(inspection_profiles_path.resolve()))}",
        f"ground_truth_file: {json.dumps(str(generated_ground_truth_path))}",
        f"selected_asset_ids: {json.dumps([profile.asset_id for profile in selected_profiles])}",
        "",
        "checkpoints:",
    ]
    for checkpoint in checkpoints_yaml:
        checkpoint_yaml_lines.extend([
            f"  - name: {checkpoint['name']}",
            f"    station_id: {checkpoint['station_id']}",
            f"    asset_id: {checkpoint['asset_id']}",
            f"    asset_display_name: {json.dumps(checkpoint['asset_display_name'])}",
            f"    asset_type: {json.dumps(checkpoint['asset_type'])}",
            f"    zone: {json.dumps(checkpoint['zone'])}",
            f"    asset_priority: {checkpoint['asset_priority']}",
            f"    enabled_modalities: {json.dumps(checkpoint['enabled_modalities'])}",
            f"    criticality: {json.dumps(checkpoint['criticality'])}",
            f"    owner_team: {json.dumps(checkpoint['owner_team'])}",
            f"    inspection_profile_id: {json.dumps(checkpoint['inspection_profile_id'])}",
            f"    asset_status: {json.dumps(checkpoint['asset_status'])}",
            f"    asset_tags: {json.dumps(checkpoint['asset_tags'])}",
            f"    x: {checkpoint['x']:.2f}",
            f"    y: {checkpoint['y']:.2f}",
            f"    yaw: {checkpoint['yaw']:.2f}",
            f"    viewpoint_id: {json.dumps(checkpoint['viewpoint_id'])}",
            f"    position_tolerance_m: {checkpoint['position_tolerance_m']:.2f}",
            f"    orientation_tolerance_rad: {checkpoint['orientation_tolerance_rad']:.2f}",
            f"    inspection_mode: {checkpoint['inspection_mode']}",
        ])
        checkpoint_yaml_lines.append("")
    generated_checkpoint_path.write_text("\n".join(checkpoint_yaml_lines).strip() + "\n")

    generated_ground_truth_path.write_text(build_yaml_report({
        "schema_version": "benchmark_ground_truth.v2",
        "site_id": site_config.site_id,
        "site_name": site_config.name,
        "site_timezone": site_config.timezone,
        "coordinate_frame": site_config.coordinate_frame,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "mission_profile": mission_profile,
        "seed": args.seed,
        "allow_critical": allow_critical,
        "asset_registry_file": str(asset_registry_path.resolve()),
        "site_config_file": str(site_config_path.resolve()),
        "inspection_profiles_file": str(inspection_profiles_path.resolve()),
        "generated_at_utc": generated_at_utc,
        "selected_asset_ids": [profile.asset_id for profile in selected_profiles],
        "stations": station_states,
    }))
    generated_manifest_path.write_text(json.dumps({
        "schema_version": "benchmark_scenario_manifest.v2",
        "site": {
            "schema_version": site_config.schema_version,
            "site_id": site_config.site_id,
            "name": site_config.name,
            "timezone": site_config.timezone,
            "map_id": site_config.map_id,
            "coordinate_frame": site_config.coordinate_frame,
            "status": site_config.status,
            "metadata": site_config.metadata,
        },
        "scenario_id": scenario_id,
        "run_id": run_id,
        "mission_profile": mission_profile,
        "seed": args.seed,
        "allow_critical": allow_critical,
        "asset_registry_file": str(asset_registry_path.resolve()),
        "site_config_file": str(site_config_path.resolve()),
        "inspection_profiles_file": str(inspection_profiles_path.resolve()),
        "world_file": str(generated_world_path),
        "checkpoint_file": str(generated_checkpoint_path),
        "ground_truth_file": str(generated_ground_truth_path),
        "selected_assets": [profile.asset_id for profile in selected_profiles],
        "selected_asset_records": [
            {
                "asset_id": profile.asset_id,
                "name": profile.display_name,
                "asset_type": profile.asset_type,
                "zone": profile.zone,
                "priority": profile.priority,
                "criticality": profile.criticality,
                "owner_team": profile.owner_team,
                "inspection_profile_id": profile.inspection_profile_id,
                "status": profile.status,
                "tags": list(profile.tags),
                "checkpoint_name": profile.checkpoint.name,
                "viewpoint_id": profile.viewpoint_id,
                "position_tolerance_m": profile.position_tolerance_m,
                "orientation_tolerance_rad": profile.orientation_tolerance_rad,
                "enabled_modalities": list(profile.enabled_modalities),
            }
            for profile in selected_profiles
        ],
        "stations": station_states,
    }, indent=2) + "\n")

    print(f"Generated advanced benchmark scenario {scenario_id}")
    print(f"  run_id: {run_id}")
    print(f"  site_id: {site_config.site_id}")
    print(f"  mission_profile: {mission_profile}")
    print(f"  allow_critical: {allow_critical}")
    print(f"  assets: {', '.join(profile.asset_id for profile in selected_profiles)}")
    print(f"  world: {generated_world_path}")
    print(f"  checkpoints: {generated_checkpoint_path}")
    print(f"  ground_truth: {generated_ground_truth_path}")


if __name__ == "__main__":
    main()
