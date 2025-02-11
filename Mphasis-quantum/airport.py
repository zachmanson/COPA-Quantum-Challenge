# airport.py
class Airport:
    def __init__(self, code):
        self.code = code
        self.flights_out = []  # Flights departing from this airport
        self.flights_in = []   # Flights arriving at this airport

    def add_flight_out(self, flight):
        self.flights_out.append(flight)

    def add_flight_in(self, flight):
        self.flights_in.append(flight)
