import dimod
from datetime import datetime
from graph import Graph

class Solver:
    def __init__(self):
        self.bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

    def add_airport_contraint(self, initial_airport: str, target_airport: str, pnr_list: list, available_flights: list, flight_graph: Graph):
        airport = flight_graph.get_airport(initial_airport)
        available_flights_to_target = [flight for flight in airport.flights_out if flight.status == "available" and flight.dest_cd == target_airport]

        #truncate for testing (optional)
        pnr_list = pnr_list[:2]
        available_flights_to_target = available_flights_to_target[:10]

        for passenger in pnr_list:
            #direct flights
            for flight in available_flights_to_target:
                original_time_departure = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
                new_time_departure = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_departure = ((new_time_departure - original_time_departure).total_seconds() / 60.0)  # in minutes

                # Include the arrival time
                original_time_arrival = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")
                new_time_arrival = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_arrival = ((new_time_arrival - original_time_arrival).total_seconds() / 60.0)  # in minutes

                dep_penalty = self._calculate_penalty(time_difference_departure)
                arr_penalty = self._calculate_penalty(time_difference_arrival)

                # Add a variable for this passenger-flight pair in the BQM
                self.bqm.add_variable((passenger.trip_id, flight.dep_key), arr_penalty + dep_penalty)

            #two legged flights 
            #honestly not sure if this will even work
            penalty_strength = 100
            for passenger in pnr_list:
                if passenger.oper_od_orig_cd != passenger.orig_cd or passenger.oper_od_dest_cd != passenger.dest_cd:
                    #first leg flights to TPH
                    first_leg_flights = [flight for flight in available_flights if flight.dest_cd == 'TPH']
                    second_leg_flights = [flight for flight in available_flights if flight.orig_cd == 'TPH']

                    for first_leg in first_leg_flights:
                        for second_leg in second_leg_flights:
                            first_leg_arrival = datetime.strptime(first_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
                            second_leg_departure = datetime.strptime(second_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")

                            connection_time = (second_leg_departure - first_leg_arrival).total_seconds() / 60.0

                        if 60 <= connection_time <= 720: #think document said between 1hr and 12hr is good connection time?
                            self.bqm.add_interaction(
                                (passenger.trip_id, first_leg.dep_key),
                                (passenger.trip_id, second_leg.dep_key),
                                -penalty_strength
                            )
                            #added -penalty to encourage this pairing

            self._add_constraints(passenger, pnr_list, available_flights_to_target)

    def _calculate_penalty(self, time_difference: float) -> int:
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

    def _add_constraints(self, pnr_list, available_flights):
        penalty_strength = 100
        
        # Constraint 1: Ensure each passenger is assigned to exactly one flight
        for passenger in pnr_list:
            for flight1 in available_flights:
                for flight2 in available_flights:
                    if flight1 != flight2:
                        self.bqm.add_interaction(
                            (passenger.trip_id, flight1.dep_key), 
                            (passenger.trip_id, flight2.dep_key), 
                            penalty_strength
                        )
        
        # Constraint 2: Seat availability constraint for each available flight
        for flight in available_flights:
            # List of binary variables for passengers who could be assigned to this flight
            passenger_vars_for_flight = [
                (passenger.trip_id, flight.dep_key, passenger.pax_cnt) 
                for passenger in pnr_list
            ]

            # Apply penalty for any pair of passengers assigned to the same flight beyond seat availability
            for i in range(len(passenger_vars_for_flight)):
                for j in range(i + 1, len(passenger_vars_for_flight)):
                    passenger_pair = (passenger_vars_for_flight[i][0:1], passenger_vars_for_flight[j][0:1])
                    # Add penalty for exceeding capacity (only if capacity could be exceeded by assigning both passengers)
                    if (passenger_vars_for_flight[i][2] + passenger_vars_for_flight[j][2]) > int(flight.c_avail_cnt):
                        self.bqm.add_interaction(
                            passenger_pair[0], 
                            passenger_pair[1], 
                            penalty_strength
                        )

    def solve(self) -> dict:
        sampler = dimod.SimulatedAnnealingSampler()
        samples = sampler.sample(self.bqm, num_reads=200)

        best_sample = samples.first.sample
        best_energy = samples.first.energy

        assignments = {}
        for key, value in best_sample.items():
            if value == 1:  # Only consider assigned flights
                passenger_id, flight_id = key
                assignments.setdefault(passenger_id, []).append(flight_id)


        return {
            'assignments': assignments,
            'best_energy': best_energy
        }