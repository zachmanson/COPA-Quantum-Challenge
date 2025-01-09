import dimod
import itertools
from datetime import datetime
from pnr import PNR
from flight import Flight

class BQMSolver:
    def __init__(self):
        pass

    def solve_reaccomodation(
            self, 
            pnr_list: list[PNR], 
            available_flights: list[Flight],
            flights_out_in_dic: dict[tuple[str, str], list[Flight]],
            flights_2legs_out_in_dic: dict[tuple[str, str], list[tuple[Flight, Flight]]],
            cvm_factor: dict[str, int],
            one_one_cost: int = 0, 
            one_multi_cost: int = int(1e4),
            multi_one_cost: int = int(1e2), 
            multi_multi_cost: int = int(1e6),
            forced_one_cost: int = 0, 
            num_reads: int = 200) -> tuple[dict, int]:
        
        bqm = self._build_bqm(pnr_list, available_flights, flights_out_in_dic, flights_2legs_out_in_dic, cvm_factor,
                             one_one_cost, one_multi_cost, multi_one_cost, multi_multi_cost, forced_one_cost)
        best_sample, best_energy = self._solve_bqm(bqm, num_reads)
        return best_sample, best_energy

    def _time_penalty(self, time_difference: float) -> float:
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


    def _build_bqm(self, 
                   pnr_list: list[PNR], 
                   available_flights: list[Flight],
                   flights_out_in_dic: dict[tuple[str, str], list[Flight]],
                   flights_2legs_out_in_dic: dict[tuple[str, str], list[tuple[Flight, Flight]]],
                   cvm_factor: dict[str, int],
                   one_one_cost: int = 0, 
                   one_multi_cost: int = int(1e4),
                   multi_one_cost: int = int(1e2), 
                   multi_multi_cost: int = int(1e6),
                   forced_one_cost: int = 0) -> dimod.BinaryQuadraticModel:

        bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

        n_one_one = 0
        n_one_multi = 0
        n_multi_one = 0
        n_multi_multi = 0
        n_forced_one = 0
        n_variables = 0

        variables_per_passenger = {}
        general_dic: dict[str, list] = {}
        general_dic["one_one"] = []
        general_dic["one_multi"] = []
        general_dic["multi_one"] = []
        general_dic["multi_multi"] = []
        general_dic["forced_one"] = []

        for passenger in pnr_list:
            variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))] = general_dic.copy()

        variables_per_flight: dict[str, dict[str, list[tuple[PNR, tuple[str, str]]]]] = {}
        for flight in available_flights:
            variables_per_flight[str(flight.dep_key)] = {}
            variables_per_flight[str(flight.dep_key)]["1Leg"] = []
            variables_per_flight[str(flight.dep_key)]["2Leg"] = []

        for passenger in pnr_list:

            passenger_vars_dict = variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]

            if not passenger.booked_multi_leg:
                available_flights_case = flights_out_in_dic[(str(passenger.orig_cd), str(passenger.dest_cd))]

                for flight in available_flights_case:
                    new_time_dep = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")
                    new_time_arr = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")

                    orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                    orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")

                    time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0)
                    time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0)

                    cost_dep = self._time_penalty(time_diff_dep)
                    cost_arr = self._time_penalty(time_diff_arr)
                    if ((cost_dep >= 0) or (cost_arr >= 0)):
                        continue
                    else:
                        bqm.add_variable((passenger.trip_id, flight.dep_key), cost_arr + cost_dep + one_one_cost- cvm_factor["one_one"] * passenger.cvm)
                        n_variables = n_variables + 1
                        n_one_one = n_one_one + 1
                        passenger_vars_dict["one_one"].append((passenger.trip_id, flight.dep_key))
                        variables_per_flight[flight.dep_key]["1Leg"].append((passenger, flight.dep_key))

            if passenger.booked_multi_leg:
                available_flights_case = flights_out_in_dic[
                    (str(passenger.oper_od_orig_cd), str(passenger.oper_od_dest_cd))]

                for flight in available_flights_case:
                    ideal_time_dep = datetime.strptime(passenger.ideal_dep_dtmz, "%Y-%m-%d %H:%M:%S")
                    ideal_time_arr = datetime.strptime(passenger.ideal_arr_dtmz, "%Y-%m-%d %H:%M:%S")

                    new_time_dep = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")
                    new_time_arr = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")

                    ideal_time_diff_dep = ((new_time_dep - ideal_time_dep).total_seconds() / 60.0)  # Mintues
                    ideal_time_diff_arr = ((new_time_arr - ideal_time_arr).total_seconds() / 60.0)

                    ideal_cost_dep = self._time_penalty(ideal_time_diff_dep)
                    ideal_cost_arr = self._time_penalty(ideal_time_diff_arr)

                    if ((ideal_cost_dep >= 0) or (ideal_cost_arr >= 0)):
                        continue
                    else:
                        bqm.add_variable((passenger.trip_id, flight.dep_key), ideal_cost_dep + ideal_cost_arr + forced_one_cost - cvm_factor["forced_one"] * passenger.cvm)
                        n_variables = n_variables + 1
                        n_forced_one = n_forced_one + 1
                        passenger_vars_dict["forced_one"].append((passenger.trip_id, flight.dep_key))
                        variables_per_flight[flight.dep_key]["1Leg"].append((passenger, flight.dep_key))

                available_flights_case = flights_out_in_dic[(str(passenger.orig_cd), str(passenger.dest_cd))]
                for flight in available_flights_case:
                    new_time_dep = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")
                    new_time_arr = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")

                    orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                    orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")

                    time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0)
                    time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0)

                    cost_dep = self._time_penalty(time_diff_dep)
                    cost_arr = self._time_penalty(time_diff_arr)

                    if ((cost_dep >= 0) or (cost_arr >= 0)):
                        continue
                    else:
                        bqm.add_variable((passenger.trip_id, flight.dep_key), cost_arr + cost_dep + multi_one_cost - cvm_factor["multi_one"] * passenger.cvm)
                        n_variables = n_variables + 1
                        n_multi_one = n_multi_one + 1
                        passenger_vars_dict["multi_one"].append((passenger.trip_id, flight.dep_key))
                        variables_per_flight[flight.dep_key]["1Leg"].append((passenger, flight.dep_key))

            available_flight_combinations = flights_2legs_out_in_dic[(str(passenger.oper_od_orig_cd), str(passenger.oper_od_dest_cd))]
            for flight_combination in available_flight_combinations:
                    first_leg = flight_combination[0]
                    second_leg = flight_combination[1]

                    original_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                    new_time_dep = datetime.strptime(first_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")
                    time_diff_dep = ((new_time_dep - original_time_dep).total_seconds() / 60.0)

                    cost_dep = self._time_penalty(time_diff_dep)
                    if (cost_dep >= 0):
                        continue

                    original_time_arr = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")
                    new_time_arr = datetime.strptime(second_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
                    time_diff_arr = ((new_time_arr - original_time_arr).total_seconds() / 60.0)

                    cost_arr = self._time_penalty(time_diff_arr)
                    if (cost_arr >= 0):
                        continue
                    if passenger.booked_multi_leg:
                        bqm.add_variable((passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)),
                                         cost_arr + cost_dep + multi_multi_cost
                                     - cvm_factor["multi_multi"] * passenger.cvm)
                        n_variables = n_variables + 1
                        n_multi_multi = n_multi_multi + 1
                        passenger_vars_dict["multi_multi"].append(
                            (passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)))

                        variables_per_flight[first_leg.dep_key]["2Leg"].append(
                            (passenger, (first_leg.dep_key, second_leg.dep_key)))
                        variables_per_flight[second_leg.dep_key]["2Leg"].append(
                            (passenger, (first_leg.dep_key, second_leg.dep_key)))

                    else:
                        bqm.add_variable((passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)),
                                      cost_arr + cost_dep + multi_multi_cost
                                      - cvm_factor["one_multi"] * passenger.cvm)
                        n_variables = n_variables + 1
                        n_one_multi = n_one_multi + 1
                        passenger_vars_dict["one_multi"].append(
                            (passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)))
                        variables_per_flight[first_leg.dep_key]["2Leg"].append(
                            (passenger, (first_leg.dep_key, second_leg.dep_key)))
                        variables_per_flight[second_leg.dep_key]["2Leg"].append(
                            (passenger, (first_leg.dep_key, second_leg.dep_key)))
            

            self._local_constraint(passenger_vars_dict, bqm, penalty_combination=int(1e6))

        print("********************************************************")
        print("Number of one_one: ", n_one_one)
        print("Number of one_multi: ", n_one_multi)
        print("Number of multi_one: ", n_multi_one)
        print("Number of multi_multi: ", n_multi_multi)
        print("Number of forced_one: ", n_forced_one)
        print("Total number of variables: ", n_variables)
        print("********************************************************")
        # Now we add the global constraints for the seats
        self._seat_constraints(variables_per_flight, available_flights, bqm, penalty_seats=int(1e8))

        return bqm

    def _local_constraint(self, variables_per_passenger: dict, bqm: dimod.BinaryQuadraticModel,
                        penalty_combination: int = 1000) -> None:
        """Adds the local constraint that only one flight is given to a given passenger."""

        reaccommodations_passenger = variables_per_passenger["one_one"] + variables_per_passenger[
            "forced_one"] + variables_per_passenger["multi_one"]
        reaccommodations_passenger = reaccommodations_passenger + variables_per_passenger[
            "one_multi"] + variables_per_passenger["multi_multi"]
        combinations = list(itertools.combinations(reaccommodations_passenger, 2))

        for combination in combinations:
            first_variable = combination[0]
            second_variable = combination[1]
            bqm.add_interaction(
                first_variable,
                second_variable,
                penalty_combination
            )


    def _seat_constraints(self, variables_per_flight: dict, available_flights: list[Flight], bqm: dimod.BinaryQuadraticModel,
                         penalty_seats: int = int(1e8)) -> None:
        """Adds the global constraint for the available seats for a given flight."""

        for flight in available_flights:
            avail_seats = flight.c_avail_cnt + flight.y_avail_cnt

            assigned_seats_1leg = 0
            assigned_seats_2leg = 0

            for variable in variables_per_flight[flight.dep_key]["1Leg"]:
                assigned_seats_1leg = assigned_seats_1leg + variable[0].pax_cnt

            for variable in variables_per_flight[flight.dep_key]["2Leg"]:
                assigned_seats_2leg = assigned_seats_2leg + variable[0].pax_cnt

            assigned_seats = assigned_seats_1leg + assigned_seats_2leg

            if (assigned_seats) > int(avail_seats):
                direct = variables_per_flight[flight.dep_key]["1Leg"]
                direct_direct = list(itertools.combinations(direct, 2))
                for combination in direct_direct:
                    direct1 = combination[0]
                    direct2 = combination[1]
                    direct1 = (direct1[0].trip_id, direct1[1])
                    direct2 = (direct2[0].trip_id, direct2[1])

                    bqm.add_interaction(
                        direct1,
                        direct2,
                        penalty_seats
                    )

                non_direct = variables_per_flight[flight.dep_key]["2Leg"]
                ndirect_ndirect = list(itertools.combinations(non_direct, 2))

                for combination in ndirect_ndirect:
                    ndirect1 = combination[0]
                    ndirect2 = combination[1]
                    ndirect1 = (ndirect1[0].trip_id, (ndirect1[1][0], ndirect1[1][1]))
                    ndirect2 = (ndirect2[0].trip_id, (ndirect2[1][0], ndirect2[1][1]))
                    bqm.add_interaction(
                        ndirect1,
                        ndirect2,
                        penalty_seats
                    )

                direct_ndirect = [(a, b) for a, b in itertools.product(
                    variables_per_flight[flight.dep_key]["1Leg"],
                    variables_per_flight[flight.dep_key]["2Leg"])
                                  if (b, a) not in itertools.product(
                        variables_per_flight[flight.dep_key]["1Leg"],
                        variables_per_flight[flight.dep_key]["2Leg"])]
                for combination in direct_ndirect:
                    dir_ndir1 = combination[0]
                    dir_ndir2 = combination[1]
                    dir_ndir1 = (dir_ndir1[0].trip_id, dir_ndir1[1])
                    dir_ndir2 = (dir_ndir2[0].trip_id, (dir_ndir2[1][0], dir_ndir2[1][1]))
                    bqm.add_interaction(
                        dir_ndir1,
                        dir_ndir2,
                        penalty_seats
                    )

    def _solve_bqm(self, bqm: dimod.BinaryQuadraticModel, num_reads: int = 200) -> tuple[dict, int]:
        """Solves the BQM using Simulated Annealing."""
        sampler = dimod.SimulatedAnnealingSampler()
        samples = sampler.sample(bqm, num_reads=num_reads)
        best_sample = samples.first.sample
        best_energy = samples.first.energy
        return best_sample, best_energy

    def process_results(self, best_sample: dict, pnr_list: list[PNR], available_flights: list[Flight]) -> None:
        """Processes the results from the BQM solution."""
        assignments: dict[str, list[str]] = {}
        for key, value in best_sample.items():
             if value == 1:
                passenger_id, flight_id = key
                assignments.setdefault(passenger_id, []).append(flight_id)

        print("********************************************************")
        print("Passenger reaccommodations: ")
        print("********************************************************")

        for passenger_id, flight_ids in assignments.items():
             for i in pnr_list:
                if i.trip_id == passenger_id:
                    print(f"Passenger {passenger_id} assigned to flights: {flight_ids}")
                    print(f"Original Time: {i.dep_dtmz}")
                    for j in available_flights:
                        if j.dep_key == flight_ids[0]:
                            print(f"New Flight Time: {j.dep_dtmz}")
                            print(f"Time Difference: {best_sample[(passenger_id, flight_ids[0])]}")
                    print("\n")