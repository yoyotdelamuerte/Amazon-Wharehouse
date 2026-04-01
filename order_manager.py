import random
import config

class OrderItem:
    def __init__(self, order_id, category, weight, shelf_pos, priority, target_drop):
        self.order_id = order_id
        self.category = category
        self.weight = weight
        self.shelf_pos = shelf_pos
        self.priority = priority
        self.target_drop = target_drop
        self.picked_up = False
        self.delivered = False

class Order:
    _id_counter = 0
    def __init__(self):
        Order._id_counter += 1
        self.order_id = Order._id_counter
        self.priority = random.randint(1, 10) # 10 is highest
        self.items = []
        self.time_created = 0
        self.deadline_timer = config.ORDER_DEADLINE_TICKS
        self.is_late = False
        self.is_completed = False

    @property
    def total_weight(self):
        return sum(item.weight for item in self.items)

    @property
    def is_fully_delivered(self):
        return all(item.delivered for item in self.items)

class OrderManager:
    """Manages spawning of global orders and tracking their fulfillment status."""
    def __init__(self, warehouse_map):
        self.warehouse_map = warehouse_map
        self.active_orders = []
        self.completed_count = 0
        self.late_count = 0
        self.tick_count = 0
        self.spawn_chance = config.ORDER_SPAWN_CHANCE
        
    def generate_random_order(self):
        order = Order()
        order.time_created = self.tick_count
        num_items = random.randint(1, config.ORDER_MAX_ITEMS)
        
        target_drop = random.choice(config.MAP_DROPS) if config.MAP_DROPS else None
        order.target_dropoff = target_drop
        
        for _ in range(num_items):
            cat = random.choice([config.CATEGORY_LIGHT, config.CATEGORY_MEDIUM, config.CATEGORY_HEAVY])
            weight = config.WEIGHT_MAPPING[cat]
            
            valid_shelves = [s for s, c in self.warehouse_map.shelf_categories.items() if c == cat]
            if not valid_shelves:
                return # Cannot fulfill if a category has no shelves
                
            shelf_pos = random.choice(valid_shelves)
            item = OrderItem(order.order_id, cat, weight, shelf_pos, order.priority, target_drop)
            order.items.append(item)
            
        self.active_orders.append(order)
        # Sort by priority
        self.active_orders.sort(key=lambda o: o.priority, reverse=True)
        
    def update(self):
        self.tick_count += 1
        
        if random.random() < self.spawn_chance:
            self.generate_random_order()
            
        # Update timers and check completion
        to_remove = []
        for o in self.active_orders:
            if o.is_fully_delivered:
                o.is_completed = True
                self.completed_count += 1
                to_remove.append(o)
                continue
                
            o.deadline_timer -= 1
            if o.deadline_timer <= 0 and not o.is_late:
                o.is_late = True
                self.late_count += 1
                
        for o in to_remove:
            self.active_orders.remove(o)

    def get_pending_tasks(self):
        """Returns a flat list of items that haven't been picked up yet, sorted by priority."""
        pending = []
        for o in self.active_orders:
            for item in o.items:
                if not item.picked_up:
                    pending.append(item)
        return pending
