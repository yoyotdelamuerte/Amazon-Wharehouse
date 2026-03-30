from warehouse_map import WarehouseMap
from fleet_manager import FleetManager
from visualizer import WarehouseVisualizer
import config

def main():
    print("========================================")
    print("  3D Automated Warehouse Simulation")
    print("========================================")
    
    print("\n[1/3] Creating Navigation Map...")
    wm = WarehouseMap()
    
    print(f"[2/3] Deploying Fleet of {config.NUM_ROBOTS} Robots...")
    fm = FleetManager(wm)
    
    print("[3/3] Setting up PyVista 3D Environment...")
    viz = WarehouseVisualizer(wm, fm)
    
    # Define the tick function synced with PyVista's event loop
    def simulation_tick(step):
        # 1. Update Game/Sim Logic
        fm.update()
        # 2. Sync visual actors with agent state
        viz.render_frame()
        
    delay = int(1000 / config.TICK_RATE)
    
    # Register the tick loop. (max_steps ensures it runs practically forever until window closed)
    viz.plotter.add_timer_event(max_steps=10000000, duration=delay, callback=simulation_tick)
    
    print("\n✅ Simulation Ready! Starting main loop.")
    print("Close the 3D window to exit the application.")
    
    viz.plotter.show()

if __name__ == "__main__":
    main()
