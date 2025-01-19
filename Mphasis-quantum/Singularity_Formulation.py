###
### ¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡   ESTE ES EL BUENO   !!!!!!!!!!!!!!!!!!!!!!!!!
###

import pandas as pd
from graph import Graph
from flight import Flight
from airport import Airport
from pnr import PNR
from datetime import datetime
import numpy as np
from dimod import BinaryQuadraticModel
import dimod
import itertools

SINGULARITY_TOKEN = "c8b07936-99b0-416f-a749-150da42f6aa1"
DWAVE_API_TOKEN = "DEV-7b444792d7a75ce33cc91f50fac2e0e021db9259"

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

#=======================================================================================================

# Step 2: Differentiate between trips as mentioned in the chat

pnr_df = pnr_df.sort_values(by=["DEP_DTML"], ascending = [True])
grouped = pnr_df.groupby(["RECLOC"])
for rec, group1 in grouped:
    trip_number = 1
    
    grouped2 = group1.groupby(["OPER_OD_ORIG_CD", "OPER_OD_DEST_CD", "DEP_DT"])

    for (orig, dest, date), group2 in grouped2:
        pnr_df.loc[group2.index, "TRIP_NUMBER"] = int(trip_number)
        trip_number = trip_number + 1
#=======================================================================================================

# Step 3: Filter PNRs with matching DEP_KEY in both datasets
# Extract the DEP_KEYs from the target flights
target_dep_keys = target_flights_df['DEP_KEY'].unique()

# Filter PNRs where DEP_KEY matches
matching_pnr_df = pnr_df[pnr_df['DEP_KEY'].isin(target_dep_keys)]

#=======================================================================================================

# Step 4: Create a list of PNR objects from the filtered PNR DataFrame

# Well what we can do is instead make the list of PASSENGERS (pnr_list) LONGER
# Such that each entrance is different according to the TRIP 
pnr_list_1leg = []
pnr_list_2leg = []
# Matrix saving all of the passengers independently of whether the trip is 1-leg or 2-legged
pnr_list = []

group = matching_pnr_df.groupby(["RECLOC", "TRIP_NUMBER"])

for rec_and_trpnr, group in group:
    recloc = rec_and_trpnr[0]
    trip_number = int( rec_and_trpnr[1] )
    
    # We select the selected pnr
    ## We select from the original PNR in order to differentiate between originally booked as direct or multi-legged
    ## And then re-scheduled as direct (forced or simple) direct
    selected_pnr = pnr_df[(pnr_df["RECLOC"] == recloc) & (pnr_df["TRIP_NUMBER"] == trip_number)] 

    # Now we iterate over all of the rows for this given configuration
    for ktrip, row in group.iterrows():
       #trip_id = f"{'1'}_{'2'}_{legs}legs_{'3'}"
       # We include the trip number and the number of legs
        trip_id = f"{row['RECLOC']}_{int(row['TRIP_NUMBER'])}_{row['DEP_KEY']}"
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
        pnr.trip_id = trip_id
        pnr.trip_number = int(trip_number),
        pnr.trip_legs = len(group),

        ## Now we check if the trip was originally booked as multi-legged or not
        ## The trip only consists of one flight
        if ((pnr.oper_od_orig_cd == pnr.orig_cd) & (pnr.oper_od_orig_cd == pnr.orig_cd)):
            pnr.booked_multi_leg = False
            
            # The flight ORIGINALLY consisted of one leg!
            ## Therefore the "ideal" arrival and departure times are the same 
            ## As the leg that is missing
            pnr.ideal_dep_dtmz = pnr.dep_dtmz
            pnr.ideal_dep_dtml = pnr.dep_dtml

            pnr.ideal_arr_dtmz = pnr.arr_dtmz
            pnr.ideal_arr_dtml = pnr.arr_dtml
        else:
            pnr.booked_multi_leg = True
            
            # The flight ORIGINALLY did NOT consist of one leg! 
            ## Therefore the "ideal" arrival and departure times are the ones
            ## corresponding to the first taken leg
            pnr.ideal_dep_dtmz = min(selected_pnr["DEP_DTMZ"])
            pnr.ideal_dep_dtml = min(selected_pnr["DEP_DTML"])

            
            pnr.ideal_arr_dtmz = max(selected_pnr["ARR_DTMZ"])
            pnr.ideal_arr_dtml = max(selected_pnr["ARR_DTML"])            


        if len(group) == 1:
            pnr_list_1leg.append(pnr)
            
            # We add an additional attribute that tell us whether or not
            # there are more than 1 cancelled flights in the trip
            pnr.trip_multi_leg = False
        elif len(group) == 2:
            pnr_list_2leg.append(pnr)

            # We add an additional attribute that tell us whether or not
            # there are more than 1 cancelled flights in the trip
            pnr.trip_multi_leg = True
        
        # We save it to the general pnr_list either way
        pnr_list.append(pnr)


