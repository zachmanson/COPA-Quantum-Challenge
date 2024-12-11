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
        trip_id = f"{row['RECLOC']}_{row['TRIP_NUMBER']}_LEG{ktrip}_{row['DEP_KEY']}"
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
bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

#=======================================================================================================

# Initialize functions
# We now create the dictionary that holdes it opposite in terms of the flight
# this will be a dictionary of dictionaries


## We now define the time penalty computation, 
#### The leg_penalty variable is for us to add to multi-legt flights
#### Those will have a high leg_penalty, as we prefer direct flights
def time_penalty(time_difference: float) -> float:
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

## We now define the local constraint function
#### This function adds the constraint that only one flight 
#### Is given to a given passenger
# variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_one"].append( ( passenger.trip_id, flight.dep_key ) )
def local_constraint(variables_flight, penalty_combination = 1000):
    
    direct_reaccommodations = variables_flight["one_one"] + variables_flight["forced_one"] + variables_flight["multi_one"]
    ndirect_reaccommodations = variables_flight["one_multi"] + variables_flight["multi_multi"]
    # We do not consider multi-multi because YOLOOOO

    dir_combinations = list(itertools.combinations(direct_reaccommodations, 2))
    ndir_combinations = list(itertools.combinations(ndirect_reaccommodations, 2))

    # Now we iterate over the direct-direct combinations
    for dir_combination in dir_combinations:
        first_flight = dir_combination[0]
        second_flight = dir_combination[1]

        # We now add the interaction
        bqm.add_interaction(
                            first_flight, 
                            second_flight, 
                            penalty_combination
                        )
        
    # Now we iterate over the ndir-ndir interactions
    for ndir_combination in ndir_combinations:
        first_flight = ndir_combination[0]
        second_flight = ndir_combination[1]

        # We now add the interaction
        bqm.add_interaction(
                            first_flight, 
                            second_flight, 
                            penalty_combination
                        )
    
    # We now add the direct-ndirect interactions
    dir_ndir_combinations = [(a, b) for a, b in itertools.product(direct_reaccommodations, ndirect_reaccommodations) if (b, a) not in itertools.product(direct_reaccommodations, ndirect_reaccommodations)]
    for dir_ndir_combination in dir_ndir_combinations:
        first_flight = dir_ndir_combinations[0]
        second_flight = dir_ndir_combinations[1]

        # We now add the interaction
        bqm.add_interaction(
                            first_flight, 
                            second_flight, 
                            penalty_combination
                        )

        



## We now define the global constraint function
#### This function adds the constraint for the available seats
#### For a given flight

flight_variables = {}

# We first iterate over all the possible flights and create an empty dictionary
for flight in available_flights:
    flight_variables[str( flight.dep_key )] = {}
    flight_variables[str( flight.dep_key )]["1Leg"] = []
    flight_variables[str( flight.dep_key )]["2Leg"] = []
    #flights_vars_dic2[str( flight.dep_key )] = []

