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

# ==========================================
# 2. Robot Fleet Settings
# ==========================================
NUM_ROBOTS = 15          # Recommended: Between 10 and 20
ROBOT_BASE_SPEED = 3.0   # Movement speed in grid units per second (visual)
ROBOT_MAX_SPEED = 6.0    # Maximum speed AI can set
ROBOT_MIN_SPEED = 1.0    # Minimum speed AI can set
TICK_RATE = 30           # Simulation logic ticks per second

# ==========================================
# 3. Visuals & Aesthetics (PyVista)
# ==========================================
THEME = 'dark'

# Shelf aesthetics
COLOR_SHELF = '#1a365d'      # Dark transparent blue
ALPHA_SHELF = 0.6            # Transparency

# Robot aesthetics
COLOR_ROBOT_IDLE = '#888888' # Gray
COLOR_ROBOT_FETCH = '#ff6600'  # Neon Orange (going to fetch a package from a shelf)
COLOR_ROBOT_CARRY = '#39ff14'  # Neon Green (carrying a package to unloading zone)

# Trails
COLOR_TRAIL = '#ffffff'      # White trail behind robots
TRAIL_LENGTH = 15            # Number of points in the trail

# Dimensions
ROBOT_SIZE = 0.5
SHELF_SIZE = 0.8
