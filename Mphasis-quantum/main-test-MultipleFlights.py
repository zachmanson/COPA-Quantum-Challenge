import pandas as pd
from graph import Graph
from flight import Flight
from airport import Airport
from pnr import PNR
from datetime import datetime
import numpy as np
from dimod import BinaryQuadraticModel
import dimod


#=======================================================================================================
# Create the graph
flight_graph = Graph()

# Path to the CSV file
available_flights = 'data_files/PRMI-DM-AVAILABLE_FLIGHTS.csv'  
cancelled_flights = 'data_files/PRMI-DM_TARGET_FLIGHTS_test.csv' 

# Build the graph using the CSV file
flight_graph.add_flights_from_csv(available_flights)
flight_graph.add_cancelled_flights_from_csv(cancelled_flights)

# # Draw the graph
# flight_graph.draw_graph()

#=======================================================================================================

# Step 1: Load both CSV files
target_flights_df = pd.read_csv("data_files/PRMI-DM_TARGET_FLIGHTS.csv")
pnr_df = pd.read_csv("data_files/PRMI_DM_ALL_PNRs.csv")

# Step 2: Filter PNRs with matching DEP_KEY in both datasets
# Extract the DEP_KEYs from the target flights
target_dep_keys = target_flights_df['DEP_KEY'].unique()

# Filter PNRs where DEP_KEY matches
matching_pnr_df = pnr_df[pnr_df['DEP_KEY'].isin(target_dep_keys)]

# Step 3: Create a list of PNR objects from the filtered PNR DataFrame
pnr_list = []
for _, row in matching_pnr_df.iterrows():
    trip_id = f"{row['RECLOC']}_{row['DEP_KEY']}"  # Create unique trip identifier
    pnr = PNR(
        recloc=row['RECLOC'],
        creation_dtz=row['CREATION_DTZ'],
        cabin_cd=row['CABIN_CD'],
        cos_cd=row['COS_CD'],
        oper_od_orig_cd=row['OPER_OD_ORIG_CD'],
        oper_od_dest_cd=row['OPER_OD_DEST_CD'],
        dep_key=row['DEP_KEY'],
        dep_dt=row['DEP_DT'],
        orig_cd=row['ORIG_CD'],
        dest_cd=row['DEST_CD'],
        flt_num=row['FLT_NUM'],
        dep_dtml=row['DEP_DTML'],
        arr_dtml=row['ARR_DTML'],
        dep_dtmz=row['DEP_DTMZ'],
        arr_dtmz=row['ARR_DTMZ'],
        od_broken_ind=row['OD_BROKEN_IND'],
        pax_cnt=row['PAX_CNT'],
        cvm=row['CVM'],
        conn_time_mins=row['CONN_TIME_MINS']
    )
    pnr.trip_id = trip_id  # Assign the trip identifier
    pnr_list.append(pnr)

# Now `pnr_list` contains all the PNR objects matching the DEP_KEY
# You can print or further process the list
print(len(pnr_list))



#=======================================================================================================

# now list of pnr object is the list of passengers that are on the cancelled flights

#=======================================================================================================

# Step 4: Find the available flights in the graph
airport_code = "VUY"
airport = flight_graph.get_airport(airport_code)
available_flights_vuy = [flight for flight in airport.flights_out if flight.status == "available" and flight.dest_cd == "TPH"]



pnrr_list = []
for passenger in pnr_list:
    if ((passenger.oper_od_orig_cd) or (passenger.orig_cd == airport_code)):
        pnrr_list.append(passenger)

pnr_list = pnrr_list 

pnr_list = pnr_list[:2]  # Limit the number of passengers for testing 
available_flights_vuy = available_flights_vuy[:10]  # Limit the number of flights for testing


#=======================================================================================================
#=======================================================================================================
#QUBO formulation
#=======================================================================================================
#=======================================================================================================

# # Building the QUBO formulation for the problem 

# # Initialize a dictionary to store binary variables
# # The keys are tuples (passenger_id, flight_id), values will be 0 or 1 to represent the binary state


