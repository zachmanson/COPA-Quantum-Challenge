import dimod
from graph import Graph
from datetime import datetime

class Solver:
    def __init__(self, initial_airport: str, target_airport: str, pnr_list: list, available_flights: list, flight_graph: Graph):
        self.initial_airport = initial_airport
        self.target_airport = target_airport
        self.pnr_list = pnr_list
        self.available_flights = available_flights #this is the entire available flight list 
        self.flight_graph = flight_graph
        self.bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)
        self.available_flights_to_target = self.find_flights()
    
    def find_flights(self) -> list:
        airport = self.flight_graph.get_airport(self.initial_airport)
        available_flights_to_target = [flight for flight in airport.flights_out if flight.status == "available" and flight.dest_cd == self.target_airport]

        pnrr_list = []
        for passenger in self.pnr_list:
            if (passenger.orig_cd == self.initial_airport):
                pnrr_list.append(passenger)

        self.pnr_list = pnrr_list 

        #truncating for testing 
        self.pnr_list = self.pnr_list[:2]  # Limit the number of passengers for testing 
        available_flights_to_target = available_flights_to_target[:10]  # Limit the number of flights for testing
        return available_flights_to_target

    def calculate_penalty(self, time_difference: float) -> int:
        if time_difference < 0:
            return 10000
        elif time_difference <= 360:
            return (-8000 + time_difference) * 7 / 3
        elif time_difference <= 720:
            return (-7000 + time_difference) * 5 / 3
        elif time_difference <= 1440:
            return (-6000 + time_difference) * 4 / 3
        elif time_difference <= 2880:
            return (-5000 + time_difference) * 3 / 3
        else:
            return 10000


    def formulate_qubo(self):
        for passenger in self.pnr_list:
            #direct flights
            for flight in self.available_flights_to_target:
                original_time_departure = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
                new_time_departure = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_departure = ((new_time_departure - original_time_departure).total_seconds() / 60.0)  # in minutes

                # Include the arrival time
                original_time_arrival = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")
                new_time_arrival = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_arrival = ((new_time_arrival - original_time_arrival).total_seconds() / 60.0)  # in minutes

                dep_penalty = self.calculate_penalty(time_difference_departure)
                arr_penalty = self.calculate_penalty(time_difference_arrival)

                # Add a variable for this passenger-flight pair in the BQM
                self.bqm.add_variable((passenger.trip_id, flight.dep_key), dep_penalty)
                self.bqm.add_variable((passenger.trip_id, flight.dep_key), arr_penalty)

        #for two legged flights

        self.add_constraints()
    
    def add_constraints(self):
        # Increase penalty strength for assignment constraint
        penalty_strength = 100  # Adjust this based on the scale of time differences

        # Constraint 1: Ensure each passenger is assigned to exactly one flight
        for passenger in self.pnr_list:
            for flight1 in self.available_flights_to_target:
                for flight2 in self.available_flights_to_target:
                    if flight1 != flight2:
                        self.bqm.add_interaction((passenger.trip_id, flight1.dep_key), (passenger.trip_id, flight2.dep_key), penalty_strength)

        penalty_strength = 100  # Penalty for constraints

        # Constraint 2: Seat availability constraint for each available flight
        for flight in self.available_flights_to_target:
            # List of binary variables for passengers who could be assigned to this flight
            passenger_vars_for_flight = [(passenger.trip_id, flight.dep_key, passenger.pax_cnt) for passenger in pnr_list]

            # Apply penalty for any pair of passengers assigned to the same flight beyond seat availability
            for i in range(len(passenger_vars_for_flight)):
                for j in range(i + 1, len(passenger_vars_for_flight)):
                    passenger_pair = (passenger_vars_for_flight[i][0:1], passenger_vars_for_flight[j][0:1])
                    # Add penalty for exceeding capacity (only if capacity could be exceeded by assigning both passengers)
                    if (passenger_vars_for_flight[i][2] + passenger_vars_for_flight[j][2]) > int(flight.c_avail_cnt):
                        self.bqm.add_interaction(passenger_pair[0], passenger_pair[1], penalty_strength)

    def solve(self):
        # Option 1: Use Simulated Annealing
        sampler = dimod.SimulatedAnnealingSampler()
        samples = sampler.sample(self.bqm, num_reads=200)

        # # Option 2: Use Exact Solver (for small BQMs)
        # sampler = dimod.ExactSolver()
        # samples = sampler.sample(bqm)

        # Display the best sample
        best_sample = samples.first.sample
        best_energy = samples.first.energy

        # Print the results
        print("Best Sample:", best_sample)
        print("Energy of Best Sample:", best_energy)

        # Step 4: Process the results
        # Extract the flight assignments from the best sample
        assignments = {}
        for key, value in best_sample.items():
            if value == 1:  # Only consider assigned flights
                passenger_id, flight_id = key
                assignments.setdefault(passenger_id, []).append(flight_id)

        # Print the assignments
        # for passenger_id, flight_ids in assignments.items():
        #     print(f"Passenger {passenger_id} assigned to flights: {flight_ids}")
            
        # in the output show the passenger details, its orginal time and teh allocated new fight time and the time diffrence 

        for passenger_id, flight_ids in assignments.items():
            for i in self.pnr_list:
                if i.trip_id == passenger_id:
                    print(f"Passenger {passenger_id} assigned to flights: {flight_ids}")
                    print(f"Original Time: {i.dep_dtmz}")
                    for j in self.available_flights_to_target:
                        if j.dep_key == flight_ids[0]:
                            print(f"New Flight Time: {j.dep_dtmz}")
                            print(f"Time Difference: {best_sample[(passenger_id, flight_ids[0])]}")
                    print("\n")