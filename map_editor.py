import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel, 
                             QMessageBox, QFileDialog, QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt
import config
from map_validator import MapValidator

class MapEditor(QMainWindow):
    def __init__(self, on_launch_callback):
        super().__init__()
        self.on_launch_callback = on_launch_callback
        self.setWindowTitle("Warehouse Map Builder")
        self.setFixedSize(800, 700)
        
        self.grid_width = config.GRID_WIDTH
        self.grid_height = config.GRID_HEIGHT
        
        self.current_tool = 'floor' # floor, shelf_L, shelf_M, shelf_H, charger, drop_in, drop_out
        
        self.cells = {} # (x, y) -> {'type': str, 'category': str, 'button': QPushButton}
        
        self.init_ui()
        self.init_grid()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Tools panel (Left)
        tools_panel = QWidget()
        tools_layout = QVBoxLayout()
        tools_panel.setLayout(tools_layout)
        
        tools_layout.addWidget(QLabel("<b>Outils Outils</b>"))
        
        self.tool_group = QButtonGroup()
        
        def add_tool(name, tool_id, checked=False):
            btn = QRadioButton(name)
            btn.toggled.connect(lambda state, t=tool_id: self.set_tool(t) if state else None)
            if checked:
                btn.setChecked(True)
                self.current_tool = tool_id
            tools_layout.addWidget(btn)
            self.tool_group.addButton(btn)

        add_tool("🧹 Sol (Effacer)", "floor", True)
        add_tool("📦 Étagère (Léger)", "shelf_L")
        add_tool("📦 Étagère (Moyen)", "shelf_M")
        add_tool("📦 Étagère (Lourd)", "shelf_H")
        add_tool("🔋 Station Recharge", "charger")
        add_tool("📥 Quai de Dépot IN", "drop_in")
        add_tool("📤 Quai de Dépot OUT", "drop_out")
        
        tools_layout.addSpacing(20)
        
        btn_save = QPushButton("💾 Sauvegarder (JSON)")
        btn_save.clicked.connect(self.save_map)
        tools_layout.addWidget(btn_save)
        
        btn_load = QPushButton("📁 Charger (JSON)")
        btn_load.clicked.connect(self.load_map)
        tools_layout.addWidget(btn_load)
        
        tools_layout.addStretch()
        
        btn_launch = QPushButton("🚀 Valider & Lancer")
        btn_launch.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 10px;")
        btn_launch.clicked.connect(self.validate_and_launch)
        tools_layout.addWidget(btn_launch)
        
        # Grid panel (Right)
        grid_panel = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        grid_panel.setLayout(self.grid_layout)
        
        main_layout.addWidget(tools_panel, 1)
        main_layout.addWidget(grid_panel, 4)
        
    def init_grid(self):
        # Initial empty map array or layout cells
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                btn = QPushButton()
                btn.setFixedSize(25, 25)
                # Reverse y visually so (0,0) is bottom-left matching PyVista?
                # PyVista visualizer uses math coordinates. Let's keep 0,0 at bottom-left in UI too.
                # QGridLayout puts row 0 at top. So row = grid_height - 1 - y
                row = self.grid_height - 1 - y
                col = x
                self.grid_layout.addWidget(btn, row, col)
                
                # Pass coords properly through closure
                btn.clicked.connect(lambda checked, cx=x, cy=y: self.cell_clicked(cx, cy))
                
                self.cells[(x, y)] = {
                    'type': 'floor',
                    'category': None,
                    'button': btn
                }
                self.update_btn_style(x, y)
                
    def set_tool(self, tool_id):
        self.current_tool = tool_id
        
    def cell_clicked(self, x, y):
        cell = self.cells[(x, y)]
        if self.current_tool == 'floor':
            cell['type'] = 'floor'
            cell['category'] = None
        elif self.current_tool.startswith('shelf_'):
            cell['type'] = 'shelf'
            if self.current_tool == 'shelf_L': cell['category'] = config.CATEGORY_LIGHT
            elif self.current_tool == 'shelf_M': cell['category'] = config.CATEGORY_MEDIUM
            elif self.current_tool == 'shelf_H': cell['category'] = config.CATEGORY_HEAVY
        else:
            cell['type'] = self.current_tool
            cell['category'] = None
            
        self.update_btn_style(x, y)
        
    def update_btn_style(self, x, y):
        cell = self.cells[(x, y)]
        btn = cell['button']
        
        style = "border: 1px solid #ccc; "
        text = ""
        
        type_ = cell['type']
        if type_ == 'floor':
            style += "background-color: #E0E0E0;"
        elif type_ == 'shelf':
            style += "background-color: #505050; color: white; font-size: 10px;"
            cat = cell['category']
            if cat == config.CATEGORY_LIGHT: text = "L"
            elif cat == config.CATEGORY_MEDIUM: text = "M"
            elif cat == config.CATEGORY_HEAVY: text = "H"
        elif type_ == 'charger':
            style += f"background-color: {config.COLOR_CHARGING_PAD};"
        elif type_ == 'drop_in':
            style += f"background-color: {config.COLOR_UNLOAD_IN}; color: white;"
            text = "↓"
        elif type_ == 'drop_out':
            style += f"background-color: {config.COLOR_UNLOAD_OUT}; color: white;"
            text = "↑"
            
        btn.setStyleSheet(style)
        btn.setText(text)
        
    def get_map_data(self):
        data = []
        for (x, y), cell in self.cells.items():
            if cell['type'] != 'floor':
                data.append({
                    'pos': [x, y],
                    'type': cell['type'],
                    'category': cell['category']
                })
        return data
        
    def save_map(self):
        data = self.get_map_data()
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la Carte JSON", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'w') as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Succès", "Carte sauvegardée !")
            
    def load_map(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Charger une Carte JSON", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    data = json.load(f)
                    
                # Reset map
                for pos, cell in self.cells.items():
                    cell['type'] = 'floor'
                    cell['category'] = None
                    self.update_btn_style(pos[0], pos[1])
                    
                # Apply data
                for item in data:
                    x, y = item['pos']
                    if (x, y) in self.cells:
                        self.cells[(x, y)]['type'] = item['type']
                        self.cells[(x, y)]['category'] = item.get('category')
                        self.update_btn_style(x, y)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de lecture: {e}")
                
    def validate_and_launch(self):
        data = self.get_map_data()
        is_valid, error_msg, parsed_config = MapValidator.validate(data, self.grid_width, self.grid_height)
        
        if not is_valid:
            QMessageBox.warning(self, "Erreur de Validation", error_msg)
            return
            
        # Call the callback with the validated map components
        self.on_launch_callback(parsed_config)
        self.close()
