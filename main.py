import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from warehouse_map import WarehouseMap
from fleet_manager import FleetManager
from visualizer import WarehouseVisualizer
from ui_dashboard import MapWindow, StatsWindow, OrdersWindow, ControlWindow
import config

def main():
    print("========================================")
    print("  3D Automated Warehouse Control Center ")
    print("========================================")
    
    app = QApplication(sys.argv)
    
    print("\n[1/3] Generating Navigation Map & Shelves...")
    wm = WarehouseMap()
    
    print(f"[2/3] Deploying Fleet Manager & Orders...")
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
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