print("Number of passengers whose booked trip has 1 leg: ", len(pnr_list_1leg))
print("Number of passengers whose booked trip has 2 legs: ", len(pnr_list_2leg))

#print("Total number of flights: ", len(pnr_list_1leg) + len(pnr_list_2leg))
print("Total number of flights: ", len(pnr_list))

#=======================================================================================================

Available_flights_df = 'data_files/PRMI-DM-AVAILABLE_FLIGHTS.csv'  
Available_flights_df = pd.read_csv(Available_flights_df)

# Now we create the available_flights list
available_flights = []
for _, row in Available_flights_df.iterrows():
    flight = Flight(
        dep_key = row["DEP_KEY"],
        dep_dt = row["DEP_DT"],
        orig_cd = row["ORIG_CD"],
        dest_cd = row["DEST_CD"], 
        flt_num = row["FLT_NUM"], 
        dep_dtml = row["DEP_DTML"], 
        arr_dtml = row["ARR_DTML"], 
        dep_dtmz = row["DEP_DTMZ"], 
        arr_dtmz = row["DEP_DTMZ"],
        c_cap_cnt = row["C_CAP_CNT"],
        c_aul_cnt = row["C_AUL_CNT"],
        c_pax_cnt = row["C_PAX_CNT"],
        c_avail_cnt = row["C_AVAIL_CNT"],
        y_cap_cnt = row["Y_CAP_CNT"],
        y_aul_cnt = row["Y_AUL_CNT"],
        y_pax_cnt = row["Y_PAX_CNT"],
        y_avail_cnt = row["Y_AVAIL_CNT"],
        status = True # Put it as to indicate that the flight is available
        # I am not following too much of the code that was previously shared and kind of doing my own
        # Either wa the status wont be used...
    )
    available_flights.append(flight)


#=======================================================================================================

# Initialize model
import singularity.optimization as sop
print("Importing singularity was no issue! ")

#=======================================================================================================

# Initialize functions
# We now create the dictionary that holdes it opposite in terms of the flight
# this will be a dictionary of dictionaries


## We now define the time penalty computation, 
#### The leg_penalty variable is for us to add to multi-legt flights
#### Those will have a high leg_penalty, as we prefer direct flights
def time_penalty(time_difference: float) -> float:
        if time_difference < 0:
            return -10000
        elif time_difference <= 360:
            #return (70 - time_difference)
            return 70
        elif time_difference <= 720:
            #return (50 - time_difference)
            return 50
        elif time_difference <= 1440:
            #return (40 - time_difference)
            return 40
        elif time_difference <= 2880:
            #return (30 - time_difference)
            return 30
        else:
            return -10000

## We now define the local constraint function
#### This function adds the constraint that only one flight 
#### Is given to a given passenger
# variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_one"].append( ( passenger.trip_id, flight.dep_key ) )
def local_constraint(variables_per_passenger, name, penalty_strength = 100):
    
    reaccommodations_passenger = variables_per_passenger["one_one"] + variables_per_passenger["forced_one"] + variables_per_passenger["multi_one"]
    reaccommodations_passenger = reaccommodations_passenger + variables_per_passenger["one_multi"] + variables_per_passenger["multi_multi"]
    name = name
    # We only want for the passenger to be assigned ONCE!!! Therefore the sum must be one

    ancilla_variable = sop.Variable("ancilla")
    local_cost = 0*ancilla_variable
    #print((type(local_cost)))
    #print(Total_cost)

    for variable in reaccommodations_passenger:
        #print("SIUUU")
        #print(type(variable))
        local_cost = local_cost + variable

    return sop.Constraint(lhs = local_cost, operator = "==", rhs = 1, 
                          penalty_strength = penalty_strength, 
                          name = name )