# # Step 1: Initiate binary variables for each passenger-flight pair
# binary_variables = {}

# # Populate binary variables for each passenger-flight pair
# for passenger in pnr_list:
#     for flight in available_flights_vuy:
#         # Create a binary variable key for this passenger-flight pair
#         binary_variables[(passenger.trip_id, flight.dep_key)] = 0  # Initial state, will later be optimized


# # Step 2 : Objective function

# # Initialize the QUBO dictionary to store penalties for each passenger-flight assignment
# qubo_objective = {}

# # Populate QUBO objective based on time difference
# for passenger in pnr_list:
#     for flight in available_flights_vuy:
#         # Calculate time difference in minutes
#         original_time = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%dT%H:%M:%SZ")
#         new_time = datetime.strptime(flight.dep_dtmz, "%Y-%m-%dT%H:%M:%SZ")
#         time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes

#         # Set up the QUBO penalty based on time difference
#         qubo_objective[(passenger.trip_id, flight.dep_key)] = time_difference


# #Step 3: Constraints

# # Penalty strength for constraints
# penalty_strength = 1000

# # Initialize QUBO dictionary for the constraints
# qubo_constraints = {}

# # Constraint 1: Each passenger is assigned to exactly one flight
# for passenger in pnr_list:
#     for flight1 in available_flights_vuy:
#         for flight2 in available_flights_vuy:
#             if flight1 != flight2:
#                 # Adding penalties if the same passenger is assigned to multiple flights
#                 key = ((passenger.trip_id, flight1.dep_key), (passenger.trip_id, flight2.dep_key))
#                 qubo_constraints[key] = penalty_strength

# # Constraint 2: Seat availability on each flight
# for flight in available_flights_vuy:
#     assigned_passengers = [passenger for passenger in pnr_list if passenger.dep_key == flight.dep_key]
#     if len(assigned_passengers) > int(flight.c_avail_cnt):
#         for passenger1 in assigned_passengers:
#             for passenger2 in assigned_passengers:
#                 if passenger1 != passenger2:
#                     key = ((passenger1.trip_id, flight.dep_key), (passenger2.trip_id, flight.dep_key))
#                     qubo_constraints[key] = penalty_strength


# #Step 4: Combine the objective and constraints to create the final QUBO dictionary

# # Combine objective and constraints into a QUBO
# bqm = BinaryQuadraticModel('BINARY')

# # Add the objective terms to the QUBO
# for (passenger_flight, time_penalty) in qubo_objective.items():
#     bqm.add_variable(passenger_flight, time_penalty)

# # Add the constraint penalties to the QUBO
# for (pair1, pair2), penalty in qubo_constraints.items():
#     bqm.add_interaction(pair1, pair2, penalty)

# # The QUBO is now ready to be solved



#=======================================================================================================



# Assume pnr_list and available_flights_vuy are already populated

#=======================================================================================================
# QUBO formulation using dimod
#=======================================================================================================

# Step 1: Initialize a binary quadratic model (BQM)
bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)


