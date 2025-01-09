import pandas as pd
from datetime import datetime
import itertools
from flight import Flight
from pnr import PNR
from graph import Graph  


class DataProcessor:
    def __init__(self):
        pass

    def load_and_process_data(
            self, 
            available_flights_path: str, cancelled_flights_path: str,
            target_flights_path: str, 
            pnr_path: str) -> tuple[list[PNR], list[Flight], dict[str, list[Flight]], dict[str, list[Flight]], dict[tuple[str, str], list[Flight]], dict[tuple[str, str], list[tuple[Flight, Flight]]]]:

        flight_graph = self._load_flight_graph(available_flights_path, cancelled_flights_path)
        target_flights_df, pnr_df = self._load_pnr_data(target_flights_path, pnr_path)
        matching_pnr_df = self._filter_pnr_data(target_flights_df, pnr_df)
        pnr_list = self._create_pnr_objects(matching_pnr_df, pnr_df)
        available_flights = self._create_flight_objects(available_flights_path)
        flights_out_dic, flights_in_dic, flights_out_in_dic, flights_2legs_out_in_dic = self._create_flight_dictionaries(available_flights)
        return pnr_list, available_flights, flights_out_dic, flights_in_dic, flights_out_in_dic, flights_2legs_out_in_dic


    def _load_flight_graph(self, available_flights_path: str, cancelled_flights_path: str) -> Graph:
       flight_graph = Graph() 
       flight_graph.add_flights_from_csv(available_flights_path)
       flight_graph.add_cancelled_flights_from_csv(cancelled_flights_path)
       return flight_graph

    def _load_pnr_data(self, target_flights_path: str, pnr_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        target_flights_df = pd.read_csv(target_flights_path)
        pnr_df = pd.read_csv(pnr_path)

        pnr_df = pnr_df.sort_values(by=["DEP_DTML"], ascending=[True])
        grouped = pnr_df.groupby(["RECLOC"])
        for rec, group1 in grouped:
             trip_number = 1
             grouped2 = group1.groupby(["OPER_OD_ORIG_CD", "OPER_OD_DEST_CD", "DEP_DT"])
             for (orig, dest, date), group2 in grouped2:
                pnr_df.loc[group2.index, "TRIP_NUMBER"] = int(trip_number)
                trip_number = trip_number + 1
        return target_flights_df, pnr_df

    def _filter_pnr_data(self, target_flights_df: pd.DataFrame, pnr_df: pd.DataFrame) -> pd.DataFrame:
        target_dep_keys = target_flights_df['DEP_KEY'].unique()
        matching_pnr_df = pnr_df[pnr_df['DEP_KEY'].isin(target_dep_keys)]
        return matching_pnr_df

    def _create_pnr_objects(self, matching_pnr_df: pd.DataFrame, pnr_df: pd.DataFrame) -> list[PNR]:
        pnr_list_1leg = []
        pnr_list_2leg = []
        pnr_list = []

        group = matching_pnr_df.groupby(["RECLOC", "TRIP_NUMBER"])

        for rec_and_trpnr, inner_group in group:
            recloc = rec_and_trpnr[0]
            trip_number = int( rec_and_trpnr[1] )

            selected_pnr = pnr_df[(pnr_df["RECLOC"] == recloc) & (pnr_df["TRIP_NUMBER"] == trip_number)]

            for ktrip, row in inner_group.iterrows():
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

                if ((pnr.oper_od_orig_cd == pnr.orig_cd) & (pnr.oper_od_orig_cd == pnr.orig_cd)):
                    pnr.booked_multi_leg = False

                    pnr.ideal_dep_dtmz = pnr.dep_dtmz
                    pnr.ideal_dep_dtml = pnr.dep_dtml

                    pnr.ideal_arr_dtmz = pnr.arr_dtmz
                    pnr.ideal_arr_dtml = pnr.arr_dtml
                else:
                    pnr.booked_multi_leg = True

                    pnr.ideal_dep_dtmz = min(selected_pnr["DEP_DTMZ"])
                    pnr.ideal_dep_dtml = min(selected_pnr["DEP_DTML"])
                    pnr.ideal_arr_dtmz = max(selected_pnr["ARR_DTMZ"])
                    pnr.ideal_arr_dtml = max(selected_pnr["ARR_DTML"])


                if len(group) == 1:
                    pnr_list_1leg.append(pnr)
                    pnr.trip_multi_leg = False
                elif len(group) == 2:
                    pnr_list_2leg.append(pnr)
                    pnr.trip_multi_leg = True

                pnr_list.append(pnr)
        return pnr_list

    def _create_flight_objects(self, available_flights_path: str) -> list[Flight]:
        available_flights_df = pd.read_csv(available_flights_path)
        available_flights = []
        for _, row in available_flights_df.iterrows():
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
                status = True
            )
            available_flights.append(flight)
        return available_flights
    
    def _create_flight_dictionaries(self, available_flights: list[Flight]) -> tuple[dict[str, list[Flight]], dict[str, list[Flight]], dict[tuple[str,str], list[Flight]], dict[tuple[str,str], list[tuple[Flight, Flight]]]]:
        flights_out_dic: dict[str, list[Flight]] = {}
        flights_in_dic: dict[str, list[Flight]] = {}
        flights_out_in_dic: dict[tuple[str, str], list[Flight]] = {}
        flights_2legs_out_in_dic: dict[tuple[str, str], list[tuple[Flight, Flight]]] = {}
        
        orig_keys = set([flight.orig_cd for flight in available_flights])
        dest_keys = set([flight.dest_cd for flight in available_flights])
        
        for orig_key in orig_keys:
            flights_out_dic[str(orig_key)] = []
        
        for dest_key in dest_keys:
            flights_in_dic[str(dest_key)] = []

        combinations = list(itertools.product(orig_keys, dest_keys))
        for combination in combinations:
            flights_out_in_dic[(str(combination[0]), str(combination[1]))] = []
            flights_2legs_out_in_dic[(str(combination[0]), str(combination[1]))] = []

        for flight in available_flights:
            flights_out_dic[str(flight.orig_cd)].append(flight)
            flights_in_dic[str(flight.dest_cd)].append(flight)
            flights_out_in_dic[(str(flight.orig_cd), str(flight.dest_cd))].append(flight)

        for combination in combinations:
             first_legs = flights_out_dic[str(combination[0])]
             second_legs = flights_in_dic[str(combination[1])]

             for first_leg in first_legs:
                    for second_leg in second_legs:
                        if (first_leg.dest_cd != second_leg.orig_cd):
                            continue
                    
                        first_leg_arr = datetime.strptime(first_leg.arr_dtmz, "%Y-%m-%d %H:%M:%S")
                        second_leg_dep = datetime.strptime(second_leg.dep_dtmz, "%Y-%m-%d %H:%M:%S")
                        conn_time = (second_leg_dep - first_leg_arr).total_seconds() / 60.0
                        
                        if ((conn_time <= 60) or (720 <= conn_time)):
                            continue
                        else:
                            flights_2legs_out_in_dic[(str(combination[0]), str(combination[1]))].append((first_leg, second_leg))
        return flights_out_dic, flights_in_dic, flights_out_in_dic, flights_2legs_out_in_dic