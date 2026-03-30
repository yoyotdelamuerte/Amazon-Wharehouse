# 3D Automated Warehouse Simulation

## Description
A visually striking, highly functional 3D Python simulation of an automated warehouse. A fleet of intelligent robots dynamically navigates a grid system to fetch packages, deliver them to a central processing station, and manage their own power cycles, all visualized in real-time using PyVista.

## Key Features
- **Advanced 3D PyVista Environment:** Sleek, high-performance rendering of the warehouse floor, obstacles, robot agents, and their physical trails.
- **Battery & Docking Mechanics:** Robots have individual battery limits. When running low, they abandon their fetch orders and safely route back to their exclusively assigned "charging bay" automatically. 
- **Anti-Congestion "1-Way" Routing:** The unloading zone is constrained by a strict 1-way entry queue and a separate exit tunnel implemented via Directed Graphs (`nx.DiGraph`). This entirely eliminates traffic bottlenecks.
- **Smart Périphérique Routing:** Robots that are empty and returning to base intuitively use an outer "highway" (the edge of the grid `y=18`) to speed back to their base. Because their charging stations are defined as isolated cul-de-sac bays, robots avoid driving over one another while charging.
- **A* Collision Avoidance:** Agents use NetworkX graph sub-views to forecast collisions tick-by-tick and sidestep blocked cells dynamically.

## Installation

Ensure you have a modern Python environment active, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the main simulation file. Close the 3D window to exit the application.

```bash
python main.py
```

## Configuration
The entire environment is customizable. Open `config.py` to adjust:
- Grid size and the number of obstacles.
- `BATTERY_DEPLETION_RATE` and threshold triggers.
- Robot counts and movement speed settings.
- Color themes (switch between dark neon vibes and bright industrial schemes).