def seat_constraints(flight_variables, available_flights,  penalty_seats = int(1e8)):
    # We now iterate over all the flights available
    for flight in available_flights:
        # Total amount of seats available for a given flight
        avail_seats = flight.c_avail_cnt + flight.y_avail_cnt

        assigned_seats_1leg = 0
        assigned_seats_2leg = 0

        # Now we obtain the number of occupied seats for the flight variables
        ## Direct flights
        for variable in flight_variables[flight.dep_key]["1Leg"]:
            assigned_seats_1leg = assigned_seats_1leg + variable[0].pax_cnt
        
        ## Non-direct flights
        for variable in flight_variables[flight.dep_key]["2Leg"]:
            assigned_seats_2leg = assigned_seats_2leg + variable[0].pax_cnt
        
        # Total amount of assigned seats
        assigned_seats = assigned_seats_1leg + assigned_seats_2leg

        # Now we cheeck if we have overassigned for this flight
        if (assigned_seats) > int(avail_seats):
            # Now we add interactions between the variables
            ## Direct-direct interactions
            direct =  flight_variables[flight.dep_key]["1Leg"]
            direct_direct = list(itertools.combinations(direct, 2))

            # Now we iterate and add the direct-direct interactions
            for combination in direct_direct:
                direct1 = combination[0]
                direct2 = combination[1]
                
                # We redefine the direct variables so we can add the variables as an interaction
                direct1 = (direct1[0].trip_id, direct1[1])
                direct2 = (direct2[0].trip_id, direct2[1])

                # Now we add the interaction
                bqm.add_interaction(
                                    direct1, 
                                    direct2, 
                                    penalty_seats
                                )
            
            # Now we iterate over the 2-leg to 2-leg interaction
            non_direct =  flight_variables[flight.dep_key]["2Leg"]
            ndirect_ndirect = list(itertools.combinations(non_direct, 2))

            # Now we iterate over the combinations
            for combination in ndirect_ndirect:
                ndirect1 = combination[0]
                ndirect2 = combination[1]

                # We redefine the ndirect variables so we can add the variables as an interaction
                ndirect1 = (ndirect1[0].trip_id, (ndirect1[1], ndirect1[2]))
                ndirect2 = (ndirect2[0].trip_id, (ndirect2[1], ndirect2[2]))

                # Now we add the interaction
                bqm.add_interaction(
                                    ndirect1, 
                                    ndirect1, 
                                    penalty_seats
                                )
            
            # Now we add direct to non-direct interactions
            direct_ndirect = [(a, b) for a, b in itertools.product(flight_variables[flight.dep_key]["1Leg"], flight_variables[flight.dep_key]["2Leg"]) 
                               if (b, a) not in itertools.product(flight_variables[flight.dep_key]["1Leg"], flight_variables[flight.dep_key]["2Leg"])]
            # Now we iterate over the combinations
            for combination in range(len(direct_ndirect)):
                    # First variable of direct/two-legs 
                    dir_ndir1 = direct_ndirect[combination][0]
                    # Second variable of direct/two-legs 
                    dir_ndir2 = direct_ndirect[combination][1]

                    # We redefine the direct variables so we can add the variables as an interaction
                    dir_ndir1 = (dir_ndir1[0].trip_id, dir_ndir1[1])
                    dir_ndir2 = (dir_ndir2[0].trip_id, (dir_ndir2[1], dir_ndir2[2]))

                    # We now add the penalty betwen the flights
                    bqm.add_interaction(
                                    dir_ndir1, 
                                    dir_ndir2, 
                                    penalty_seats
                                )

            
#=======================================================================================================

# Explanation
# We will have several cases

# ******************************************************************************************************
# Journey based solution scoring mechanism for following solution scenarios
# ******************************************************************************************************

# Scenario 1-One-One : 
## For each cancelled direct flight between 2 locations in the PNR dataset, 
## the alternate solution is a direct flight between the  2 locations

# Scenario 2-One-Multi : 
## For each cancelled direct flight between 2 locations in the PNR dataset, 
## the alternate solution is a combination of multiple flights between the 2 locations

# Scenario 3- Multi -One : 
## For an impacted multi-stage journey between 2 locations (i.e. Journey plan has more than one flight legs) 
## in the PNR dataset due to cancellations, each cancelled flight leg in the PNR dataset along with its upline/downline flight 
## is replaced with an alternate direct flight between the 2 locations

# Scenario 4-Multi -Multi :  
## For an impacted multi-stage journey between 2 locations (i.e. Journey plan has more than one flight legs) 
## in the PNR dataset due to cancellations, each cancelled flight leg in the PNR dataset along with its upline/downline flight 
## is replaced  with a combination of alternate multiple flights between the 2 locations"


# Let us see how many variables we have!
n_one_one = 0
n_one_multi = 0
n_multi_one = 0
n_multi_multi = 0

# We also define the new "forced_one" category
n_forced_one = 0

# We create a dataframe that tell us all the possibilities that we can have PER RECLOC and PER trip number!
# flight_variables stores the variables FOR a given flight
# variables_flight stores the flights FOR a given variable

