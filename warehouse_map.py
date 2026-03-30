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
        
        # Initialize a 2D grid graph
        self.graph = nx.grid_2d_graph(self.width, self.height)
        
        self.shelves = set()
        self.generate_shelves()
        
    def generate_shelves(self):
        """
        Creates clusters or rows of shelves ensuring there are aisles available
        for robots to navigate between them.
        """
        possible_shelves = []
        # Create vertical rows with 2-wide aisles in between, leaving space near borders
        for x in range(2, self.width - 2, 4):
            for y in range(2, self.height - 2):
                possible_shelves.append((x, y))
                possible_shelves.append((x + 1, y))
                
        # Randomly select a subset of these to be shelves based on config
        random.shuffle(possible_shelves)
        self.shelves = set(possible_shelves[:config.NUM_SHELVES])
        
        # Ensure the unloading zones are never blocked by a shelf
        if config.UNLOADING_ZONE_IN in self.shelves:
            self.shelves.remove(config.UNLOADING_ZONE_IN)
        if config.UNLOADING_ZONE_OUT in self.shelves:
            self.shelves.remove(config.UNLOADING_ZONE_OUT)
            
        # Remove shelf nodes from the navigation graph (they act as obstacles)
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
