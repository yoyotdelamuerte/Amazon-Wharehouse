import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from map_editor import MapEditor
from warehouse_map import WarehouseMap
from fleet_manager import FleetManager
from visualizer import WarehouseVisualizer
from ui_dashboard import MapWindow, StatsWindow, OrdersWindow, ControlWindow
import config

# Global variables to prevent garbage collection of dashboard windows and timer
dashboard_windows = []
timer = None

def launch_simulation(parsed_config):
    global dashboard_windows, timer
    
    print("\n[✓] Map Validated. Starting Configuration...")
    # 1. Inject generated map data into the config singleton
    config.MAP_SHELVES = parsed_config['shelves']
    config.MAP_DROPS = parsed_config['drops']
    config.MAP_CHARGERS = parsed_config['chargers']
    config.NUM_ROBOTS = len(config.MAP_CHARGERS)
    
    print("[1/3] Generating Navigation Map & Shelves...")
    wm = WarehouseMap()
    
    print("[2/3] Deploying Fleet Manager & Orders...")
    fm = FleetManager(wm)
    
    print("[3/3] Booting UI Dashboard Modules...")
    
    # 1. Map View
    map_win = MapWindow()
    viz = WarehouseVisualizer(wm, fm, map_win.plotter)
    map_win.show()
    map_win.move(100, 100)
    
    # 2. Stats Dashboard
    stats_win = StatsWindow(fm)
    stats_win.show()
    stats_win.move(950, 100)
    
    # 3. Orders Queue
    orders_win = OrdersWindow(fm.order_manager)
    orders_win.show()
    orders_win.move(950, 560)
    
    # 4. Control Panel
    control_win = ControlWindow(fm)
    control_win.show()
    control_win.move(100, 750)
    
    dashboard_windows.extend([map_win, stats_win, orders_win, control_win])
    
    def simulation_tick():
        fm.update()
        viz.render_frame()
        stats_win.update_stats()
        orders_win.update_orders()
        control_win.update_controls()
        
    delay = int(1000 / config.TICK_RATE)
    
    timer = QTimer()
    timer.timeout.connect(simulation_tick)
    timer.start(delay)
    
    print("\n✅ Simulation Dashboard Online!")

def main():
    print("========================================")
    print("  3D Automated Warehouse Control Center ")
    print("========================================")
    
    app = QApplication(sys.argv)
    
    # Start the Map Editor first
    editor = MapEditor(on_launch_callback=launch_simulation)
    editor.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