# Now we set the seat constraint
# Now we set the seat constraint
def seat_constraint(variables_per_flight, available_flights, penalty_strength = 1000):
    # List to save the constraints
    constraints = []

    # We now iterate over all the available flights
    for flight in available_flights:
        title = r"Flight_{}_Seat_Constraint".format(flight.dep_key)
        avail_seats = flight.c_avail_cnt + flight.y_avail_cnt

        # Seats taken by the variables for the assigned flight
        ancilla_variable = sop.Variable("ancilla")
        # Now Total_cost is in terms of SOP!!!
        taken_seats = 0*ancilla_variable

        for double in variables_per_flight[flight.dep_key]:

            # Here we have the variable
            variable = double[0]
            # Here we have the passenger
            passenger = double[1]
            taken_seats = taken_seats + passenger.pax_cnt * variable


        # Now we do the constraints
        constraint = sop.Constraint(lhs = taken_seats, operator="<=", 
                       rhs = avail_seats, penalty_strength= penalty_strength,
                       name = title)
        constraints.append(constraint)

    return constraints

        

## Now we create the dictionaries! 
# For local constraints
variables_per_passenger = {}
# For seat constraints!
variables_per_flight = {}

# We initialize / initialise the variables_per_flight dictionary
for flight in available_flights:
    variables_per_flight[str(flight.dep_key)] = []



# We create the general dictionary 
general_dic = {}
general_dic["one_one"] = []
general_dic["one_multi"] = []
general_dic["multi_one"] = []
general_dic["multi_multi"] = []
general_dic["forced_one"] = []

# We now give structure to the variables_per_passenger dictionary
#group = matching_pnr_df.groupby(["RECLOC", "TRIP_NUMBER"])

#for rec_and_trpnr, group in group:
#    recloc = rec_and_trpnr[0]
#    trip_number = rec_and_trpnr[1]

#    # We now give structure to the dictionary storing the flights PER variable
#    variables_per_passenger[(str(recloc), str(int(trip_number)))] = general_dic


#====================================================================================================================================

## We now compute the possiblities for each origin and destination

flights_out_dic = {}
flights_in_dic = {}
flights_out_in_dic = {}
# This last dictionary contains all the possible two-legged combinations for a given origin and destination
flights_2legs_out_in_dic = {}


# We initialize the dictionaries
orig_keys = Available_flights_df["ORIG_CD"].unique()
dest_keys = Available_flights_df["DEST_CD"].unique()

for orig_key in orig_keys:
    flights_out_dic[str(orig_key)] = []

for dest_key in dest_keys:
    flights_in_dic[str(dest_key)] = []

# Now we initialize for the one-legged and two-legged "Master" dictionaries
#combinations = list( Available_flights_df.groupby(["ORIG_CD", "DEST_CD"]).groups.keys() ) #WRONG!!!
combinations = list(itertools.product(orig_keys, dest_keys))
for combination in combinations:
    flights_out_in_dic[(str(combination[0]), str(combination[1]))] = []
    flights_2legs_out_in_dic[(str(combination[0]), str(combination[1]))] = []

# Now we fill in the DIRECT dictionaries
for flight in available_flights:
    flights_out_dic[str(flight.orig_cd)].append(flight)
    flights_in_dic[str(flight.dest_cd)].append(flight)
    flights_out_in_dic[( str(flight.orig_cd), str(flight.dest_cd) )].append(flight)


