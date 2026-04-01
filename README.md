# 3D Automated Warehouse Control Center

## Description
A visually striking, highly functional Python simulation of an automated logistics warehouse. A fleet of intelligent robots dynamically navigates an interconnected grid system to fetch grouped packages based on order priority, deliver them to multiple central drop-off stations, and manage their own power cycles intelligently.

The simulation has been completely overhauled to include a robust **PyQt5 Multi-Window Dashboard**, allowing users to dynamically sketch warehouse layouts in a Map Editor before launching the high-performance **PyVista** 3D visualization.

## Key Features
- **Interactive Map Editor:** Draw your own warehouse layout using an intuitive 2D grid editor. Place modular shelving units, specialized loading docks (IN/OUT), and robot charging bays. The built-in validator ensures the warehouse is structurally sound and accessible before launch.
- **Deep Fleet Logistics (Cooperative A*):** Robots utilize an advanced multi-agent pathfinding algorithm featuring "Soft-Reservation". Robots algorithmically avoid each others' predicted future paths, virtually eliminating head-to-head collisions and traffic jams.
- **Patience-Based Deadlock Resolver:** In unnavigable chokepoints, robots that are blocked will yield to higher-priority peers. If trapped for too long, a "patience" timer triggers a complete path recalculation, ensuring complex 3-way deadlocks resolve themselves smoothly.
- **Dynamic Order Management System:** Features realistic item requests with varying weights (Light, Medium, Heavy) and processing priorities. The system orchestrates order fulfillments, tracks latencies, and dynamically assigns tasks to empty or partially-loaded robots.
- **Sleek 2D Top-Down View:** The environment is rendered in a locked top-down viewing angle with parallel projection. It guarantees perfect overview of the entire warehouse floor while retaining 3D hardware-accelerated rendering benefits via PyVista.
- **Smart Perimeter Routing:** Robots that are empty and returning to base intuitively use an outer "highway" to speed back home without clogging critical aisles.

## Installation

Ensure you have Python 3.8+ active, then install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the main entry point to spawn the Map Editor and Dashboard windows.

```bash
python main.py
```

### Workflow
1. **Design Map:** Upon launch, use the grid editor to paint Shelves (Left Click), Loading Docks (Middle Click), and Chargers (Right Click).
2. **Launch System:** Once your map is valid, click "Launch Simulation".
3. **Monitor Logistics:** The Order Dashboard and 3D Visualizer will boot up, seamlessly processing incoming orders until you close the application.

## Configuration
While the warehouse layout is fully dynamic via the editor, engine logic is customizable. Open `config.py` to adjust:
- **TICK_RATE** and physical robot movement speeds.
- Agent properties like `BATTERY_DEPLETION_RATE`, maximum carrying capacity, and charging thresholds.
- Order spawn rates and generation probabilities.
- UI Color themes and object aesthetic definitions.
