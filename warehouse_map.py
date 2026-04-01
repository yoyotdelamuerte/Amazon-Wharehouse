import networkx as nx
import random
import config

class WarehouseMap:
    """
    Manages the 3D warehouse environment mapping:
    - Generates a navigation grid using networkx.
    - Places static shelves (obstacles).
    - Removes shelf coordinates from the traversable graph to prevent robot collision.
    """
    def __init__(self):
        self.width = config.GRID_WIDTH
        self.height = config.GRID_HEIGHT
        
        # Initialize a 2D grid graph, using DiGraph for 1-way streets
        self.graph = nx.grid_2d_graph(self.width, self.height, create_using=nx.DiGraph)
        
        self.shelves = set()
        self.shelf_categories = {}
        self.load_shelves()
        self.enforce_one_way_lanes()
        self.create_charging_bays()

    def create_charging_bays(self):
        """
        Removes edges between adjacent charging stations so robots don't drive
        through one station to get to another.
        """
        chargers = config.MAP_CHARGERS
        for i in range(len(chargers)):
            for j in range(i + 1, len(chargers)):
                c1, c2 = chargers[i], chargers[j]
                if self.graph.has_edge(c1, c2):
                    self.graph.remove_edge(c1, c2)
                if self.graph.has_edge(c2, c1):
                    self.graph.remove_edge(c2, c1)

    def enforce_one_way_lanes(self):
        """
        Creates one-way constraints for the unloading zones to prevent deadlock.
        Forces the IN node to only lead to the OUT node, and prevents returning.
        """
        for drop in config.MAP_DROPS:
            d_in = drop['in']
            d_out = drop['out']
            
            # Prevent going from OUT back to IN
            if self.graph.has_edge(d_out, d_in):
                self.graph.remove_edge(d_out, d_in)
        
    def load_shelves(self):
        """
        Loads shelves from the configured map data and removes their nodes
        from the navigation graph so robots go around them.
        """
        self.shelf_categories = config.MAP_SHELVES.copy()
        self.shelves = set(self.shelf_categories.keys())
        
        for shelf in self.shelves:
            if shelf in self.graph:
                self.graph.remove_node(shelf)
                
    def get_random_shelf(self):
        """
        Returns a random shelf position. Used for target assignment.
        """
        return random.choice(list(self.shelves)) if self.shelves else None
        
    def get_adjacent_navigable_nodes(self, node):
        """
        Returns all valid adjacent nodes (up, down, left, right) that a robot can stand on.
        Agents need this to reach a shelf since they cannot occupy the shelf's coordinate.
        """
        x, y = node
        neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        # Return only neighbors that exist in the navigable graph
        return [n for n in neighbors if n in self.graph]

    def shortest_path(self, start, target):
        """
        Computes the shortest path using A* pathfinding via networkx.
        Returns a list of coordinate tuples (path) or None if no path exists.
        """
        try:
            # A* using Manhattan distance as heuristic for grid movements
            path = nx.astar_path(
                self.graph, 
                start, 
                target, 
                heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
            )
            return path
        except nx.NetworkXNoPath:
            return None
