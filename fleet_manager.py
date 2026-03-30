import random
import networkx as nx
from robot_agent import RobotAgent, RobotState
import config

class FleetManager:
    """
    Coordinates pathing for the entire robot fleet.
    Avoids collisions by assigning reservations and dynamically holding robots on ticks.
    """
    def __init__(self, warehouse_map):
        self.warehouse_map = warehouse_map
        self.robots = []
        self.delivered_count = 0
        self.conflicts_avoided = 0
        
        # Init robots at their designated charging stations
        for i in range(min(config.NUM_ROBOTS, len(config.CHARGING_STATIONS))):
            station_pos = config.CHARGING_STATIONS[i]
            # Immediately set them to start charging or idle at their station
            r = RobotAgent(i, station_pos)
            r.state = RobotState.CHARGING # Let them top up initially just in case
            self.robots.append(r)

    def get_path(self, robot, target_node, use_peripheral_weight=False):
        """
        Gets A* shortest path avoiding nodes currently occupied by other robots.
        Falls back to base graph if completely trapped.
        """
        occupied = set()
        for r in self.robots:
            if r.robot_id != robot.robot_id:
                occupied.add(r.grid_pos)
                if r.next_node:
                    occupied.add(r.next_node)
                    
        def valid_node(n):
            return n not in occupied or n == target_node or n == robot.grid_pos
            
        view = nx.subgraph_view(self.warehouse_map.graph, filter_node=valid_node)
        
        def return_weight(u, v, d):
            # Peripheral highway definition
            target_y = config.GRID_HEIGHT - 2 # y=18
            max_x = config.GRID_WIDTH - 1     # x=19
            # If both nodes of the edge are on the perimeter, weight is 1. Otherwise 5.
            if (u[0] == 0 or u[0] == max_x or u[1] == 0 or u[1] == target_y) and \
               (v[0] == 0 or v[0] == max_x or v[1] == 0 or v[1] == target_y):
                return 1
            return 5
            
        weight_func = return_weight if use_peripheral_weight else None
        
        # Try finding path around other moving agents
        try:
            path = nx.astar_path(
                view, 
                robot.grid_pos, 
                target_node, 
                heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]),
                weight=weight_func
            )
            return path
        except nx.NetworkXNoPath:
            # Fallback to the regular graph to prevent an agent stuck in IDLE state forever
            try:
                path = nx.astar_path(
                    self.warehouse_map.graph, 
                    robot.grid_pos, 
                    target_node, 
                    heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]),
                    weight=weight_func
                )
                return path
            except nx.NetworkXNoPath:
                return None

    def assign_missions(self):
        """Assign goals (shelf or unloading) to idle robots."""
        for robot in self.robots:
            if robot.state == RobotState.IDLE:
                
                # Priority 1: Check if battery is low and we're not carrying a package
                if robot.battery_level < config.BATTERY_THRESHOLD and not robot.has_package:
                    # Low battery logic: return to specific charging station via perimeter
                    path = self.get_path(robot, robot.charging_station_pos, use_peripheral_weight=True)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.RETURNING)
                            robot.speed = config.ROBOT_MAX_SPEED
                    continue

                if robot.has_package:
                    # Returning package to unloading zone IN
                    path = self.get_path(robot, config.UNLOADING_ZONE_IN)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.MOVING)
                            robot.speed = config.ROBOT_MAX_SPEED
                elif robot.grid_pos == config.UNLOADING_ZONE_IN:
                    # Move out of the unloading zone
                    path = self.get_path(robot, config.UNLOADING_ZONE_OUT)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.MOVING)
                            robot.speed = config.ROBOT_MAX_SPEED
                else:
                    # Going to get a package from a shelf
                    target_shelf = self.warehouse_map.get_random_shelf()
                    if not target_shelf: continue
                    adj_nodes = self.warehouse_map.get_adjacent_navigable_nodes(target_shelf)
                    if not adj_nodes: continue
                    
                    target_node = random.choice(adj_nodes)
                    path = self.get_path(robot, target_node)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.MOVING)
                            robot.speed = config.ROBOT_BASE_SPEED
                            
    def resolve_conflicts(self):
        """Checks for immediate 1-tick collisions and blocks agents to avoid overlaps."""
        # Reset block flags for the frame
        for r in self.robots:
            r.was_blocked = r.is_blocked
            r.is_blocked = False
            
        for r1 in self.robots:
            if r1.state not in (RobotState.MOVING, RobotState.RETURNING) or not r1.next_node:
                continue
                
            needs_to_wait = False
            
            for r2 in self.robots:
                if r1.robot_id == r2.robot_id: continue
                
                # Check 1: r1 wants to enter a cell r2 is currently occupying
                if r1.next_node == r2.grid_pos:
                    needs_to_wait = True
                    
                    # Special Case: Head-on collision
                    if r2.state in (RobotState.MOVING, RobotState.RETURNING) and r2.next_node == r1.grid_pos:
                        # Deadlock resolution: Priority rule
                        if r1.robot_id > r2.robot_id:
                            # r1 abandons its path entirely to step out of the way on the next tick
                            # Revert to IDLE to recalculate path next frame
                            prev_state = r1.state
                            r1.state = RobotState.IDLE
                            r1.next_node = None
                            
                            if not r1.was_blocked:
                                self.conflicts_avoided += 1
                            needs_to_wait = False # Handled by abandoning path
                            break
                            
                # Check 2: Both robots heading to exactly the same empty cell concurrently
                elif r2.state in (RobotState.MOVING, RobotState.RETURNING) and r1.next_node == r2.next_node:
                    if r1.robot_id > r2.robot_id:
                        needs_to_wait = True
                        
            # Apply block
            if needs_to_wait and r1.state in (RobotState.MOVING, RobotState.RETURNING):
                r1.is_blocked = True
                if not r1.was_blocked:
                    self.conflicts_avoided += 1

    def update(self):
        """Main dispatcher update matching simulation tick rate."""
        self.assign_missions()
        self.resolve_conflicts()
        
        for robot in self.robots:
            # Track delivery status edge case
            was_carrying = robot.has_package and robot.state in (RobotState.MOVING, RobotState.RETURNING)
            
            robot.update()
            
            if was_carrying and not robot.has_package and robot.state == RobotState.IDLE:
                # Successfully arrived at unloading zone this frame
                self.delivered_count += 1