# Step 2: Initiate binary variables for each passenger-flight pair
# Objective function coefficients
for passenger in pnr_list:
    # Fod direct flights
    original_time_departure = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
    original_time_arrival = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")

    for flight in available_flights_vuy:
    # Assign a direct flight for the direct flight
        if ((passenger.oper_od_orig_cd == flight.orig_cd) & (passenger.oper_od_dest_cd == flight.dest_cd)):
            # Include differences in departure time
            # original_time = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%dT%H:%M:%SZ")
            # new_time = datetime.strptime(flight.dep_dtmz, "%Y-%m-%dT%H:%M:%SZ")
            new_time_departure = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
            # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
            time_difference_departure = ((new_time_departure - original_time_departure).total_seconds() / 60.0)  # in minutes

            # Include the arrival time
            new_time_arrival = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
            # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
            time_difference_arrival = ((new_time_arrival - original_time_arrival).total_seconds() / 60.0)  # in minutes
            
            # Add a variable for this passenger-flight pair in the BQM
            ## Score bands for departure delays
            if time_difference_departure < 0:
                bqm.add_variable((passenger.trip_id, flight.dep_key), 10000)
            elif ((0 < time_difference_departure) & (360 <= time_difference_departure)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-8000+time_difference_departure)*7/3 ) # Less than 6 hours
            elif ((360 < time_difference_departure) & (720 <= time_difference_departure)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-7000+time_difference_departure)*5/3 ) # Between 6 and 12 hours
            elif ((720 < time_difference_departure & 1440) <= (time_difference_departure)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-6000+time_difference_departure)*4/3 ) # Between 12 and 24 hours
            elif ((1440 < time_difference_departure) & (2880 <= time_difference_departure)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-5000+time_difference_departure)*3/3 ) # Between 24 and 48 hours
            elif 2880 < time_difference_departure: # More than 48 hours
                bqm.add_variable((passenger.trip_id, flight.dep_key), 10000) 

            ## Score bands for arrival delays
            if ((0 < time_difference_arrival) & (360 <= time_difference_arrival)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-8000+time_difference_arrival)*7/3 ) # Less than 6 hours
            elif ((360 < time_difference_arrival) & (720 <= time_difference_arrival)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-7000+time_difference_arrival)*5/3 ) # Between 6 and 12 hours
            elif ((720 < time_difference_arrival) & (1440 <= time_difference_arrival)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-6000+time_difference_arrival)*4/3 ) # Between 12 and 24 hours
            elif ((1440 < time_difference_arrival) & (2880 <= time_difference_arrival)):
                bqm.add_variable((passenger.trip_id, flight.dep_key), (-5000+time_difference_arrival)*3/3 ) # Between 24 and 48 hours
            elif 4320 < time_difference_arrival: # More than 72 hours
                bqm.add_variable((passenger.trip_id, flight.dep_key), 10000) 

    # For two-legged flights
    for flight1 in available_flights_vuy:
        for flight2 in available_flights_vuy: # We skip having the same flight twice
            time_arr1 = datetime.strptime(flight1.arr_dtmz, "%Y-%m-%d %H:%M:%S") # Time of arrival of first flight
            time_dep2 = datetime.strptime(flight2.dep_dtmz, "%Y-%m-%d %H:%M:%S") # Time of departure of second flight
            conn_time =  ((time_dep2 - time_arr1).total_seconds() / 60.0)  # in minutes

            if (flight1 == flight2): # We cannot have the same flight as a connection flight twice
                pass
            

            elif ( (flight1.orig_cd == passenger.orig_cd) & (flight2.dest_cd == passenger.dest_cd) 
                  & (flight1.dest_cd == flight2.orig_cd) 
                  & (60 <= conn_time ) & (conn_time <= 720) ): # Connecting time between 1 and 12 hours
                
                new_time_departure = datetime.strptime(flight1.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_departure = ((new_time_departure - original_time_departure).total_seconds() / 60.0)  # in minutes

                # Include the arrival time
                new_time_arrival = datetime.strptime(flight2.arr_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
                # time_difference = abs((new_time - original_time).total_seconds() / 60.0)  # in minutes
                time_difference_arrival = ((new_time_arrival - original_time_arrival).total_seconds() / 60.0)  # in minutes
                
                # Add a variable for this passenger-flight pair in the BQM
                ## Score bands for departure delays
                if time_difference_departure < 0:
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), 10000)
                elif ((0 < time_difference_departure) & (360 <= time_difference_departure)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-6000+time_difference_departure)*7/3 ) # Less than 6 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-6000+time_difference_departure)*7/3 ) # Less than 6 hours
                elif ((360 < time_difference_departure) & (720 <= time_difference_departure)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-5000+time_difference_departure)*5/3 ) # Between 6 and 12 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-5000+time_difference_departure)*5/3 ) # Between 6 and 12 hours
                elif ((720 < time_difference_departure & 1440) <= (time_difference_departure)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-4000+time_difference_departure)*4/3 ) # Between 12 and 24 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-4000+time_difference_departure)*4/3 ) # Between 12 and 24 hours
                elif ((1440 < time_difference_departure) & (2880 <= time_difference_departure)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-3000+time_difference_departure)*3/3 ) # Between 24 and 48 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-3000+time_difference_departure)*3/3 ) # Between 24 and 48 hours
                elif 2880 < time_difference_departure: # More than 48 hours
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), 10000)
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), 10000) 

                ## Score bands for arrival delays
                if ((0 < time_difference_arrival) & (360 <= time_difference_arrival)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-6000+time_difference_arrival)*7/3 ) # Less than 6 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-6000+time_difference_arrival)*7/3 ) # Less than 6 hours
                elif ((360 < time_difference_arrival) & (720 <= time_difference_arrival)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-5000+time_difference_arrival)*5/3 ) # Between 6 and 12 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-5000+time_difference_arrival)*5/3 ) # Between 6 and 12 hours
                elif ((720 < time_difference_arrival) & (1440 <= time_difference_arrival)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-4000+time_difference_arrival)*4/3 ) # Between 12 and 24 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-4000+time_difference_arrival)*4/3 ) # Between 12 and 24 hours
                elif ((1440 < time_difference_arrival) & (2880 <= time_difference_arrival)):
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), (-3000+time_difference_arrival)*3/3 ) # Between 24 and 48 hours
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), (-3000+time_difference_arrival)*3/3 ) # Between 24 and 48 hours
                elif 4320 < time_difference_arrival: # More than 72 hours
                    bqm.add_variable((passenger.trip_id, flight1.dep_key), 10000)
                    bqm.add_variable((passenger.trip_id, flight2.dep_key), 10000)
                



    




