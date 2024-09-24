import pandas as pd
from airport import Airport
from flightnetwork import FlightNetwork
from geopy.distance import distance
import airportsdata as ad

AIRPORTS = ad.load('IATA')

def read_data(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename)
    return df

def convert_datetime(df: pd.DataFrame) -> pd.DataFrame:
    df['DEP_DTML'] = pd.to_datetime(df['DEP_DTML'])
    df['ARR_DTML'] = pd.to_datetime(df['ARR_DTML'])
    
    df['DEP_DTMZ'] = pd.to_datetime(df['DEP_DTMZ'])
    df['ARR_DTMZ'] = pd.to_datetime(df['ARR_DTMZ'])

    return df

def get_real_airports(flights: pd.DataFrame) -> set:
    real_airports = set()
    for _, flight in flights.iterrows():
        iata = flight['ORIG_CD']
        if iata in AIRPORTS:
            real_airports.add(iata)

    return real_airports

def create_airport_objects(real_airports: set) -> dict:
    airports = {}
    for iata in real_airports:
        airport_iata = AIRPORTS[iata].get('iata')
        name = AIRPORTS[iata].get('name')
        city = AIRPORTS[iata].get('city')
        lat = AIRPORTS[iata].get('lat')
        lon = AIRPORTS[iata].get('lon')
        airport = Airport(airport_iata, name, city, (lat, lon))
        airports[iata] = airport

    airports = get_nearby_airports(airports)
    return airports

def get_nearby_airports(airports: dict) -> dict:
    for key, airport in airports.items():
        coords = airport.coordinates
        for _, other_airport in airports.items():
            other_iata = other_airport.iata
            if other_iata != key:
                other_coords =other_airport.coordinates
                d = distance(coords, other_coords).kilometers
                if d <= 250:
                    airport.add_nearby_airport(other_airport.iata)

    return airports

def get_affected_passengers(pnr: pd.DataFrame, cancelled_flights: pd.DataFrame) -> pd.DataFrame:
    affected_passengers = pd.merge(pnr, cancelled_flights[['DEP_KEY']], on = 'DEP_KEY', how = 'inner')
    return affected_passengers

def get_alternative_flights(affected_passengers: pd.DataFrame, flights_network: FlightNetwork) -> dict:
    alternative_flights_dict = {}

    for _, passenger in affected_passengers.iterrows():
        recloc = passenger['RECLOC']
        source = passenger['OPER_OD_ORIG_CD']
        original_dep_time =passenger ['DEP_DTMZ'] #this might not work for connections i probably need to find the original dep time for the overall trip here
        destination = passenger['OPER_OD_DEST_CD']
        passenger_class = passenger['CABIN_CD']
        required_c_seats = abs(passenger['PAX_CNT']) if passenger_class == 'C' else 0
        required_y_seats = abs(passenger['PAX_CNT']) if passenger_class == 'Y' else 0
        original_dep_key = passenger['DEP_KEY']
        
        possible_routes = flights_network.find_all_valid_paths(source, destination, required_c_seats, required_y_seats, passenger_class, original_dep_time)
        key = (recloc, original_dep_key)
        alternative_flights_dict[key] = possible_routes

    return alternative_flights_dict


def initialize_flight_network(available_flights: pd.DataFrame) -> FlightNetwork:
    network = FlightNetwork()
    for _, row in available_flights.iterrows():
        network.add_flight(row['ORIG_CD'], row['DEST_CD'], row['DEP_DTMZ'], row['ARR_DTMZ'], abs(row['C_AVAIL_CNT']), abs(row['Y_AVAIL_CNT']), row['DEP_KEY'])
    return network

def main():
    pnr_filename = 'PRMI_DM_ALL_PNRs.csv'
    cancelled_filename = 'PRMI-DM_TARGET_FLIGHTS.csv'
    available_filename = 'PRMI-DM-AVAILABLE_FLIGHTS.csv'
    pnr = read_data(pnr_filename)
    cancelled_flights = read_data(cancelled_filename)
    available_flights = read_data(available_filename)

    pnr = convert_datetime(pnr)
    cancelled_flights = convert_datetime(cancelled_flights)
    available_flights = convert_datetime(available_flights)

    #was using this for keeping track of nearby airports but since the iata is encoded probably useless now (and the related functions)
    #real_airports_iatas = get_real_airports(cancelled_flights).union(get_real_airports(available_flights))
    #real_airports = create_airport_objects(real_airports_iatas)

    affected_passengers = get_affected_passengers(pnr, cancelled_flights)
    flights_network = initialize_flight_network(available_flights)
    alternative_flights = get_alternative_flights(affected_passengers, flights_network)
    flattened_data = [
            {'RECLOC': key[0], 'Original DEP_KEY': key[1], 'Path': path }
            for key, paths in alternative_flights.items()
            for path in paths
    ]
    df = pd.DataFrame(flattened_data)
    df.to_csv('alternative_flights.csv', index = False)


if __name__ == '__main__':
    main()
