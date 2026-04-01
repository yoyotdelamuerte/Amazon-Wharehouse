import time
import config
from warehouse_map import WarehouseMap
from fleet_manager import FleetManager

def run_test():
    # Mock config data
    config.MAP_CHARGERS = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
    config.NUM_ROBOTS = len(config.MAP_CHARGERS)
    config.MAP_DROPS = [{'in': (19, 10), 'out': (19, 11)}]
    config.MAP_SHELVES = {
        (5, 5): config.CATEGORY_LIGHT, (5, 6): config.CATEGORY_MEDIUM, (5, 7): config.CATEGORY_HEAVY,
        (10, 5): config.CATEGORY_LIGHT, (10, 6): config.CATEGORY_MEDIUM, (10, 7): config.CATEGORY_HEAVY,
    }
    config.ORDER_SPAWN_CHANCE = 0.05 # Reasonable spawn rate
    
    wm = WarehouseMap()
    fm = FleetManager(wm)
    
    # Run the simulation for 3000 ticks
    ticks = 3000
    deadlocks_detected = 0
    
    # We will track blocked time for each robot
    blocked_time = {r.robot_id: 0 for r in fm.robots}
    
    for t in range(ticks):
        fm.update()
        
        # Check blocked states
        for r in fm.robots:
            if r.is_blocked:
                blocked_time[r.robot_id] += 1
            else:
                blocked_time[r.robot_id] = 0
                
            # If a robot is blocked for too long, it's a deadlock
            if blocked_time[r.robot_id] > 40:
                deadlocks_detected += 1
                # reset the tracker so we don't count the same deadlock every tick
                blocked_time[r.robot_id] = 0
                
    print(f"Test finished. Deadlocks detected: {deadlocks_detected}, Orders delivered: {fm.order_manager.completed_count}")

if __name__ == "__main__":
    run_test()
