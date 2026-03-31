import pyvista as pv
import numpy as np
import config

class WarehouseVisualizer:
    """
    Renders the warehouse 3D environment using PyVista.
    Updates the meshes corresponding to agents dynamically.
    """
    def __init__(self, warehouse_map, fleet_manager, plotter):
        self.wm = warehouse_map
        self.fm = fleet_manager
        
        pv.set_plot_theme(config.THEME)
        self.plotter = plotter
        
        self.robot_actors = []
        self.trail_actors = [None] * config.NUM_ROBOTS
        
        self.setup_scene()
        
    def setup_scene(self):
        # 1. Ground Grid Plane
        ground = pv.Plane(
            center=(self.wm.width/2 - 0.5, self.wm.height/2 - 0.5, -0.1), 
            direction=(0, 0, 1), 
            i_size=self.wm.width, 
            j_size=self.wm.height, 
            i_resolution=self.wm.width, 
            j_resolution=self.wm.height
        )
        self.plotter.add_mesh(ground, color=config.COLOR_GROUND, show_edges=True, edge_color=config.COLOR_GROUND_EDGE)
        
        # 2. Unloading Zones
        unload_in = pv.Cube(
            center=(config.UNLOADING_ZONE_IN[0], config.UNLOADING_ZONE_IN[1], -0.05), 
            x_length=1.0, y_length=1.0, z_length=0.1
        )
        self.plotter.add_mesh(unload_in, color=config.COLOR_UNLOAD_IN) # Red for Drop-off IN
        
        unload_out = pv.Cube(
            center=(config.UNLOADING_ZONE_OUT[0], config.UNLOADING_ZONE_OUT[1], -0.05), 
            x_length=1.0, y_length=1.0, z_length=0.1
        )
        self.plotter.add_mesh(unload_out, color=config.COLOR_UNLOAD_OUT) # Light blue for Exit OUT

        # 2.5 Charging Stations
        charge_pad_mesh = pv.Cube(
            center=(0, 0, -0.05), 
            x_length=1.0, y_length=1.0, z_length=0.1
        )
        for pad_pos in config.CHARGING_STATIONS:
            moved_pad = charge_pad_mesh.copy()
            moved_pad.translate((pad_pos[0], pad_pos[1], 0), inplace=True)
            self.plotter.add_mesh(moved_pad, color=config.COLOR_CHARGING_PAD)

        # 3. Static Shelves
        shelf_mesh = pv.Cube(center=(0, 0, config.SHELF_SIZE/2), x_length=config.SHELF_SIZE, y_length=config.SHELF_SIZE, z_length=config.SHELF_SIZE)
        for shelf_pos in self.wm.shelves:
            moved_shelf = shelf_mesh.copy()
            moved_shelf.translate((shelf_pos[0], shelf_pos[1], 0), inplace=True)
            
            cat = self.wm.shelf_categories.get(shelf_pos, config.CATEGORY_LIGHT)
            shelf_color = config.COLOR_SHELF
            if cat == config.CATEGORY_LIGHT: shelf_color = '#A5D6A7' # Light Green
            elif cat == config.CATEGORY_MEDIUM: shelf_color = '#FFCC80' # Orange
            elif cat == config.CATEGORY_HEAVY: shelf_color = '#B0BEC5' # Heavy metal
            
            self.plotter.add_mesh(
                moved_shelf, 
                color=shelf_color, 
                opacity=config.ALPHA_SHELF,
                show_edges=True
            )
            
        # 4. Robots
        main_body = pv.Cube(center=(0, 0, config.ROBOT_SIZE/2), x_length=config.ROBOT_SIZE, y_length=config.ROBOT_SIZE, z_length=config.ROBOT_SIZE)
        nose_size = config.ROBOT_SIZE * 0.4
        nose = pv.Cube(center=(config.ROBOT_SIZE/2 + nose_size/2, 0, config.ROBOT_SIZE/2), 
                       x_length=nose_size, y_length=nose_size, z_length=config.ROBOT_SIZE*0.8)
        robot_proto = main_body + nose
        
        for robot in self.fm.robots:
            actor = self.plotter.add_mesh(robot_proto.copy(), color=robot.color)
            actor.position = (robot.pos[0], robot.pos[1], 0)
            self.robot_actors.append(actor)
            
        # 5. UI Overlays (Removed since we have Qt dash windows now)
        self.plotter.view_xy()
        self.plotter.enable_parallel_projection()
        self.plotter.enable_2d_style()
        
    def render_frame(self):
        """Called every tick to update the visuals."""
        for i, robot in enumerate(self.fm.robots):
            # Update robot translation, rotation and active color state
            actor = self.robot_actors[i]
            actor.position = (robot.pos[0], robot.pos[1], 0)
            actor.orientation = (0, 0, robot.facing_angle)
            actor.prop.color = pv.Color(robot.color)
            
            # Update physical trail
            if len(robot.trail) > 1:
                points = np.array(robot.trail)
                points[:, 2] = 0.05  # Render slightly above ground ground to avoid z-fighting
                try:
                    line_data = pv.lines_from_points(points)
                    
                    if self.trail_actors[i] is not None:
                        self.plotter.remove_actor(self.trail_actors[i])
                        
                    self.trail_actors[i] = self.plotter.add_mesh(line_data, color=config.COLOR_TRAIL, line_width=2)
                except ValueError:
                    pass
                
        # We rely on Qt QTimer instead of PyVista timer loop.
