"""Mission building functions for Skydio SDK.

This module provides functions to build Skydio Mission objects from waypoints.
Requires the generated SDK - run `python generate_sdk.py` first.

For geodetic primitives (GpsPoint, LocalFrame, make_waypoint, etc.), see geo.py.

NOTE: Missions include expectedGpsOrigin with terrain elevation MSL for correct
altitude display in Skydio Cloud. Without this, missions may appear underground.

Usage:
    from geo import GpsPoint, LocalFrame, EnuPoint, make_waypoint
    from mission_helpers import build_mission
    import math
    
    # Create waypoints using helper function
    target = GpsPoint(lat=37.7897, lon=-122.3972, alt=0)
    frame = LocalFrame(target)
    
    waypoints = []
    for i in range(36):
        angle = math.radians(i * 10)
        enu = EnuPoint(east=80*math.cos(angle), north=80*math.sin(angle), up=100)
        gps = frame.enu_to_gps(enu)
        waypoints.append(make_waypoint(position=gps, look_at=target, photo=True))
    
    # Build mission (requires SDK)
    mission = build_mission(waypoints, name="Orbit Mission")
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

from geo import deg_to_rad

if TYPE_CHECKING:
    from skydio_client.models import Mission


def get_terrain_elevation(lat: float, lon: float, timeout: float = 10.0) -> float:
    """Look up terrain elevation MSL at a GPS coordinate.
    
    Uses the free Open-Elevation API. No API key required.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        timeout: Request timeout in seconds
        
    Returns:
        Terrain elevation in meters above mean sea level (MSL)
        
    Raises:
        RuntimeError: If the API request fails
    
    Example:
        # Ohio farmland
        elev = get_terrain_elevation(40.03045, -82.99777)  # Returns ~250m
    """
    import requests
    
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()["results"][0]["elevation"]
    except Exception as e:
        raise RuntimeError(f"Failed to get terrain elevation: {e}") from e


def build_mission(
    waypoints: List[dict],
    name: str = "Mission",
    terrain_elevation_msl: float = None,
    auto_start: bool = True,
) -> "Mission":
    """Build a Skydio Mission object from waypoint dicts.
    
    REQUIRES the generated SDK. Run `python generate_sdk.py` first.
    
    IMPORTANT: For correct altitude display in Skydio Cloud, provide
    terrain_elevation_msl (terrain height at takeoff location). Without this,
    missions may appear underground in the Cloud visualization.
    
    Args:
        waypoints: List of dicts with keys:
            - latitude_deg, longitude_deg, altitude_m
            - heading_deg (ENU: 0=East, 90=North)
            - pitch_deg (0=level, +90=down)
            - speed_mps
            - photo (bool)
        name: Display name for the mission
        terrain_elevation_msl: Terrain elevation at takeoff in meters MSL.
            If None, uses get_terrain_elevation() to look it up automatically.
            Required for correct altitude display in Cloud.
        auto_start: Whether mission starts automatically when uploaded
        
    Returns:
        Mission object ready to upload to Skydio API
        
    Raises:
        ImportError: If the SDK has not been generated yet
    
    Example:
        from geo import GpsPoint, make_waypoint
        
        target = GpsPoint(lat=37.7897, lon=-122.3972, alt=50)
        waypoints = [
            make_waypoint(GpsPoint(37.79, -122.40, 100), look_at=target, photo=True),
            make_waypoint(GpsPoint(37.79, -122.39, 100), heading_deg=180, photo=True),
        ]
        
        # Option 1: Auto-lookup terrain (requires internet)
        mission = build_mission(waypoints, name="My Mission")
        
        # Option 2: Provide terrain elevation manually
        mission = build_mission(waypoints, name="My Mission", terrain_elevation_msl=250.0)
    """
    # Validate input
    if not waypoints:
        raise ValueError("waypoints list cannot be empty")

    # Deferred import - gives helpful error if SDK not generated
    try:
        from skydio_client.models import (
            Action,
            CameraSettings,
            Mission,
            GpsOriginInfo,
            GotoWaypointActionArgs,
            Waypoint,
            PositionXy,
            PositionZ,
            Heading,
            GimbalPitch,
            MotionArgs,
            TraversalMotionArgs,
            LookAtMotionArgs,
            SetObstacleAvoidanceActionArgs,
            StopVideoActionArgs,
            TakePhotoActionArgs,
            ReturnSettings,
            SkillsActionArgsGotoWaypoint,
            SkillsActionArgsSequence,
            SkillsActionArgsSetObstacleAvoidance,
            SkillsActionArgsStopVideo,
            SkillsActionArgsTakePhoto,
            SkillsSequenceActionArgs,
        )
    except (ImportError, ModuleNotFoundError, TypeError) as e:
        raise ImportError(
            "Skydio SDK not available. Please run 'python generate_sdk.py' first.\n"
            f"Original error: {e}"
        ) from e
    
    # Get terrain elevation at first waypoint if not provided
    first_wp = waypoints[0]
    origin_lat = first_wp["latitude_deg"]
    origin_lon = first_wp["longitude_deg"]
    
    if terrain_elevation_msl is None:
        terrain_elevation_msl = get_terrain_elevation(origin_lat, origin_lon)
    
    def create_waypoint_sequence(wp_dict: dict) -> Action:
        """Create action sequence for a single waypoint."""
        waypoint_obj = Waypoint(
            xy=PositionXy(
                frame="GPS",
                x=wp_dict["latitude_deg"],
                y=wp_dict["longitude_deg"],
            ),
            z=PositionZ(
                frame="WORLD_TAKEOFF",
                value=wp_dict["altitude_m"],
            ),
            heading=Heading(
                value=deg_to_rad(wp_dict["heading_deg"]),
                frame="GPS",
            ),
            gimbal_pitch=GimbalPitch(value=deg_to_rad(wp_dict["pitch_deg"])),
        )
        
        motion_args = MotionArgs(
            traversal_args=TraversalMotionArgs(
                height_mode="CONSTANT_END",
                speed=wp_dict.get("speed_mps", 5.0),
            ),
            look_at_args=LookAtMotionArgs(
                heading_mode="CONSTANT_END",
                gimbal_pitch_mode="CONSTANT_END",
            ),
        )
        
        actions = [
            Action(
                action_key="SetObstacleAvoidance",
                args=SkillsActionArgsSetObstacleAvoidance(
                    set_obstacle_avoidance=SetObstacleAvoidanceActionArgs(
                        oa_setting="DEFAULT"
                    )
                ),
            ),
            Action(
                action_key="StopVideo",
                args=SkillsActionArgsStopVideo(
                    stop_video=StopVideoActionArgs(no_args=False)
                ),
            ),
            Action(
                action_key="GotoWaypoint",
                args=SkillsActionArgsGotoWaypoint(
                    goto_waypoint=GotoWaypointActionArgs(
                        waypoint=waypoint_obj,
                        motion_args=motion_args,
                    )
                ),
            ),
        ]
        
        if wp_dict.get("photo", False):
            actions.append(
                Action(
                    action_key="TakePhoto",
                    args=SkillsActionArgsTakePhoto(
                        take_photo=TakePhotoActionArgs(
                            camera_settings=CameraSettings(
                                recording_mode="PHOTO_DEFAULT",
                            ),
                        ),
                        is_skippable=True,
                    ),
                )
            )
        
        actions.append(
            Action(
                action_key="SetObstacleAvoidance",
                args=SkillsActionArgsSetObstacleAvoidance(
                    set_obstacle_avoidance=SetObstacleAvoidanceActionArgs(
                        oa_setting="DEFAULT"
                    )
                ),
            )
        )
        
        return Action(
            action_key="Sequence",
            args=SkillsActionArgsSequence(
                sequence=SkillsSequenceActionArgs(
                    name="",
                    actions=actions,
                )
            ),
        )
    
    # Build all waypoint sequences
    waypoint_sequences = [create_waypoint_sequence(wp) for wp in waypoints]
    
    # Wrap in root sequence
    root_sequence = Action(
        action_key="Sequence",
        args=SkillsActionArgsSequence(
            sequence=SkillsSequenceActionArgs(
                name="root_sequence",
                actions=waypoint_sequences,
            )
        ),
    )
    
    # Create mission with expected GPS origin for correct Cloud altitude display
    return Mission(
        display_name=name,
        expected_gps_origin=GpsOriginInfo(
            lat=origin_lat,
            lon=origin_lon,
            gps_altitude=terrain_elevation_msl,
            gps_heading=0,
        ),
        actions=[root_sequence],
        auto_start=auto_start,
        dock_mission=True,
        lost_connection_action="RETURN_TO_HOME",
        post_failure_action="DEFAULT_RETURN",
        post_mission_action="DEFAULT_RETURN",
        rtx_settings=ReturnSettings(
            wait_time=60,
            minimum_height=30,
            speed=5,
        ),
        use_rtx_settings=True,
        autonomous_abort_mission_on_failed_action=True,
    )


# Alias for backwards compatibility with main.py
def create_waypoint_mission_from_simple_waypoints(simple_waypoints: List[dict]) -> "Mission":
    """Create a waypoint mission from a list of simple waypoint dicts.
    
    This is an alias for build_mission() for backwards compatibility.
    
    Args:
        simple_waypoints: List of waypoint dicts
        
    Returns:
        Mission object
    """
    return build_mission(simple_waypoints, name="Waypoint Mission")