variables_flight = {}

# We create the general dictionary 
general_dic = {}
general_dic["one_one"] = []
general_dic["one_multi"] = []
general_dic["multi_one"] = []
general_dic["multi_multi"] = []
general_dic["forced_one"] = []

# We now give structure to the variables_flight dictionary
group = matching_pnr_df.groupby(["RECLOC", "TRIP_NUMBER"])

for rec_and_trpnr, group in group:
    recloc = rec_and_trpnr[0]
    trip_number = rec_and_trpnr[1]

    # We now give structure to the dictionary storing the flights PER variable
    variables_flight[(str(recloc), str(int(trip_number)))] = general_dic


#print(variables_flight.keys())
#=======================================================================================================

# NOW WE SOLVE!!!!!!!

one_one_cost = 0
one_multi_cost = int(1e4)
multi_one_cost = int(1e2)
multi_multi_cost = int(1e6)

# To change this cost, depending on the feedback that we obtain
forced_one_cost = 0
## Different penalties for each proposed solution


# We count the total number of variables
n_variables = 0


## Testing
#pnr_list = pnr_list[0:2]
#available_flights = available_flights[0:10]
print("Reduced dataset: ")
print("Number of passengers: ", len(pnr_list) )
print("Number of available flights: ", len(available_flights) )

