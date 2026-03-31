import random
import networkx as nx
from robot_agent import RobotAgent, RobotState
from order_manager import OrderManager
import config

class FleetManager:
    def __init__(self, warehouse_map):
        self.warehouse_map = warehouse_map
        self.order_manager = OrderManager(warehouse_map)
        self.robots = []
        self.delivered_count = 0
        self.conflicts_avoided = 0
        self.auto_mode = True
        self.active_limit = config.NUM_ROBOTS
        
        for i in range(min(config.NUM_ROBOTS, len(config.CHARGING_STATIONS))):
            station_pos = config.CHARGING_STATIONS[i]
            r = RobotAgent(i, station_pos)
            r.state = RobotState.CHARGING
            self.robots.append(r)

    def get_path(self, robot, target_node, use_peripheral_weight=False):
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
            target_y = config.GRID_HEIGHT - 2
            max_x = config.GRID_WIDTH - 1
            if (u[0] == 0 or u[0] == max_x or u[1] == 0 or u[1] == target_y) and \
               (v[0] == 0 or v[0] == max_x or v[1] == 0 or v[1] == target_y):
                return 1
            return 5
            
        weight_func = return_weight if use_peripheral_weight else None
        
        try:
            path = nx.astar_path(view, robot.grid_pos, target_node, 
                                 heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]),
                                 weight=weight_func)
            return path
        except nx.NetworkXNoPath:
            try:
                path = nx.astar_path(self.warehouse_map.graph, robot.grid_pos, target_node, 
                                     heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]),
                                     weight=weight_func)
                return path
            except nx.NetworkXNoPath:
                return None

    def assign_missions(self):
        pending_tasks = self.order_manager.get_pending_tasks()
        
        if getattr(self, 'auto_mode', True):
            required_robots = min(config.NUM_ROBOTS, (len(pending_tasks) + 1) // 2)
            # Ensure at least 1 robot is active if there are tasks, 0 if none
            self.active_limit = required_robots if pending_tasks else 0
        
        for i, robot in enumerate(self.robots):
            is_allowed_to_work = i < getattr(self, 'active_limit', config.NUM_ROBOTS)
            
            if robot.state == RobotState.IDLE:
                
                # Check low battery or forced rest
                needs_charge = robot.battery_level < config.BATTERY_THRESHOLD
                should_rest = needs_charge or not is_allowed_to_work
                
                if should_rest and not robot.inventory and not robot.assigned_tasks:
                    if robot.grid_pos != robot.charging_station_pos:
                        path = self.get_path(robot, robot.charging_station_pos, use_peripheral_weight=True)
                        if path and len(path) > 0:
                            if path[0] == robot.grid_pos: path.pop(0)
                            if len(path) > 0:
                                robot.set_path(path, state=RobotState.RETURNING)
                                robot.speed = config.ROBOT_MAX_SPEED
                    elif needs_charge:
                        robot.state = RobotState.CHARGING
                    continue

                if robot.grid_pos == config.UNLOADING_ZONE_IN:
                    # Unload all inventory
                    if robot.inventory:
                        for item in robot.inventory:
                            item.delivered = True
                        robot.inventory.clear()
                        robot.current_weight = 0
                    
                    path = self.get_path(robot, config.UNLOADING_ZONE_OUT)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.MOVING)
                            robot.speed = config.ROBOT_MAX_SPEED
                    continue
                    
                if robot.assigned_tasks:
                    task = robot.assigned_tasks[0]
                    adj_nodes = self.warehouse_map.get_adjacent_navigable_nodes(task.shelf_pos)
                    
                    if robot.grid_pos in adj_nodes:
                        robot.state = RobotState.LOADING
                        robot.loading_timer = robot.loading_duration
                    else:
                        target_node = random.choice(adj_nodes) if adj_nodes else None
                        if target_node:
                            path = self.get_path(robot, target_node)
                            if path and len(path) > 0:
                                if path[0] == robot.grid_pos: path.pop(0)
                                if len(path) > 0:
                                    robot.set_path(path, state=RobotState.MOVING)
                                    robot.speed = config.ROBOT_BASE_SPEED
                    continue
                    
                if robot.inventory and not robot.assigned_tasks:
                    path = self.get_path(robot, config.UNLOADING_ZONE_IN)
                    if path and len(path) > 0:
                        if path[0] == robot.grid_pos: path.pop(0)
                        if len(path) > 0:
                            robot.set_path(path, state=RobotState.MOVING)
                            robot.speed = config.ROBOT_MAX_SPEED
                    continue

                if pending_tasks and not robot.assigned_tasks and not robot.inventory:
                    available_cap = config.ROBOT_MAX_CAPACITY
                    for task in list(pending_tasks):
                        if task.weight <= available_cap:
                            robot.assigned_tasks.append(task)
                            pending_tasks.remove(task)
                            available_cap -= task.weight
                    
                    if robot.assigned_tasks:
                        task = robot.assigned_tasks[0]
                        adj_nodes = self.warehouse_map.get_adjacent_navigable_nodes(task.shelf_pos)
                        if adj_nodes:
                            path = self.get_path(robot, random.choice(adj_nodes))
                            if path and len(path) > 0:
                                if path[0] == robot.grid_pos: path.pop(0)
                                if len(path) > 0:
                                    robot.set_path(path, state=RobotState.MOVING)
                                    robot.speed = config.ROBOT_BASE_SPEED

    def resolve_conflicts(self):
        for r in self.robots:
            r.was_blocked = r.is_blocked
            r.is_blocked = False
            
        for r1 in self.robots:
            if r1.state not in (RobotState.MOVING, RobotState.RETURNING) or not r1.next_node:
                continue
            needs_to_wait = False
            for r2 in self.robots:
                if r1.robot_id == r2.robot_id: continue
                if r1.next_node == r2.grid_pos:
                    needs_to_wait = True
                    if r2.state in (RobotState.MOVING, RobotState.RETURNING) and r2.next_node == r1.grid_pos:
                        if r1.robot_id > r2.robot_id:
                            r1.state = RobotState.IDLE
                            r1.next_node = None
                            if not r1.was_blocked:
                                self.conflicts_avoided += 1
                            needs_to_wait = False
                            break
                elif r2.state in (RobotState.MOVING, RobotState.RETURNING) and r1.next_node == r2.next_node:
                    if r1.robot_id > r2.robot_id:
                        needs_to_wait = True
                        
            if needs_to_wait and r1.state in (RobotState.MOVING, RobotState.RETURNING):
                r1.is_blocked = True
                if not r1.was_blocked:
                    self.conflicts_avoided += 1

    def update(self):
        self.order_manager.update()
        self.assign_missions()
        self.resolve_conflicts()
        for robot in self.robots:
            robot.update()