# Now we fill the dictionaries for two-legged flights
for combination in combinations:
    first_legs = flights_out_dic[ str(combination[0]) ]
    second_legs = flights_in_dic[ str(combination[1]) ]

    # Now we check each combination
    for first_leg in first_legs:
        for second_leg in second_legs:
            
            # if the first and second leg do not satisfy spatial conditions,
            if (first_leg.dest_cd != second_leg.orig_cd):
                continue
            
            # Now we check time conditions
            first_leg_arr = datetime.strptime(first_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
            second_leg_dep = datetime.strptime(second_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")
            conn_time = (second_leg_dep - first_leg_arr).total_seconds() / 60.0    

            ## if the connection time is too low or the connection time is too high
            ### Minimum 60 minutes of time and maximum 12 hours of connection time
            if ((conn_time <= 60) or (720 <= conn_time)):
                continue
            else:
                flights_2legs_out_in_dic[(str(combination[0]), str(combination[1]))].append( (first_leg, second_leg) )


print("Flight inventories finished!!! ")


#=================================================================================================================================

# We add costs for the CVM variables

one_one_cost = 0
one_multi_cost = int(1e4)
multi_one_cost = int(1e2)
multi_multi_cost = int(1e6)

# Factor to include in the computation of the cvm!
cvm_factor = {}
cvm_factor["one_one"] = int(100)
cvm_factor["one_multi"] = int(1e2)
cvm_factor["multi_one"] = int(1e3)
cvm_factor["multi_multi"] = int(1e1)
cvm_factor["forced_one"] = int(120)

# To change this cost, depending on the feedback that we obtain
forced_one_cost = 0
## Different penalties for each proposed solution

#=================================================================================================================================

#=================================================================================================================================

############### ¡¡¡¡¡¡¡ NOW WE SOLVE!!!!!!!! ###############

n_variables = 0
n_one_one = 0
n_one_multi = 0
n_multi_multi = 0
n_multi_one = 0
n_forced_one = 0


print(" Setting seach space! ")

pnr_list = pnr_list[0:2]
available_flights = available_flights[0:10]

print("Reduced dataset: ")
print("Number of passengers: ", len(pnr_list) )
print("Number of available flights: ", len(available_flights) )


# We have the TOTAL cost for the whole system
ancilla_variable = sop.Variable("ancilla")

# Now Total_cost is in terms of SOP!!!
Total_cost = 0*ancilla_variable
#print((type(Total_cost)))
#print(Total_cost)

variables_list = []

constraints_pnr = {}

for passenger in pnr_list: 
    print("(Passenger, trip number): ", (passenger.recloc, passenger.trip_number[0]), "/", len(pnr_list))

    variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))] = general_dic
    
    #***********************************************************************************
    ### DIRECT FLIGHTS
    #***********************************************************************************

    ## ONE-ONE CASE
    ## BOOKING ONLY HAS ONE DIRECT FLIGHT
    ## THEREFORE, WE JUST FIND A NEW DIRECT FLIGHT
    if not passenger.booked_multi_leg:

        # We retrieve the flights important for our case
        available_flights_case = flights_out_in_dic[ (str(passenger.orig_cd), str(passenger.dest_cd)) ]
        
        # Now we iterate over all possible case
        for flight in available_flights_case:

             # Retrieve the original times
            new_time_dep = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
            new_time_arr = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S") 


            orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
            orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                
            time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0) # Minutes
            time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0) 

            cost_dep = time_penalty(time_diff_dep)
            cost_arr = time_penalty(time_diff_arr)

            # Is this a good pairing?
            if ((cost_dep <= 0) or (cost_arr <= 0)): # Check the penalty
                #  We do not add an energy for this flight, the flight is already terrible!
                continue 
            else:
                # We add a variable for this flight
                var = (passenger.trip_id, flight.dep_key)
                 
                # We put it in shape of the sop language
                var = sop.Variable(str(var))
                #print(var)
                var_cost = cost_dep + cost_arr + cvm_factor["one_one"]*passenger.cvm
                
                # We save the variable
                variables_list.append((var, var_cost))

                # Now we add it to the total cost
                Total_cost = Total_cost + var * var_cost

                # We save the assigned DIRECT flight for this passenger
                variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_one"].append( var )

                # We add the assigned flight to be dictionary saving the global variables
                variables_per_flight[flight.dep_key].append( (var, passenger) )

                # We increment the number of total variables
                n_variables = n_variables + 1
                n_one_one = n_one_one + 1

    
    if passenger.booked_multi_leg:
        ## FORCED-ONE CASE
        ## BOOKING HAS SEVERAL LEGS, AND WE OBTAIN A DIRECT ONE 
        ## FOR THE WHOLE TRIP, NOT JUST THE CANCELLED LEG    
        
        # We retrieve the flights important for our case
        available_flights_case = flights_out_in_dic[ (str(passenger.oper_od_orig_cd), str(passenger.oper_od_dest_cd)) ]
        for flight in available_flights_case:

            # Passenger originally BOOKED multiple legs!
            ideal_time_dep = datetime.strptime(passenger.ideal_dep_dtmz, "%Y-%m-%d %H:%M:%S")
            ideal_time_arr = datetime.strptime(passenger.ideal_arr_dtmz, "%Y-%m-%d %H:%M:%S")

            ideal_time_diff_dep = ((new_time_dep - ideal_time_dep).total_seconds() / 60.0) # Mintues
            ideal_time_diff_arr = ((new_time_arr - ideal_time_arr).total_seconds() / 60.0)

            ideal_cost_dep = time_penalty(ideal_time_diff_dep)
            ideal_cost_arr = time_penalty(ideal_time_diff_arr)
                
            # Is this flight terrible?
            if ((ideal_cost_dep <= 0) or (ideal_cost_arr <= 0)): # Check the penalty
                    #  We do not add an energy for this flight, the flight is already terrible!
                continue 
            else:
                
                # We add a variable for this flight
                var = (passenger.trip_id, flight.dep_key)
                 
                # We put it in shape of the sop language
                var = sop.Variable(str(var))
                #print(var)
                var_cost = cost_dep + cost_arr + cvm_factor["forced_one"]*passenger.cvm
                
                # We save the variable
                variables_list.append((var, var_cost))

                # Now we add it to the total cost
                Total_cost = Total_cost + var * var_cost

                # We save the assigned DIRECT flight for this passenger
                variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["forced_one"].append( var )

                # We add the assigned flight to be dictionary saving the global variables
                variables_per_flight[flight.dep_key].append( (var, passenger) )

                # We increment the number of total variables
                n_variables = n_variables + 1
                n_forced_one = n_forced_one + 1
     

        #MULTI-ONE CASE
        ## BOOKING HAS SEVERAL LEGS, AND WE OBTAIN A DIRECT ONE
        ## FOR THE CANCELLED TRIP
        available_flights_case = flights_out_in_dic[ (str(passenger.orig_cd), str(passenger.dest_cd)) ]
        for flight in available_flights_case:

            orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
            orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
            
            time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0) # Minutes
            time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0) 

            cost_dep = time_penalty(time_diff_dep)
            cost_arr = time_penalty(time_diff_arr)

            # Is this a good pairing?
            if ((cost_dep <= 0) or (cost_arr <= 0)): # Check the penalty
                    #  We do not add an energy for this flight, the flight is already terrible!
                continue 
            else:

                # We add a variable for this flight
                var = (passenger.trip_id, flight.dep_key)
                 
                # We put it in shape of the sop language
                var = sop.Variable(str(var))
                #print(var)
                var_cost = cost_dep + cost_arr + cvm_factor["multi_one"]*passenger.cvm
                
                # We save the variable
                variables_list.append((var, var_cost))

                # Now we add it to the total cost
                Total_cost = Total_cost + var * var_cost

                # We save the assigned DIRECT flight for this passenger
                variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["multi_one"].append( var )

                # We add the assigned flight to be dictionary saving the global variables
                variables_per_flight[flight.dep_key].append( (var, passenger) )
                
                # We increment the number of total variables
                n_variables = n_variables + 1
                n_multi_one = n_multi_one + 1
    

    #****************************************************************************************************
    # Now we do NON-DIRECT flights
    #****************************************************************************************************
    # We do NOT make the distinction between oper_orig_cd and oper_dest_cd anymore
    # Because functionally there is no difference. if the case is one-multi, oper_od_orig_cd = orig_cd
    
    available_flights_case = flights_2legs_out_in_dic[(str(passenger.oper_od_orig_cd), str(passenger.oper_od_dest_cd))]
    # Now we iterate over the flights
    for flight_combination in available_flights_case:
        
        first_leg = flight_combination[0]
        second_leg = flight_combination[1]
        
        # Check the departure penalty costs FIRST before doiny any computation
        original_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
        new_time_dep = datetime.strptime(first_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
        time_diff_dep = ((new_time_dep - original_time_dep).total_seconds() / 60.0)  # in minutes
                    
        # Check if the penalty is acceptable or not
        cost_dep = time_penalty(time_diff_dep)
        if (cost_dep <= 0): # Check the penalty
            # Skip all the pairings with ths flight as the first leg
            continue

        # Now we check if the second flight is trash in terms of arriving
        original_time_arr = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
        new_time_arr = datetime.strptime(second_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
        time_diff_arr = ((new_time_arr - original_time_arr).total_seconds() / 60.0)  # in minutes

        # Check if the cost is acceptable or not
        cost_arr = time_penalty(time_diff_arr)
        if (cost_arr <= 0):
            # Skip this second leg
            continue


        # If this does not fail, then we add the new variable! 
        ## This pairing is acceptable then!
        ## We differentiate between multi-multi and one-multi


        if passenger.booked_multi_leg:
            #****************************************************************************************************************
                ## MULTI-MULTI COST!!! ##
            #****************************************************************************************************************

            # We add a variable for this flight
            var = (passenger.trip_id, (first_leg.dep_key, second_leg.dep_key))
                 
            # We put it in shape of the sop language
            var = sop.Variable(str(var))
            #print(var)
            var_cost = cost_dep + cost_arr + cvm_factor["multi_multi"]*passenger.cvm
                
            # We save the variable
            variables_list.append((var, var_cost))

            # Now we add it to the total cost
            Total_cost = Total_cost + var * var_cost

            # We save the assigned DIRECT flight for this passenger
            variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["multi_multi"].append( var )

            # We add the assigned flight to be dictionary saving the global variables
            variables_per_flight[flight.dep_key].append( (var, passenger) )

            # We increment the number of total variables
            n_variables = n_variables + 1
            n_multi_multi = n_multi_multi + 1
            
        else:
            #****************************************************************************************************************
            ## ONE-MULTI CASE !!! ##
            #****************************************************************************************************************
            # We add a variable for this flight
            var = (passenger.trip_id, (first_leg.dep_key, second_leg.dep_key))
                 
            # We put it in shape of the sop language
            var = sop.Variable(str(var))
            #print(var)
            var_cost = cost_dep + cost_arr + cvm_factor["one_multi"]*passenger.cvm
                
            # We save the variable
            variables_list.append((var, var_cost))

            # Now we add it to the total cost
            Total_cost = Total_cost + var * var_cost

            # We save the assigned DIRECT flight for this passenger
            variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_multi"].append( var )

            # We add the assigned flight to be dictionary saving the global variables
            variables_per_flight[flight.dep_key].append( (var, passenger) )

            # We increment the number of total variables
            n_variables = n_variables + 1
            n_one_multi = n_one_multi + 1
    
    # We now SAVE the local constraints
    #print( variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))] )
    constraints_pnr[str(passenger.recloc)] = local_constraint(variables_per_passenger[(str(passenger.recloc), str(passenger.trip_number[0]))], name = passenger.recloc)


# Cost function
objective = sop.Objective(Total_cost, "maximize")

# Objective
Reaccommodation = sop.Model(objective)

print("********************************************************")
print("Number of one_one: ", n_one_one)
print("Number of one_multi: ", n_one_multi)
print("Number of multi_one: ", n_multi_one)
print("Number of multi_multi: ", n_multi_multi)
print("Number of forced_one: ", n_forced_one)
print("Total number of variables: ", n_variables)


# Now we add the LOCAL constraints
for key in constraints_pnr.keys():
    Reaccommodation.add_constraint(constraints_pnr[key])


# Now we add the SEAT constraints
# The LHS is a LIST containing the constraints
seat_constraints = seat_constraint(variables_per_flight, available_flights, penalty_strength = 1000)
print(seat_constraints)

#for constraint in seat_constraints:
#    Reaccommodation.add_constraint(constraint)


# Finally we OPTIMIZE!!!
print("Almost optimizing...")
#result = Reaccommodation.optimize(solver = "simulated_annealing", num_solution = 5, timeout = 60)

# The total number of the search space is
# n_search_space = 2**n_variables 
# because these are binary variables
# Let us optimize working with a fraction of it

n_factor = 2**5 # 1 / 2**n_factor of the search space
n_search_space = (2**n_variables)/(2**n_factor)

time_per_sample = 60*60*1 # 1 Hour (excessively high!)
time_per_sample = 60*5 # 5 minutes

# This one supports up to 1M variables!

solver = "dwave_hybrid"
#solver = "simulated_annealing"


# Import solver ! 
import neal
#solver=neal.SimulatedAnnealingSampler()

print(r"Optimizing!!! Solver: {}".format(solver))

result = Reaccommodation.optimize(solver=solver, num_solutions = int(n_search_space), 
                                  time_limit=time_per_sample, dwave_api_token = DWAVE_API_TOKEN
                                  )

print("Saving results!")
import pickle
with open("Reaccommodations.pkl", "wb") as f:
    pickle.dump(result, f)