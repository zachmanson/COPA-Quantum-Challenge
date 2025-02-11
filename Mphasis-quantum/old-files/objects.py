class Flight:
    def __init__(self, flight_id, dep_key, origin, destination, dep_datetime, arr_datetime, c_avail_cnt, y_avail_cnt, status):
        self.flight_id = flight_id
        self.dep_key = dep_key
        self.origin = origin
        self.destination = destination
        self.dep_datetime = dep_datetime
        self.arr_datetime = arr_datetime
        self.c_avail_cnt = c_avail_cnt
        self.y_avail_cnt = y_avail_cnt
        self.status = status

    def is_available(self):
        return self.status == "Available"

    def book_seat(self, cabin_class, num_seats=1):
        if cabin_class == "C" and self.c_avail_cnt >= num_seats:
            self.c_avail_cnt -= num_seats
            return True
        elif cabin_class == "Y" and self.y_avail_cnt >= num_seats:
            self.y_avail_cnt -= num_seats
            return True
        return False


class Passenger:
    def __init__(self, pnr, original_flight_id, pax_cnt, cabin_class, cvm):
        self.pnr = pnr
        self.original_flight_id = original_flight_id
        self.pax_cnt = pax_cnt
        self.cabin_class = cabin_class
        self.cvm = cvm
        self.reaccommodated = False

    def mark_reaccommodated(self):
        self.reaccommodated = True


        
class FlightGraph:
    def __init__(self):
        self.graph = {}

    def add_flight(self, origin, destination, flight):
        if origin not in self.graph:
            self.graph[origin] = []
        self.graph[origin].append((destination, flight))

    def get_connections(self, origin):
        return self.graph.get(origin, [])
