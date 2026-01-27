"""Geodetic primitives for GPS coordinate manipulation.

This module provides accurate coordinate conversions and calculations using
the WGS84 ellipsoid model. All functions work WITHOUT the generated Skydio SDK.

=== COORDINATE SYSTEMS ===

GPS Frame:
    - latitude: degrees, -90 to 90
    - longitude: degrees, -180 to 180
    - altitude: meters above takeoff (WORLD_TAKEOFF frame)

ENU (East-North-Up) Local Frame:
    - east: meters (positive = east)
    - north: meters (positive = north)
    - up: meters (positive = up)
    - Origin: A chosen GPS reference point

=== HEADING CONVENTION ===

Skydio uses ENU (East-North-Up) heading:
    0°   = East
    90°  = North
    180° = West
    270° = South

This is DIFFERENT from compass heading:
    Compass: 0° = North, 90° = East
    ENU:     0° = East,  90° = North

Conversion:
    enu_deg = (90 - compass_deg) % 360
    compass_deg = (90 - enu_deg) % 360

=== GIMBAL PITCH CONVENTION ===

    0°   = Level (looking at horizon)
    +90° = Straight down (nadir)
    -90° = Straight up (zenith)

=== WGS84 ELLIPSOID ===

    Equatorial radius: 6,378,137 m
    Polar radius: 6,356,752.3 m

Using the ellipsoid model prevents ~0.3% error at mid-latitudes
compared to spherical approximations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional


# =============================================================================
# Constants
# =============================================================================

# WGS84 ellipsoid constants
EARTH_EQUATORIAL_RADIUS_M = 6_378_137.0  # Semi-major axis (a)
EARTH_POLAR_RADIUS_M = 6_356_752.3       # Semi-minor axis (b)

# Derived: First eccentricity squared
_E_SQ = 1 - (EARTH_POLAR_RADIUS_M / EARTH_EQUATORIAL_RADIUS_M) ** 2

# Mission limits
DEFAULT_SPEED_MPS = 5.0
DEFAULT_GIMBAL_PITCH_DEG = 0.0  # Level with horizon


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass(frozen=True)
class GpsPoint:
    """A point in GPS coordinates with mission altitude.
    
    Attributes:
        lat: Latitude in degrees (-90 to 90)
        lon: Longitude in degrees (-180 to 180)
        alt: Altitude in meters (often defaulting to above takeoff)
    
    Note:
        The alt field often defaults to above takeoff in Skydio missions, 
        but GPS frame can be represented in the API.
    
    Example:
        # Building in San Francisco, fly at 100m above takeoff
        tower = GpsPoint(lat=37.7897, lon=-122.3972, alt=100)
    """
    lat: float
    lon: float
    alt: float = 0.0


@dataclass(frozen=True)
class EnuPoint:
    """A point in local East-North-Up coordinates.
    
    Attributes:
        east: Meters east of origin (positive = east)
        north: Meters north of origin (positive = north)
        up: Meters above origin (positive = up)
    
    Example:
        # 100m east, 50m north, 30m up from origin
        offset = EnuPoint(east=100, north=50, up=30)
    """
    east: float
    north: float
    up: float = 0.0


def make_waypoint(
    position: GpsPoint,
    look_at: Optional[GpsPoint] = None,
    heading_deg: Optional[float] = None,
    pitch_deg: Optional[float] = None,
    speed_mps: float = DEFAULT_SPEED_MPS,
    photo: bool = False,
) -> dict:
    """Create a waypoint dict, optionally computing heading/pitch from look_at.
    
    This is a simple helper function that returns a dict - no classes, no SDK dependency.
    If look_at is provided, heading and pitch are auto-computed to face that target.
    
    Args:
        position: GPS position of the drone
        look_at: Optional target GPS point - if provided, auto-computes heading/pitch
        heading_deg: Heading in ENU degrees (0=East, 90=North). Auto-computed if look_at set.
        pitch_deg: Gimbal pitch in degrees (0=level, +90=down). Auto-computed if look_at set.
        speed_mps: Flight speed in meters per second
        photo: Whether to take a photo at this waypoint
        
    Returns:
        Dict with keys: latitude_deg, longitude_deg, altitude_m, heading_deg, pitch_deg, speed_mps, photo
    
    Example:
        # Explicit heading/pitch
        wp = make_waypoint(
            position=GpsPoint(lat=37.79, lon=-122.40, alt=100),
            heading_deg=90,  # Face north
            pitch_deg=30,    # Look down 30 degrees
        )
        
        # Auto-computed from look_at
        target = GpsPoint(lat=37.7897, lon=-122.3972, alt=50)
        wp = make_waypoint(
            position=GpsPoint(lat=37.79, lon=-122.40, alt=100),
            look_at=target,  # heading and pitch computed automatically
            photo=True,
        )
    """
    # Auto-compute heading/pitch from look_at if provided
    if look_at is not None:
        if heading_deg is None:
            heading_deg = heading_between(position, look_at)
        if pitch_deg is None:
            pitch_deg = pitch_to_target(position, look_at)
    
    # Default to 0 if still None
    if heading_deg is None:
        heading_deg = 0.0
    if pitch_deg is None:
        pitch_deg = 0.0
    
    return {
        "latitude_deg": position.lat,
        "longitude_deg": position.lon,
        "altitude_m": position.alt,
        "heading_deg": heading_deg,
        "pitch_deg": pitch_deg,
        "speed_mps": speed_mps,
        "photo": photo,
    }


# =============================================================================
# Local Coordinate Frame
# =============================================================================

class LocalFrame:
    """Local coordinate frame for GPS ↔ ENU conversions.
    
    Creates a tangent plane at the origin point using WGS84 ellipsoid model.
    Accurate for distances up to ~10km from origin.
    
    Example:
        # Create frame centered on target
        target = GpsPoint(lat=37.7897, lon=-122.3972, alt=0)
        frame = LocalFrame(target)
        
        # Convert GPS to local meters
        enu = frame.gps_to_enu(GpsPoint(lat=37.7900, lon=-122.3970, alt=50))
        
        # Convert local meters to GPS
        gps = frame.enu_to_gps(EnuPoint(east=100, north=200, up=50))
    """
    
    def __init__(self, origin: GpsPoint):
        """Initialize local frame at the given GPS origin.
        
        Args:
            origin: The GPS point that becomes (0, 0, 0) in ENU coordinates
        """
        self.origin = origin
        lat_rad = math.radians(origin.lat)
        
        # WGS84 radii of curvature at this latitude
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        
        # Prime vertical radius of curvature (east-west)
        self._N = EARTH_EQUATORIAL_RADIUS_M / math.sqrt(1 - _E_SQ * sin_lat ** 2)
        
        # Meridional radius of curvature (north-south)
        self._M = EARTH_EQUATORIAL_RADIUS_M * (1 - _E_SQ) / (1 - _E_SQ * sin_lat ** 2) ** 1.5
        
        # Meters per degree at this latitude
        self._m_per_deg_lat = math.radians(1) * self._M
        self._m_per_deg_lon = math.radians(1) * self._N * cos_lat
    
    def gps_to_enu(self, point: GpsPoint) -> EnuPoint:
        """Convert GPS coordinates to local ENU meters.
        
        Args:
            point: GPS point to convert
            
        Returns:
            EnuPoint with east, north, up offsets from origin
        """
        dlat = point.lat - self.origin.lat
        dlon = point.lon - self.origin.lon
        dalt = point.alt - self.origin.alt
        
        east = dlon * self._m_per_deg_lon
        north = dlat * self._m_per_deg_lat
        up = dalt
        
        return EnuPoint(east=east, north=north, up=up)
    
    def enu_to_gps(self, point: EnuPoint) -> GpsPoint:
        """Convert local ENU meters to GPS coordinates.
        
        Args:
            point: ENU point to convert
            
        Returns:
            GpsPoint with lat, lon, alt
        """
        dlat = point.north / self._m_per_deg_lat
        dlon = point.east / self._m_per_deg_lon
        
        lat = self.origin.lat + dlat
        lon = self.origin.lon + dlon
        alt = self.origin.alt + point.up
        
        return GpsPoint(lat=lat, lon=lon, alt=alt)


# =============================================================================
# Heading and Pitch Calculations
# =============================================================================

def heading_between(from_point: GpsPoint, to_point: GpsPoint) -> float:
    """Compute ENU heading from one GPS point to another.
    
    ENU Convention:
        0°   = East
        90°  = North
        180° = West
        270° = South
    
    Args:
        from_point: Starting GPS position (where drone is)
        to_point: Target GPS position (what drone looks at)
        
    Returns:
        Heading in degrees [0, 360) in ENU convention
    
    Example:
        drone = GpsPoint(lat=37.79, lon=-122.40, alt=100)
        target = GpsPoint(lat=37.7897, lon=-122.3972, alt=50)
        heading = heading_between(drone, target)  # Returns heading to face target
    """
    frame = LocalFrame(from_point)
    enu = frame.gps_to_enu(to_point)
    
    # atan2(north, east) gives angle from east axis
    angle_rad = math.atan2(enu.north, enu.east)
    angle_deg = math.degrees(angle_rad)
    
    # Normalize to [0, 360)
    return angle_deg % 360.0


def pitch_to_target(from_point: GpsPoint, to_point: GpsPoint) -> float:
    """Compute gimbal pitch to look at a target.
    
    Gimbal Pitch Convention:
        0°   = Level (looking at horizon)
        +90° = Straight down
        -90° = Straight up
    
    Args:
        from_point: Camera GPS position (where drone is)
        to_point: Target GPS position (what drone looks at)
        
    Returns:
        Pitch in degrees (positive = looking down)
    
    Example:
        drone = GpsPoint(lat=37.79, lon=-122.40, alt=100)
        target = GpsPoint(lat=37.7897, lon=-122.3972, alt=50)  # 50m below
        pitch = pitch_to_target(drone, target)  # Returns positive (looking down)
    """
    frame = LocalFrame(from_point)
    enu = frame.gps_to_enu(to_point)
    
    horizontal_dist = math.sqrt(enu.east ** 2 + enu.north ** 2)
    vertical_dist = enu.up
    
    if horizontal_dist < 0.001:  # Very close horizontally
        return 90.0 if vertical_dist < 0 else -90.0
    
    pitch_rad = math.atan2(vertical_dist, horizontal_dist)
    return -math.degrees(pitch_rad)


def distance_between(point1: GpsPoint, point2: GpsPoint) -> float:
    """Compute 3D distance between two GPS points in meters.
    
    Args:
        point1: First GPS point
        point2: Second GPS point
        
    Returns:
        Distance in meters
    
    Example:
        p1 = GpsPoint(lat=37.79, lon=-122.40, alt=0)
        p2 = GpsPoint(lat=37.7897, lon=-122.3972, alt=100)
        dist = distance_between(p1, p2)  # Returns ~330m
    """
    frame = LocalFrame(point1)
    enu = frame.gps_to_enu(point2)
    return math.sqrt(enu.east ** 2 + enu.north ** 2 + enu.up ** 2)


# =============================================================================
# Heading Conversion Utilities
# =============================================================================

def compass_to_enu(compass_deg: float) -> float:
    """Convert compass heading to ENU heading.
    
    Compass: 0° = North, 90° = East, 180° = South, 270° = West
    ENU:     0° = East,  90° = North, 180° = West, 270° = South
    
    Args:
        compass_deg: Heading in compass convention
        
    Returns:
        Heading in ENU convention [0, 360)
    
    Example:
        compass_to_enu(0)    # Returns 90 (North in compass = 90° in ENU)
        compass_to_enu(90)   # Returns 0 (East in compass = 0° in ENU)
    """
    return (90.0 - compass_deg) % 360.0


def enu_to_compass(enu_deg: float) -> float:
    """Convert ENU heading to compass heading.
    
    Args:
        enu_deg: Heading in ENU convention
        
    Returns:
        Heading in compass convention [0, 360)
    
    Example:
        enu_to_compass(0)    # Returns 90 (0° ENU = East = 90° compass)
        enu_to_compass(90)   # Returns 0 (90° ENU = North = 0° compass)
    """
    return (90.0 - enu_deg) % 360.0


# =============================================================================
# Angle Utilities
# =============================================================================

def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return math.radians(degrees)


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(radians)


