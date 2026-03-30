import pyvista as pv
import numpy as np
import config

class WarehouseVisualizer:
    """
    Renders the warehouse 3D environment using PyVista.
    Updates the meshes corresponding to agents dynamically.
    """
    def __init__(self, warehouse_map, fleet_manager):
        self.wm = warehouse_map
        self.fm = fleet_manager
        
        pv.set_plot_theme(config.THEME)
        self.plotter = pv.Plotter()
        
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
        self.plotter.add_mesh(ground, color='#222222', show_edges=True, edge_color='#444444')
        
        # 2. Unloading Zones
        unload_in = pv.Cube(
            center=(config.UNLOADING_ZONE_IN[0], config.UNLOADING_ZONE_IN[1], -0.05), 
            x_length=1.0, y_length=1.0, z_length=0.1
        )
        self.plotter.add_mesh(unload_in, color='#ff0000') # Red for Drop-off IN
        
        unload_out = pv.Cube(
            center=(config.UNLOADING_ZONE_OUT[0], config.UNLOADING_ZONE_OUT[1], -0.05), 
            x_length=1.0, y_length=1.0, z_length=0.1
        )
        self.plotter.add_mesh(unload_out, color='#00aaff') # Light blue for Exit OUT

        # 3. Static Static Shelves
        shelf_mesh = pv.Cube(center=(0, 0, config.SHELF_SIZE/2), x_length=config.SHELF_SIZE, y_length=config.SHELF_SIZE, z_length=config.SHELF_SIZE)
        for shelf_pos in self.wm.shelves:
            moved_shelf = shelf_mesh.copy()
            moved_shelf.translate((shelf_pos[0], shelf_pos[1], 0), inplace=True)
            self.plotter.add_mesh(
                moved_shelf, 
                color=config.COLOR_SHELF, 
                opacity=config.ALPHA_SHELF,
                show_edges=True
            )
            
        # 4. Robots
        robot_proto = pv.Cube(center=(0, 0, config.ROBOT_SIZE/2), x_length=config.ROBOT_SIZE, y_length=config.ROBOT_SIZE, z_length=config.ROBOT_SIZE)
        for robot in self.fm.robots:
            actor = self.plotter.add_mesh(robot_proto.copy(), color=robot.color)
            actor.position = (robot.pos[0], robot.pos[1], 0)
            self.robot_actors.append(actor)
            
        # 5. UI Overlays
        self.text_actor = self.plotter.add_text(
            "Delivered: 0\nConflicts Avoided: 0", 
            position='upper_left', 
            color='white', 
            font_size=12
        )
            
        # 6. Default Camera Angle
        self.plotter.camera.position = (self.wm.width/2, -self.wm.height*0.2, self.wm.height*1.5)
        self.plotter.camera.focal_point = (self.wm.width/2, self.wm.height/2, 0)
        
    def render_frame(self):
        """Called every tick to update the visuals."""
        for i, robot in enumerate(self.fm.robots):
            # Update robot translation and active color state
            actor = self.robot_actors[i]
            actor.position = (robot.pos[0], robot.pos[1], 0)
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
                
        # Update metrics overlay
        self.plotter.remove_actor(self.text_actor)
        self.text_actor = self.plotter.add_text(
            f"Delivered: {self.fm.delivered_count}\nConflicts Avoided: {self.fm.conflicts_avoided}", 
            position='upper_left', 
            color='white', 
            font_size=12
        )
        
        # We don't need to call self.plotter.update() manually if using add_timer_event
