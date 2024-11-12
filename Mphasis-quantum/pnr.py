class PNR:
    def __init__(self, recloc, creation_dtz, cabin_cd, cos_cd, oper_od_orig_cd, oper_od_dest_cd, dep_key, 
                 dep_dt, orig_cd, dest_cd, flt_num, dep_dtml, arr_dtml, dep_dtmz, arr_dtmz, od_broken_ind, pax_cnt, 
                 cvm, conn_time_mins):
        self.recloc = recloc  # Record locator
        self.creation_dtz = creation_dtz  # PNR created date
        self.cabin_cd = cabin_cd  # Cabin code
        self.cos_cd = cos_cd  # Class code
        self.oper_od_orig_cd = oper_od_orig_cd  # Operating Origin Code
        self.oper_od_dest_cd = oper_od_dest_cd  # Operating Destination Code
        self.dep_key = dep_key  # Departure Key
        self.dep_dt = dep_dt  # Departure Date
        self.orig_cd = orig_cd  # Origin City Code
        self.dest_cd = dest_cd  # Destination City Code
        self.flt_num = flt_num  # Flight Number
        self.dep_dtml = dep_dtml  # Departure Datetime
        self.arr_dtml = arr_dtml  # Arrival Datetime
        self.dep_dtmz = dep_dtmz  # Departure Zulu Datetime
        self.arr_dtmz = arr_dtmz  # Arrival Zulu Datetime
        self.od_broken_ind = od_broken_ind  # Broken flight indicator
        self.pax_cnt = pax_cnt  # Passenger count
        self.cvm = cvm  # Customer value score
        self.conn_time_mins = conn_time_mins  # Connection time in minutes

    def __repr__(self):
        return f"PNR({self.dep_key}, {self.dep_dt},Time {self.dep_dtmz} -> {self.arr_dtmz} ,{self.cabin_cd}, {self.cos_cd}, {self.orig_cd} -> {self.dest_cd})"
