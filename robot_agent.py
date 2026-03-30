import numpy as np
import config

class RobotState:
    IDLE = 0
    MOVING = 1
    LOADING = 2


class RobotAgent:
    """
    Represents a single robot entity in the warehouse.
    Manages continuous 3D position logic over time based on grid paths.
    """
    def __init__(self, robot_id, start_pos):
        self.robot_id = robot_id
        
        # Position in continuous 3D space: (x, y, z)
        self.pos = np.array([float(start_pos[0]), float(start_pos[1]), 0.0])
        self.grid_pos = start_pos
        self.next_node = None
        
        self.speed = config.ROBOT_BASE_SPEED
        
        self.state = RobotState.IDLE
        self.color = config.COLOR_ROBOT_IDLE
        self.path = []
        self.has_package = False
        self.is_blocked = False
        self.was_blocked = False
        
        # simulated time to load/unload a package
        self.loading_timer = 0
        self.loading_duration = config.TICK_RATE * 1  # 1 second
        
        # Trailing path for visual aesthetics
        self.trail = []

    def set_path(self, path, is_fetching=True):
        """Assigns a new path to follow"""
        self.path = path
        if len(self.path) > 0:
            self.state = RobotState.MOVING
            self.next_node = self.path.pop(0)
            self.color = config.COLOR_ROBOT_FETCH if is_fetching else config.COLOR_ROBOT_CARRY

    def update(self):
        """Tick function applied per frame to update position and state"""
        if self.state == RobotState.IDLE:
            return
            
        elif self.state == RobotState.LOADING:
            self.loading_timer -= 1
            if self.loading_timer <= 0:
                self.has_package = True
                self.state = RobotState.IDLE
                self.color = config.COLOR_ROBOT_CARRY
            return
            
        elif self.state == RobotState.MOVING:
            if self.is_blocked:
                # Fleet manager requested agent to wait to avoid collision
                return
                
            if self.next_node is None:
                return
                
            # Move towards next_node continuously
            target_pos = np.array([float(self.next_node[0]), float(self.next_node[1]), 0.0])
            direction = target_pos - self.pos
            distance = np.linalg.norm(direction)
            
            # Use dynamic speed instead of static global speed
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
                    if not self.has_package:
                        if self.grid_pos == config.UNLOADING_ZONE_OUT:
                            # Reached exit of unloading zone
                            self.state = RobotState.IDLE
                            self.color = config.COLOR_ROBOT_IDLE
                        else:
                            # Reached shelf
                            self.state = RobotState.LOADING
                            self.loading_timer = self.loading_duration
                    else:
                        # Reached unloading zone
                        self.has_package = False
                        self.state = RobotState.IDLE
                        self.color = config.COLOR_ROBOT_IDLE
            else:
                # Intermediate step
                self.pos += (direction / distance) * speed_per_tick
