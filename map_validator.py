import networkx as nx

class MapValidator:
    @staticmethod
    def validate(map_data, grid_width, grid_height):
        """
        map_data: list of dict representing cells with their type.
        returns: (is_valid, error_message, parsed_data) 
        Parsed data contains: shelves, chargers, drops
        """
        shelves = {}
        chargers = []
        drops_in = []
        drops_out = []
        
        for cell in map_data:
            pos = tuple(cell['pos'])
            type_ = cell['type']
            if type_ == 'shelf':
                shelves[pos] = cell['category']
            elif type_ == 'charger':
                chargers.append(pos)
            elif type_ == 'drop_in':
                drops_in.append(pos)
            elif type_ == 'drop_out':
                drops_out.append(pos)

        if not chargers:
            return False, "Vous devez placer au moins une station de recharge.", None
        if not drops_in or not drops_out:
            return False, "Vous devez placer au moins un quai IN et un quai OUT.", None
        if len(drops_in) != len(drops_out):
            return False, "Le nombre de quais IN doit être égal au nombre de quais OUT.", None

        # Check that we have at least one shelf of each category
        cats = set(shelves.values())
        if not cats:
            return False, "Vous devez placer au moins une étagère.", None
            
        # Build temp graph for connectivity check
        graph = nx.grid_2d_graph(grid_width, grid_height, create_using=nx.Graph)
        for s in shelves:
            if s in graph:
                graph.remove_node(s)
                
        # Check if all free cells are in the same connected component
        components = list(nx.connected_components(graph))
        if not components:
            return False, "La carte est vide ou bloquée.", None
            
        main_comp = max(components, key=len)
        
        # verify all stations, drops and shelf adjacencies are in the main component
        for c in chargers + drops_in + drops_out:
            if c not in main_comp:
                return False, f"L'entité à la position {c} est enfermée ou non atteignable.", None
                
        for s in shelves:
            x, y = s
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            valid_n = [n for n in neighbors if n in main_comp]
            if not valid_n:
                return False, f"L'étagère à la position {s} ne peut pas être atteinte par les robots.", None

        # Pair Drop INs and OUTs based on proximity.
        drops = []
        unpaired_outs = list(drops_out)
        for d_in in drops_in:
            x, y = d_in
            # Find adjacent OUT
            adj = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            paired = False
            for a in adj:
                if a in unpaired_outs:
                    drops.append({'in': d_in, 'out': a})
                    unpaired_outs.remove(a)
                    paired = True
                    break
            if not paired:
                return False, f"Le quai IN en {d_in} doit avoir un quai OUT adjacent.", None

        parsed = {
            'shelves': shelves,
            'chargers': chargers,
            'drops': drops
        }
        
        return True, "", parsed
