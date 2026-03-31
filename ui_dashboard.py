from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView
from pyvistaqt import QtInteractor
import pyvista as pv
import config

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warehouse 3D Map")
        self.resize(800, 600)
        
        self.frame = QWidget()
        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(0,0,0,0)
        
        # Instantiate the PyVista Qt Widget
        self.plotter = QtInteractor(self.frame)
        self.vlayout.addWidget(self.plotter.interactor)
        
        self.frame.setLayout(self.vlayout)
        self.setCentralWidget(self.frame)

class StatsWindow(QMainWindow):
    def __init__(self, fleet_manager):
        super().__init__()
        self.fm = fleet_manager
        self.setWindowTitle("Warehouse Global Stats")
        self.resize(300, 420)
        
        self.label_orders = QLabel("Orders Completed: 0")
        self.label_late = QLabel("Late Orders: 0")
        self.label_conflicts = QLabel("Conflicts Avoided: 0")
        
        # Set large bold font for the main metrics
        font = self.label_orders.font()
        font.setPointSize(16)
        font.setBold(True)
        self.label_orders.setFont(font)
        self.label_late.setFont(font)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label_orders)
        layout.addWidget(self.label_late)
        layout.addWidget(self.label_conflicts)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("<b>Robot Fleet Status</b>"))
        
        self.robot_labels = []
        for r in self.fm.robots:
            lbl = QLabel(f"Robot {r.robot_id}: Idle")
            layout.addWidget(lbl)
            self.robot_labels.append(lbl)
            
        layout.addStretch()
            
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def update_stats(self):
        self.label_orders.setText(f"Orders Completed: {self.fm.order_manager.completed_count}")
        self.label_late.setText(f"Late Orders: {self.fm.order_manager.late_count}")
        self.label_conflicts.setText(f"Conflicts Avoided: {self.fm.conflicts_avoided}")
        for i, r in enumerate(self.fm.robots):
            state_str = "Idle"
            if r.state == 1: state_str = "Moving"
            elif r.state == 2: state_str = "Loading"
            elif r.state == 3: state_str = "Charging"
            elif r.state == 4: state_str = "Returning"
            self.robot_labels[i].setText(f"Robot {r.robot_id}: {state_str} | Load: {r.current_weight}/{config.ROBOT_MAX_CAPACITY} | Batt: {int(r.battery_level)}%")

class OrdersWindow(QMainWindow):
    def __init__(self, order_manager):
        super().__init__()
        self.om = order_manager
        self.setWindowTitle("Order Queue & Logistics")
        self.resize(550, 420)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Order ID", "Priority", "Weight", "Progress", "Timer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Active Orders Queue</b>"))
        layout.addWidget(self.table)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def update_orders(self):
        # Update table rows dynamically
        self.table.setRowCount(len(self.om.active_orders))
        for i, o in enumerate(self.om.active_orders):
            self.table.setItem(i, 0, QTableWidgetItem(f"#{o.order_id}"))
            self.table.setItem(i, 1, QTableWidgetItem(str(o.priority)))
            self.table.setItem(i, 2, QTableWidgetItem(str(o.total_weight)))
            
            picked = sum(1 for item in o.items if item.picked_up)
            self.table.setItem(i, 3, QTableWidgetItem(f"{picked}/{len(o.items)}"))
            
            timer_item = QTableWidgetItem(f"{o.deadline_timer}")
            if o.is_late:
                timer_item.setText("LATE")
                # Red text for late orders
                # timer_item.setForeground(QColor(255, 0, 0)) - Optional
            self.table.setItem(i, 4, timer_item)
