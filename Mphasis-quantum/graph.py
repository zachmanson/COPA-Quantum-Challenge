# graph.py
from flight import Flight
from airport import Airport
import networkx as nx
import matplotlib.pyplot as plt

class Graph:
    def __init__(self):
        self.airports = {}  # Dictionary to store Airport objects by code

    def add_flight(self, flight):
        orig_airport = self.get_airport(flight.orig_cd)
        dest_airport = self.get_airport(flight.dest_cd)

        # Add flight to the respective airports
        orig_airport.add_flight_out(flight)
        dest_airport.add_flight_in(flight)

    def get_airport(self, code):
        if code not in self.airports:
            self.airports[code] = Airport(code)
        return self.airports[code]

    def add_flights_from_csv(self, csv_file):
        import csv
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a flight object for each row
                flight = Flight(
                    row['DEP_KEY'], row['DEP_DT'], row['ORIG_CD'], row['DEST_CD'], 
                    row['FLT_NUM'], row['DEP_DTML'], row['ARR_DTML'], row['DEP_DTMZ'], 
                    row['ARR_DTMZ'], row['C_CAP_CNT'], row['C_AUL_CNT'], row['C_PAX_CNT'], 
                    row['C_AVAIL_CNT'], row['Y_CAP_CNT'], row['Y_AUL_CNT'], row['Y_PAX_CNT'], 
                    row['Y_AVAIL_CNT'], "available"
                )
                # Add the flight to the graph
                self.add_flight(flight)
    
    def add_cancelled_flights_from_csv(self, csv_file):
        import csv
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a flight object for each row
                flight = Flight(
                    row['DEP_KEY'], row['DEP_DT'], row['ORIG_CD'], row['DEST_CD'], 
                    row['FLT_NUM'], row['DEP_DTML'], row['ARR_DTML'], row['DEP_DTMZ'], 
                    row['ARR_DTMZ'], row['C_CAP_CNT'], row['C_AUL_CNT'], row['C_PAX_CNT'], 
                    row['C_AVAIL_CNT'], row['Y_CAP_CNT'], row['Y_AUL_CNT'], row['Y_PAX_CNT'], 
                    row['Y_AVAIL_CNT'], "cancelled"
                )
                # Add the flight to the graph
                self.add_flight(flight)

    def draw_graph(self):
        # Create a NetworkX directed graph
        G = nx.DiGraph()

        # Add nodes (airports) and edges (flights)
        for airport_code, airport in self.airports.items():
            G.add_node(airport_code)  # Add airport as a node
            
            for flight in airport.flights_out:
                # Add a directed edge for each flight (from origin to destination)
                G.add_edge(flight.orig_cd, flight.dest_cd, label=flight.flt_num)

        # Generate positions for each node (you can choose layouts like 'spring', 'shell', etc.)
        pos = nx.spring_layout(G)

        # Draw the graph
        plt.figure(figsize=(12, 8))
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color='skyblue', alpha=0.8)

        # Draw edges
        nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='grey', alpha=0.5)

        # Draw labels for nodes (airport codes)
        nx.draw_networkx_labels(G, pos, font_size=10, font_color='black')

        # Draw edge labels (flight numbers)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

        # Show the plot
        plt.title("Flight Network Graph")
        plt.show()
