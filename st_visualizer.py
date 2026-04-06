import math
import config

def generate_warehouse_svg(wm, fm, width=600, height=600):
    """
    Generates a highly-performant SVG string representing the 2D state of the warehouse.
    """
    gw = config.GRID_WIDTH
    gh = config.GRID_HEIGHT
    
    cell_w = width / gw
    cell_h = height / gh
    
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background-color: {config.COLOR_GROUND}; border: 1px solid {config.COLOR_GROUND_EDGE}; border-radius: 8px;">']
    
    # 1. Grid lines (Optional, but looks nice)
    for x in range(1, gw):
        px = x * cell_w
        svg.append(f'<line x1="{px}" y1="0" x2="{px}" y2="{height}" stroke-width="1" stroke="{config.COLOR_GROUND_EDGE}" opacity="0.3"/>')
    for y in range(1, gh):
        py = y * cell_h
        svg.append(f'<line x1="0" y1="{py}" x2="{width}" y2="{py}" stroke-width="1" stroke="{config.COLOR_GROUND_EDGE}" opacity="0.3"/>')
        
    def to_svg_coord(gx, gy):
        # SVG coordinates: 0,0 is top-left.
        # But in PyVista 0,0 was also effectively bottom-left or whatever. 
        # In map editor, 0,0 was bottom-left. Let's invert Y so 0,0 is bottom-left for consistency with old behavior.
        sx = gx * cell_w
        sy = height - (gy + 1) * cell_h
        return sx, sy
        
    def to_svg_center(gx, gy):
        sx, sy = to_svg_coord(gx, gy)
        return sx + cell_w/2, sy + cell_h/2

    # 2. Charging Zones
    for cx, cy in config.MAP_CHARGERS:
        sx, sy = to_svg_coord(cx, cy)
        svg.append(f'<rect x="{sx}" y="{sy}" width="{cell_w}" height="{cell_h}" fill="{config.COLOR_CHARGING_PAD}" opacity="0.6"/>')
        svg.append(f'<text x="{sx + cell_w/2}" y="{sy + cell_h/2}" fill="white" font-size="{cell_h*0.5}" text-anchor="middle" dominant-baseline="central">⚡</text>')

    # 3. Drop Zones
    for drop in config.MAP_DROPS:
        inx, iny = drop['in']
        outx, outy = drop['out']
        s_inx, s_iny = to_svg_coord(inx, iny)
        s_outx, s_outy = to_svg_coord(outx, outy)
        svg.append(f'<rect x="{s_inx}" y="{s_iny}" width="{cell_w}" height="{cell_h}" fill="{config.COLOR_UNLOAD_IN}" opacity="0.8"/>')
        svg.append(f'<text x="{s_inx + cell_w/2}" y="{s_iny + cell_h/2}" fill="white" font-size="{cell_h*0.5}" text-anchor="middle" dominant-baseline="central">IN</text>')
        
        svg.append(f'<rect x="{s_outx}" y="{s_outy}" width="{cell_w}" height="{cell_h}" fill="{config.COLOR_UNLOAD_OUT}" opacity="0.8"/>')
        svg.append(f'<text x="{s_outx + cell_w/2}" y="{s_outy + cell_h/2}" fill="white" font-size="{cell_h*0.5}" text-anchor="middle" dominant-baseline="central">OUT</text>')

    # 4. Shelves
    for (sx, sy) in wm.shelves:
        vx, vy = to_svg_coord(sx, sy)
        cat = wm.shelf_categories.get((sx, sy), config.CATEGORY_LIGHT)
        shelf_color = config.COLOR_SHELF
        text = ""
        if cat == config.CATEGORY_LIGHT: 
            shelf_color = '#A5D6A7'
            text = "L"
        elif cat == config.CATEGORY_MEDIUM: 
            shelf_color = '#FFCC80'
            text = "M"
        elif cat == config.CATEGORY_HEAVY: 
            shelf_color = '#B0BEC5'
            text = "H"
            
        svg.append(f'<rect x="{vx+2}" y="{vy+2}" width="{cell_w-4}" height="{cell_h-4}" fill="{shelf_color}" rx="4"/>')
        svg.append(f'<text x="{vx + cell_w/2}" y="{vy + cell_h/2}" fill="#333" font-size="{cell_h*0.5}" font-weight="bold" text-anchor="middle" dominant-baseline="central">{text}</text>')

    # 5. Trails
    for robot in fm.robots:
        if len(robot.trail) > 1:
            points_str = []
            for point in robot.trail:
                tx, ty = float(point[0]), float(point[1])  # trail stores 3D numpy arrays [x, y, z]
                cx, cy = to_svg_center(tx, ty)
                points_str.append(f"{cx},{cy}")
            svg.append(f'<polyline points="{" ".join(points_str)}" fill="none" stroke="{robot.color}" stroke-width="2" stroke-dasharray="4,4" opacity="0.6" />')

    # 6. Robots
    r_radius = min(cell_w, cell_h) * 0.4
    for robot in fm.robots:
        rx, ry = to_svg_center(robot.pos[0], robot.pos[1])
        
        # Robot body
        svg.append(f'<circle cx="{rx}" cy="{ry}" r="{r_radius}" fill="{robot.color}" stroke="#333" stroke-width="2"/>')
        
        # Robot ID
        svg.append(f'<text x="{rx}" y="{ry}" fill="white" font-size="{r_radius}" font-weight="bold" text-anchor="middle" dominant-baseline="central">{robot.robot_id}</text>')
        
        # Direction indicator (nose)
        # facing_angle is usually in degrees. Let's make sure. PyVista roll/pitch/yaw is in degrees usually.
        # But wait, looking at python math: math.cos takes radians.
        # Let's check fleet_manager.py or robot_agent.py to see how `facing_angle` is calculated. It actually used degrees `math.degrees(math.atan2(dy, dx))`
        import math as m
        rad = m.radians(robot.facing_angle)
        # Because we inverted Y axis for rendering (SVG Y goes down, Grid Y goes up), we need to invert the angle's sin part
        nx = rx + (r_radius * 1.5) * m.cos(rad)
        ny = ry - (r_radius * 1.5) * m.sin(rad) # Minus because SVG Y grows downwards
        
        svg.append(f'<line x1="{rx}" y1="{ry}" x2="{nx}" y2="{ny}" stroke="#333" stroke-width="3" stroke-linecap="round"/>')
        svg.append(f'<circle cx="{nx}" cy="{ny}" r="{r_radius*0.3}" fill="black"/>')

    svg.append('</svg>')
    
    return "".join(svg)
