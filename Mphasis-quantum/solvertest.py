from solver import Solver
from graph import Graph
from pnr import PNR
import pandas as pd


def parse_data() -> tuple:
    flight_graph = Graph()

    # Path to the CSV file
    available_flights = 'Mphasis-quantum/data_files/PRMI-DM-AVAILABLE_FLIGHTS.csv'  
    cancelled_flights = 'Mphasis-quantum/data_files/PRMI-DM_TARGET_FLIGHTS_test.csv' 

    # Build the graph using the CSV file
    flight_graph.add_flights_from_csv(available_flights)
    flight_graph.add_cancelled_flights_from_csv(cancelled_flights)

    # Step 1: Load both CSV files
    target_flights_df = pd.read_csv("Mphasis-quantum/data_files/PRMI-DM_TARGET_FLIGHTS.csv")
    pnr_df = pd.read_csv("Mphasis-quantum/data_files/PRMI_DM_ALL_PNRs.csv")

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

    #this is only for testing VUY airports it should be done in general
    airport_code = "VUY"
    airport = flight_graph.get_airport(airport_code)
    available_flights_vuy = [flight for flight in airport.flights_out if flight.status == "available" and flight.dest_cd == "TPH"]



    pnrr_list = []
    for passenger in pnr_list:
        if (passenger.orig_cd == airport_code):
            pnrr_list.append(passenger)

    pnr_list = pnrr_list 

    pnr_list = pnr_list[:2]  # Limit the number of passengers for testing 
    available_flights_vuy = available_flights_vuy[:10]  # Limit the number of flights for testing

    return pnr_list, available_flights_vuy


def get_multileg_passengers(pnr_list: list):
    for passenger in pnr_list:
        #multi leg passenger on first leg
        if passenger.oper_od_dest_cd != passenger.dest_cd: 
            pass
        #multi leg passenger on second leg
        if passenger.oper_od_orig_cd != passenger.orig_cd: 

def run_airport_reaccomodation(flight_graph: Graph, pnr_list: list):
    solver = Solver()
    pass




def main():
    pnr, available_flights = parse_data()
    for p in pnr:
        print(p.orig_cd)


if __name__ == '__main__':
    main()
    