# Step 3: Constraints

# Increase penalty strength for assignment constraint
penalty_strength = 100  # Adjust this based on the scale of time differences

# Constraint 1: Ensure each passenger is assigned to exactly one flight
#for passenger in pnr_list:
#    for flight1 in available_flights_vuy:
#        for flight2 in available_flights_vuy:
#            if flight1 != flight2:
#                bqm.add_interaction((passenger.trip_id, flight1.dep_key), (passenger.trip_id, flight2.dep_key), penalty_strength)

penalty_strength = 100  # Penalty for constraints

# Constraint 2: Seat availability constraint for each available flight
for flight in available_flights_vuy:
    # List of binary variables for passengers who could be assigned to this flight
    passenger_vars_for_flight = [(passenger.trip_id, flight.dep_key, passenger.pax_cnt) for passenger in pnr_list]

    # Apply penalty for any pair of passengers assigned to the same flight beyond seat availability
    for i in range(len(passenger_vars_for_flight)):
        for j in range(i + 1, len(passenger_vars_for_flight)):
            passenger_pair = (passenger_vars_for_flight[i][0:1], passenger_vars_for_flight[j][0:1])
            # Add penalty for exceeding capacity (only if capacity could be exceeded by assigning both passengers)
            if (passenger_vars_for_flight[i][2] + passenger_vars_for_flight[j][2]) > int(flight.c_avail_cnt):
                bqm.add_interaction(passenger_pair[0], passenger_pair[1], penalty_strength)







#=======================================================================================================
# Solve the BQM using a sampler
#=======================================================================================================

# Option 1: Use Simulated Annealing
sampler = dimod.SimulatedAnnealingSampler()
samples = sampler.sample(bqm, num_reads=200)

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
    for i in pnr_list:
        if i.trip_id == passenger_id:
            print(f"Passenger {passenger_id} assigned to flights: {flight_ids}")
            print(f"Original Time: {i.dep_dtmz}")
            for j in available_flights_vuy:
                if j.dep_key == flight_ids[0]:
                    print(f"New Flight Time: {j.dep_dtmz}")
                    print(f"Time Difference: {best_sample[(passenger_id, flight_ids[0])]}")
            print("\n")
