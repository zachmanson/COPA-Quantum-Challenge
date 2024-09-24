import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from datetime import timedelta

class FlightNetwork:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
    def add_flight(self, departure, arrival, dep_time, arr_time, c_avail, y_avail, dep_key):
        self.graph.add_edge(departure, arrival, dep_time = dep_time, arr_time = arr_time, c_avail = c_avail, y_avail = y_avail, dep_key = dep_key)

    def is_valid_path(self, path, c_seats, y_seats, passenger_class, original_dep_time):
        valid_edges_per_leg = []
        for i in range(len(path) - 1):
            edge_data = self.graph[path[i]][path[i+1]]
            valid_edges_for_leg = []

            for key, data in edge_data.items():
                arr_time = data.get('arr_time')
                dep_time = data.get('dep_time')
                c_avail = int(data.get('c_avail', 0))
                y_avail = int(data.get('y_avail', 0))
                dep_key = data.get('dep_key')


                if i == 0 and (dep_time - original_dep_time) > timedelta(hours = 72):
                    continue

                if passenger_class == 'C':
                    if c_seats > c_avail + y_avail:
                        continue
                if passenger_class == 'Y':
                    if y_seats > y_avail:
                        continue

                valid_edges_for_leg.append({
                    'source': path[i],
                    'destination': path[i+1],
                    'dep_key': dep_key,
                    'edge_key' : key,
                    'arr_time': arr_time,
                    'dep_time': dep_time,
                    'c_avail': c_avail,
                    'y_avail': y_avail
                })

            if not valid_edges_for_leg:
                return False, []
            
            valid_edges_per_leg.append(valid_edges_for_leg)

        valid_paths = []
        current_paths = [[edge] for edge in valid_edges_per_leg[0]]

        for i in range(1, len(valid_edges_per_leg)):
            next_paths = []

            for path in current_paths:
                last_edge = path[-1]
                for edge in valid_edges_per_leg[i]:
                    if last_edge['arr_time'] <= edge['dep_time'] and (edge['dep_time'] - last_edge['arr_time']) <= timedelta(hours = 23):
                        new_path = path + [edge]
                        next_paths.append(new_path)

            current_paths = next_paths


        valid_paths_keys = set(tuple(edge['dep_key'] for edge in path) for path in current_paths)
        valid_paths_keys = [list(path) for path in valid_paths_keys]

        return True, valid_paths_keys

    def find_all_paths(self, source, destination, max_legs = 2):
        raw_paths = nx.all_simple_paths(self.graph, source, destination, cutoff= max_legs)
        unique_paths = set(tuple(path) for path in raw_paths)
        return [list(path) for path in unique_paths]
    

    def find_all_valid_paths(self, source, destination, c_seats, y_seats, passenger_class, original_dep_time, max_legs = 2):
        all_paths = self.find_all_paths(source, destination, max_legs)
        valid_paths = []

        for path in all_paths:
            is_valid, valid_paths_keys = self.is_valid_path(path, c_seats, y_seats, passenger_class, original_dep_time)
            if is_valid:
                valid_paths.append(valid_paths_keys)

        return valid_paths

    def visualize(self):
        pos = nx.spring_layout(self.graph, k=0.05)  # Adjust k for node spacing
        plt.figure(figsize=(12, 12))
        nx.draw_networkx_nodes(self.graph, pos, node_size=600, node_color='lightblue')
        nx.draw_networkx_edges(self.graph, pos, arrowstyle='-|>', arrowsize=5, edge_color='gray')
        nx.draw_networkx_labels(self.graph, pos, font_size=12, font_family='sans-serif')
        plt.title('Flight Network')
        plt.show()

    def __repr__(self):
        edge_details = []
        for source, destination, key, data in self.graph.edges(keys=True, data=True):
            edge_details.append(f"{source} -> {destination} (flight {key}): "
                                f"dep_time={data['dep_time']}, arr_time={data['arr_time']}, "
                                f"C seats={data['c_avail']}, Y seats={data['y_avail']}")
        
        return f"FlightNetwork with {self.graph.number_of_nodes()} airports and {self.graph.number_of_edges()} flights:\n" + "\n".join(edge_details)
