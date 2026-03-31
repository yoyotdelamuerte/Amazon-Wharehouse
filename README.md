# 3D Automated Warehouse Simulation

## Description
A visually striking, highly functional python simulation of an automated warehouse. A fleet of intelligent robots dynamically navigates a grid system to fetch packages, deliver them to a central processing station, and manage their own power cycles. 

The application utilizes **PyVista** for powerful hardware-accelerated rendering, but mathematically locks the camera to a **top-down 2D orthographic projection**, ensuring peak readability and preventing accidental camera-drifting while managing complex logistics.

## Key Features
- **Sleek 2D Top-Down View:** The environment is rendered in a locked top-down interface with parallel projection. It guarantees perfect overview of the entire warehouse floor while retaining 3D lighting and rendering benefits.
- **Dynamic Physics & Visuals:** Running at a highly optimized **60 ticks per second**, robots move with smooth fluidity. Each robot features a distinct "front" face (nose geometry) and pivots realistically on its axis depending on its pathing angle. 
- **Battery & Docking Mechanics:** Robots have individual battery limits. When running low, they safely route back to their exclusively assigned "charging bay".
- **Anti-Congestion "1-Way" Routing:** The unloading zone is constrained by a strict 1-way entry queue and a separate exit tunnel via Directed Graphs (`nx.DiGraph`).
- **Smart Perimeter Routing:** Robots that are empty and returning to base intuitively use an outer "highway" (the edge of the grid) to speed back home without clogging aisles. 
- **A* Collision Avoidance:** Agents use NetworkX graph algorithms to forecast collisions tick-by-tick and sidestep blocked cells dynamically.

## Installation

Ensure you have a modern Python environment active, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the main simulation file to spawn the logistics dashboard. Close the visualization window to terminate the application.

```bash
python main.py
```

## Configuration
The entire environment is customizable. Open `config.py` to adjust:
- **TICK_RATE** and robot movement speeds (`ROBOT_BASE_SPEED`, `ROBOT_MAX_SPEED`).
- Grid size and the number of obstacles.
- `BATTERY_DEPLETION_RATE` and threshold triggers.
- Robot counts.
- UI Color themes and object aesthetic definitions.