for passenger in pnr_list:
    print("Passenger: ", passenger.recloc, "/", len(pnr_list))
    #print("Trip number: ", passenger.trip_number[0])
    
    # We iterate over the available flights
    ## DIRECT FLIGHTS
    for flight in available_flights:
        #print(flight.dep_key)

        new_time_dep = datetime.strptime(flight.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
        new_time_arr = datetime.strptime(flight.arr_dtmz, "%Y-%m-%d %H:%M:%S") 

        ## ONE-ONE CASE
        ## BOOKING ONLY HAS ONE DIRECT FLIGHT
        ## THEREFORE, WE JUST FIND A NEW DIRECT FLIGHT
        if not pnr.booked_multi_leg:

            # We check the spatial constraints
            spat_const1 = (flight.orig_cd != passenger.orig_cd)
            spat_const2 = (flight.dest_cd != passenger.dest_cd)

            if (spat_const1 or spat_const2):
                # The flight does not fit the criteria
                # Since it does not pass through the passenger's origin OR destiantion
                continue
            else:

                orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
                
                time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0) # Minutes
                time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0) 

                cost_dep = time_penalty(time_diff_dep)
                cost_arr = time_penalty(time_diff_arr)

                # Is this a good pairing?
                if ((cost_dep >= 0) or (cost_arr >= 0)): # Check the penalty
                    #  We do not add an energy for this flight, the flight is already terrible!
                    continue 
                else:
                    # We add a variable for this flight
                    bqm.add_variable((passenger.trip_id, flight.dep_key), cost_arr + cost_dep + one_one_cost)
                    n_variables = n_variables + 1
                    n_one_one = n_one_one + 1
                            
                    # We save the assigned DIRECT flight for this passenger
                    variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_one"].append( ( passenger.trip_id, flight.dep_key ) )

                    # We add the assigned flight to be dictionary saving the global variables
                    flight_variables[flight.dep_key]["1Leg"].append( (passenger, flight.dep_key) )
            

        if pnr.booked_multi_leg:
            ## FORCED-ONE CASE
            ## BOOKING HAS SEVERAL LEGS, AND WE OBTAIN A DIRECT ONE 
            ## FOR THE WHOLE TRIP, NOT JUST THE CANCELLED LEG
            #*****************************************************************************************************************
            
            # We check spatial constraints
            spat_const1 = (flight.orig_cd != passenger.oper_od_orig_cd)
            spat_const2 = (flight.dest_cd != passenger.oper_od_dest_cd)

            if (spat_const1 or spat_const2):
                # The flight does not pass through the passenger's desired destination
                # Or origin
                continue
                
            else:
                # Passenger originally BOOKED multiple legs!
                ideal_time_dep = datetime.strptime(pnr.ideal_dep_dtmz, "%Y-%m-%d %H:%M:%S")
                ideal_time_arr = datetime.strptime(pnr.ideal_arr_dtmz, "%Y-%m-%d %H:%M:%S")

                ideal_time_diff_dep = ((new_time_dep - ideal_time_dep).total_seconds() / 60.0) # Mintues
                ideal_time_diff_arr = ((new_time_arr - ideal_time_arr).total_seconds() / 60.0)

                ideal_cost_dep = time_penalty(ideal_time_diff_dep)
                ideal_cost_arr = time_penalty(ideal_time_diff_arr)
                
                # Is this flight terrible?
                if ((ideal_cost_dep >= 0) or (ideal_cost_arr >= 0)): # Check the penalty
                    #  We do not add an energy for this flight, the flight is already terrible!
                    continue 
                else:
                    # We add a variable for this flight
                    # We add the forced one penalty!
                    bqm.add_variable((passenger.trip_id, flight.dep_key), ideal_cost_dep + ideal_cost_arr + forced_one_cost)
                    n_variables = n_variables + 1
                    n_forced_one = n_forced_one + 1
                            
                    # We save the assigned DIRECT flight for this passenger
                    variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["forced_one"].append( ( passenger.trip_id, flight.dep_key ) )

                    # We add the assigned flight to be dictionary saving the global variables
                    flight_variables[flight.dep_key]["1Leg"].append( (passenger, flight.dep_key) )
                
            #*****************************************************************************************************************
            #MULTI-ONE CASE
            ## BOOKING HAS SEVERAL LEGS, AND WE OBTAIN A DIRECT ONE
            ## FOR THE CANCELLED TRIP
            orig_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
            orig_time_arr = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")
            
            time_diff_dep = ((new_time_dep - orig_time_dep).total_seconds() / 60.0) # Minutes
            time_diff_arr = ((new_time_arr - orig_time_arr).total_seconds() / 60.0) 

            cost_dep = time_penalty(time_diff_dep)
            cost_arr = time_penalty(time_diff_arr)

            # Is this a good pairing?
            if ((cost_dep >= 0) or (cost_arr >= 0)): # Check the penalty
                #  We do not add an energy for this flight, the flight is already terrible!
                continue 
            else:
                # We add a variable for this flight
                bqm.add_variable((passenger.trip_id, flight.dep_key), cost_arr + cost_dep + multi_one_cost)
                n_variables = n_variables + 1
                n_multi_one = n_multi_one + 1
                        
                # We save the assigned DIRECT flight for this passenger
                variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["multi_one"].append( ( passenger.trip_id, flight.dep_key ) )

                # We add the assigned flight to be dictionary saving the global variables
                flight_variables[flight.dep_key]["1Leg"].append( (passenger, flight.dep_key) )
    

    # Now we do NON-DIRECT flights
    # We do NOT make the distinction between oper_orig_cd and oper_dest_cd anymore
    # Because functionally there is no difference. if the case is one-multi, oper_od_orig_cd = orig_cd
    # And ifit is MULTI-MULTI there is NO business case
    first_leg_flights = [flight for flight in available_flights if flight.orig_cd == passenger.orig_cd]
    second_leg_flights = [flight for flight in available_flights if flight.dest_cd == passenger.dest_cd]   

    # Now we iterate over the flights
    for first_leg in first_leg_flights:
        # Check the departure penalty costs FIRST before doiny any computation
        original_time_dep = datetime.strptime(passenger.dep_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
        new_time_dep = datetime.strptime(first_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")  # flight time does include seconds
        time_diff_dep = ((new_time_dep - original_time_dep).total_seconds() / 60.0)  # in minutes
                    
        # Check if the penalty is acceptable or not
        cost_dep = time_penalty(time_diff_dep)
        if (cost_dep >= 0): # Check the penalty
            # Skip all the pairings with ths flight as the first leg
            continue

        # Now we check the second leg
        for second_leg in second_leg_flights:

            # Check the connection cases!!!
            ## If this is a VALID connection consider the second leg. 
            ## Otherwise, ignore it
            first_leg_arr = datetime.strptime(first_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
            second_leg_dep = datetime.strptime(second_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")

            # Compute the connection time
            conn_time = (second_leg_dep - first_leg_arr).total_seconds() / 60.0    

            # Only perform the computations if the flights do indeed connect ! 
            ## Skip this pairing if the flights do not connect, 
            ## if the connection time is too low or the connection time is too high
            ### Minimum 60 minutes of time and maximum 12 hours of connection time
            if ((first_leg.dest_cd != second_leg.orig_cd) or (conn_time <= 60) or (720 <= conn_time)):
                # Skip this pairing! 
                # This second leg does not apply as a connecting flight
                continue

            # Now we check if the second flight is trash in terms of arriving
            original_time_arr = datetime.strptime(passenger.arr_dtmz, "%Y-%m-%d %H:%M")  # pnr does not include seconds
            new_time_arr = datetime.strptime(second_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
            time_diff_arr = ((new_time_arr - original_time_arr).total_seconds() / 60.0)  # in minutes

            # Check if the cost is acceptable or not
            cost_arr = time_penalty(time_diff_arr)
            if (cost_arr >= 0):
                # Skip this second leg
                continue


            # If this does not fail, then we add the new variable! 
            ## This pairing is acceptable then!
            ## We differentiate between multi-multi and one-multi


            if pnr.booked_multi_leg:
                #****************************************************************************************************************
                ## MULTI-MULTI COST!!! ##
                #****************************************************************************************************************
                bqm.add_variable((passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)), 
                                                cost_arr + cost_dep + multi_multi_cost)
                # We add the available variables
                n_variables = n_variables + 1
                n_multi_multi = n_multi_multi + 1
                variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["multi_multi"].append( ( passenger.trip_id, (first_leg.dep_key, second_leg.dep_key) ) )


                # We save the variables in the dictionary
                flight_variables[first_leg.dep_key]["2Leg"].append( ( passenger, (first_leg.dep_key, second_leg.dep_key) ) )
                flight_variables[second_leg.dep_key]["2Leg"].append( ( passenger, (first_leg.dep_key, second_leg.dep_key) ) )
            
            else:
                #****************************************************************************************************************
                ## ONE-MULTI CASE !!! ##
                #****************************************************************************************************************
                bqm.add_variable((passenger.trip_id, (first_leg.dep_key, second_leg.dep_key)), 
                                                cost_arr + cost_dep + multi_multi_cost)
                # We add the available variables
                n_variables = n_variables + 1
                n_one_multi = n_one_multi + 1
                variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))]["one_multi"].append( ( passenger.trip_id, (first_leg.dep_key, second_leg.dep_key) ) )


                # We save the variables in the dictionary
                flight_variables[first_leg.dep_key]["2Leg"].append( ( passenger, (first_leg.dep_key, second_leg.dep_key) ) )
                flight_variables[second_leg.dep_key]["2Leg"].append( ( passenger, (first_leg.dep_key, second_leg.dep_key) ) )


    # Now we add the constraints that the passenger is only assigned to one flight
    local_constraint(variables_flight[(str(passenger.recloc), str(passenger.trip_number[0]))], penalty_combination = 1000)


# We print the total number of variables
print("Number of one_one: ", n_one_one)
print("Number of one_multi: ", n_one_multi)
print("Number of multi_one: ", n_multi_one)
print("Number of multi_multi: ", n_multi_multi)
print("Number of forced_one: ", n_forced_one)
print("Total number of variables: ", n_variables)

# Now we add the global constraints for the seats
seat_constraints(flight_variables, available_flights,  penalty_seats = int(1e8))

## Now solve the problem!!!
#sampler = dimod.SimulatedAnnealingSampler()
#samples = sampler.sample(bqm, num_reads = 200)

#best_sample = samples.first.sample
#best_energy = samples.first.energy