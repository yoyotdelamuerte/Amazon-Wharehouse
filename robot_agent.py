import numpy as np
import config

class RobotState:
    IDLE = 0
    MOVING = 1
    LOADING = 2
    CHARGING = 3
    RETURNING = 4


class RobotAgent:
    """
    Represents a single robot entity in the warehouse.
    Manages continuous 3D position logic over time based on grid paths.
    """
    def __init__(self, robot_id, start_pos):
        self.robot_id = robot_id
        
        # Battery setup
        self.charging_station_pos = start_pos
        self.battery_level = config.BATTERY_MAX
        
        # Position in continuous 3D space: (x, y, z)
        self.pos = np.array([float(start_pos[0]), float(start_pos[1]), 0.0])
        self.grid_pos = start_pos
        self.next_node = None
        
        self.facing_angle = 0.0
        self.speed = config.ROBOT_BASE_SPEED
        
        self.state = RobotState.IDLE
        self.color = config.COLOR_ROBOT_IDLE
        self.path = []
        
        self.inventory = []
        self.assigned_tasks = []
        self.current_weight = 0
        
        self.is_blocked = False
        self.was_blocked = False
        
        # simulated time to load/unload a package
        self.loading_timer = 0
        self.loading_duration = config.TICK_RATE * 1  # 1 second
        
        # Trailing path for visual aesthetics
        self.trail = []

    def set_path(self, path, state=RobotState.MOVING):
        """Assigns a new path to follow"""
        self.path = path
        if len(self.path) > 0:
            self.state = state
            self.next_node = self.path.pop(0)

    def update_color_aesthetic(self):
        """Dynamic color updates based on state and battery."""
        if self.state == RobotState.CHARGING:
            self.color = config.COLOR_ROBOT_CHARGING
        elif self.state == RobotState.RETURNING:
            self.color = config.COLOR_ROBOT_LOW_BATT
        elif self.state == RobotState.IDLE:
            self.color = config.COLOR_ROBOT_IDLE
        else: # MOVING or LOADING
            if self.current_weight > 0:
                self.color = config.COLOR_ROBOT_CARRY
            else:
                self.color = config.COLOR_ROBOT_FETCH

    def update(self):
        """Tick function applied per frame to update position and state"""
        if self.state == RobotState.CHARGING:
            self.battery_level += config.BATTERY_CHARGE_RATE
            if self.battery_level >= config.BATTERY_MAX:
                self.battery_level = config.BATTERY_MAX
                self.state = RobotState.IDLE
            self.update_color_aesthetic()
            return
            
        elif self.state == RobotState.IDLE:
            self.update_color_aesthetic()
            return
            
        elif self.state == RobotState.LOADING:
            self.loading_timer -= 1
            if self.loading_timer <= 0:
                if self.assigned_tasks:
                    task = self.assigned_tasks.pop(0)
                    task.picked_up = True
                    self.inventory.append(task)
                    self.current_weight += task.weight
                self.state = RobotState.IDLE
            self.update_color_aesthetic()
            return
            
        # Both MOVING and RETURNING behave similarly for movement
        elif self.state in (RobotState.MOVING, RobotState.RETURNING):
            if self.is_blocked:
                self.update_color_aesthetic()
                return
                
            if self.next_node is None:
                self.update_color_aesthetic()
                return
                
            # Deplete battery while moving
            self.battery_level -= config.BATTERY_DEPLETION_RATE
            if self.battery_level < 0:
                self.battery_level = 0
                
            # Move towards next_node continuously
            target_pos = np.array([float(self.next_node[0]), float(self.next_node[1]), 0.0])
            direction = target_pos - self.pos
            distance = np.linalg.norm(direction)
            if distance > 0.001:
                self.facing_angle = np.degrees(np.arctan2(direction[1], direction[0]))
            
            speed_per_tick = self.speed / config.TICK_RATE
            
            if distance <= speed_per_tick:
                # Waypoint reached
                self.pos = target_pos.copy()
                self.grid_pos = self.next_node
                
                # aesthetic trail logic
                self.trail.append(self.pos.copy())
                if len(self.trail) > config.TRAIL_LENGTH:
                    self.trail.pop(0)

                if len(self.path) > 0:
                    self.next_node = self.path.pop(0)
                else:
                    self.next_node = None
                    # End of path logic
                    if self.state == RobotState.RETURNING:
                        # Reached charging station
                        self.state = RobotState.CHARGING
                    elif any(self.grid_pos == drop['in'] for drop in config.MAP_DROPS):
                        # Reached unloading zone. 
                        # Dropping off is handled by FleetManager so it can track order completions.
                        self.state = RobotState.IDLE
                    else:
                        # Reached exit of unloading zone or intermediate stop
                        self.state = RobotState.IDLE
            else:
                # Intermediate step
                self.pos += (direction / distance) * speed_per_tick
                
            self.update_color_aesthetic()
