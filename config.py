# config.py
"""
Configuration parameters for the 3D Automated Warehouse Simulation.
"""

# ==========================================
# 1. Environment Settings
# ==========================================
GRID_WIDTH = 20
GRID_HEIGHT = 20
NUM_SHELVES = 40  # Number of shelves to place as obstacles

# Locations
UNLOADING_ZONE_IN = (0, 0)   # Where robots drop off packages
UNLOADING_ZONE_OUT = (1, 0)  # Where robots exit to avoid blocking the entrance

# Charging Zones (5 spots along the top wall)
CHARGING_STATIONS = [(2, 19), (6, 19), (10, 19), (14, 19), (18, 19)]

# ==========================================
# 2. Robot Fleet Settings
# ==========================================
NUM_ROBOTS = 5           # Exact number dictated by charging stations
ROBOT_BASE_SPEED = 3.0   # Movement speed in grid units per second (visual)
ROBOT_MAX_SPEED = 6.0    # Maximum speed AI can set
ROBOT_MIN_SPEED = 1.0    # Minimum speed AI can set
TICK_RATE = 60           # Simulation logic ticks per second

# Battery Settings
BATTERY_MAX = 100.0
BATTERY_DEPLETION_RATE = 2.0 / TICK_RATE  # 2.0% per second while moving
BATTERY_CHARGE_RATE = 25.0 / TICK_RATE    # 25.0% per second while charging
BATTERY_THRESHOLD = 25.0                  # Return to charge when below this

# ==========================================
# 3. Visuals & Aesthetics (PyVista)
# ==========================================
THEME = 'document'           # White/Light background theme

# Environment aesthetics
COLOR_GROUND = '#E0E0E0'     # Light industrial concrete
COLOR_GROUND_EDGE = '#B0B0B0'

# Shelf aesthetics
COLOR_SHELF = '#505050'      # Grey metallic shelves
ALPHA_SHELF = 0.8            # Transparency

# Robot aesthetics
COLOR_ROBOT_IDLE = '#FFB300'       # Yellow-Orange (Caution/Industrial)
COLOR_ROBOT_FETCH = '#FF8F00'      # Deep Orange
COLOR_ROBOT_CARRY = '#2E7D32'      # Green success/running
COLOR_ROBOT_LOW_BATT = '#D32F2F'   # Red low battery alert
COLOR_ROBOT_CHARGING = '#1565C0'   # Blue charging state

# Zones
COLOR_UNLOAD_IN = '#D32F2F'        # Red for Drop-off IN
COLOR_UNLOAD_OUT = '#1976D2'       # Blue for Exit OUT
COLOR_CHARGING_PAD = '#00E676'     # Green parking pad

# Trails
COLOR_TRAIL = '#000000'      # Dark trail
TRAIL_LENGTH = 15            # Number of points in the trail

# Dimensions
ROBOT_SIZE = 0.5
SHELF_SIZE = 0.8
