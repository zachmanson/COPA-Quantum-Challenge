from graph import Graph

# Create the graph
flight_graph = Graph()

# Path to the CSV file
csv_file_path = 'path/to/PRMI_DM_AVAILABLE_FLIGHTS.csv'  # Replace with the actual path

# Build the graph using the CSV file
flight_graph.build_graph_from_csv(csv_file_path)

# Example: Accessing data
for airport_code, airport in flight_graph.airports.items():
    print(f"Airport: {airport_code}")
    print("Outbound flights:")
    for flight in airport.flights_out:
        print(f"Flight {flight.flt_num} to {flight.dest_cd}")
    print("Inbound flights:")
    for flight in airport.flights_in:
        print(f"Flight {flight.flt_num} from {flight.orig_cd}")
