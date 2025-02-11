class Flight:
    def __init__(self, dep_key, dep_dt, orig_cd, dest_cd, flt_num, dep_dtml, arr_dtml,
                 dep_dtmz, arr_dtmz, c_cap_cnt, c_aul_cnt, c_pax_cnt, c_avail_cnt,
                 y_cap_cnt, y_aul_cnt, y_pax_cnt, y_avail_cnt,status):
        self.dep_key = dep_key
        self.dep_dt = dep_dt
        self.orig_cd = orig_cd
        self.dest_cd = dest_cd
        self.flt_num = flt_num
        self.dep_dtml = dep_dtml
        self.arr_dtml = arr_dtml
        self.dep_dtmz = dep_dtmz
        self.arr_dtmz = arr_dtmz
        self.c_cap_cnt = c_cap_cnt
        self.c_aul_cnt = c_aul_cnt
        self.c_pax_cnt = c_pax_cnt
        self.c_avail_cnt = c_avail_cnt
        self.y_cap_cnt = y_cap_cnt
        self.y_aul_cnt = y_aul_cnt
        self.y_pax_cnt = y_pax_cnt
        self.y_avail_cnt = y_avail_cnt
        self.status = status

    def __repr__(self):
        return (f"Flight {self.flt_num} ({self.orig_cd} -> {self.dest_cd}):\n"
                f"  Departure Date: {self.dep_dt}\n"
                f"  Departure Time (Local): {self.dep_dtml}, (Zulu): {self.dep_dtmz}\n"
                f"  Arrival Time (Local): {self.arr_dtml}, (Zulu): {self.arr_dtmz}\n"
                f"  Cabin C: Capacity: {self.c_cap_cnt}, Occupied: {self.c_aul_cnt}, Passengers: {self.c_pax_cnt}, Available: {self.c_avail_cnt}\n"
                f"  Cabin Y: Capacity: {self.y_cap_cnt}, Occupied: {self.y_aul_cnt}, Passengers: {self.y_pax_cnt}, Available: {self.y_avail_cnt}\n"
                f"  Departure Key: {self.dep_key}\n")