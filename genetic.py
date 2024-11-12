import pandas as pd
import random
from datetime import timedelta

POPULATION_SIZE = 100  # Number of candidate solutions
GENERATIONS = 50  # Number of generations
MUTATION_RATE = 0.05  # Probability of mutation

def read_data(fname: str) -> pd.DataFrame:
    data = pd.read_csv(fname)
    data['Path'] = data['Path'].apply(eval)
    return data

def read_csv(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename)
    return df

def convert_datetime(df: pd.DataFrame) -> pd.DataFrame:
    df['DEP_DTML'] = pd.to_datetime(df['DEP_DTML'])
    df['ARR_DTML'] = pd.to_datetime(df['ARR_DTML'])
    
    df['DEP_DTMZ'] = pd.to_datetime(df['DEP_DTMZ'])
    df['ARR_DTMZ'] = pd.to_datetime(df['ARR_DTMZ'])

    return df

def create_flight_info(df):
    flight_info = {}
    for _, row in df.iterrows():
        flight_key = row['DEP_KEY']
        flight_info[flight_key] = {
            'DEP_DTMZ': row['DEP_DTMZ'],
            'seats_available': row['C_AVAIL_CNT'] + row['Y_AVAIL_CNT']
        }
    return flight_info

def calculate_delay_score(alternate_flight, original_flight, flight_info):
    original_departure = flight_info[original_flight]['DEP_DTMZ']
    first_leg_key = alternate_flight[0][0]
    alternate_departure = flight_info[first_leg_key]['DEP_DTMZ']

    delay_hours = (alternate_departure - original_departure)

    if delay_hours <= timedelta(hours = 6):
        return 70
    elif delay_hours <= timedelta(hours = 12):
        return 50
    elif delay_hours <= timedelta(hours = 24):
        return 40
    elif delay_hours <= timedelta(hours = 48):
        return 30
    else:
        return 0


def fitness(solution, passenger_df, flight_info):
    total_delay_score = 0
    total_passengers_reaccomodated = 0
    total_direct_flights = 0
    seats_remaining = {key: flight_info[key]['seats_available'] for key in flight_info}

    for i, row in passenger_df.iterrows():
        recloc = row['RECLOC']
        original_flight_key = row['Original DEP_KEY']
        alternate_flights = row['Path']

        delay_score = calculate_delay_score(alternate_flights, original_flight_key, flight_info)
        first_leg_key = alternate_flights[0][0]
        if seats_remaining[first_leg_key] > 0:
            seats_remaining[first_leg_key] -= 1 #this needs to change to the number of passengers
            total_delay_score += delay_score
            total_passengers_reaccomodated += 1 #again change to the number of passengers
        
            if len(alternate_flights) == 1:
                total_direct_flights += 1

    fitness_value = total_passengers_reaccomodated + (total_delay_score / len(passenger_df)) + (total_direct_flights * 2)
    return fitness_value

def initialize_population(passenger_df):
    population = []
    for _, row in passenger_df.iterrows():
        recloc = row['RECLOC']
        alternate_flights = row['Path']  
        individual = random.choice(alternate_flights)
        population.append({recloc: individual})

    return population

def select(population, passenger_df, flight_info):
    selected = []
    for _ in range(POPULATION_SIZE // 2):
        parent_1 = random.choice(population)
        parent_2 = random.choice(population)

        if fitness(parent_1, passenger_df, flight_info) > fitness(parent_2, passenger_df, flight_info):
            selected.append(parent_1)
        else:
            selected.append(parent_2)

    return selected

def crossover(parent_1, parent_2):
    child = {}
    all_reclocs = set(parent_1.keys()).union(set(parent_2.keys()))
    for recloc in all_reclocs:
        if recloc in parent_1 and recloc in parent_2:
            child[recloc] = random.choice([parent_1[recloc], parent_2[recloc]])
        elif recloc in parent_1:
            child[recloc] = parent_1[recloc]
        else:
            child[recloc] = parent_2[recloc]
    return child

def mutate(individual, passenger_df):
    for recloc in individual.keys():
        if random.random() < MUTATION_RATE:
            alternate_flights = passenger_df[passenger_df['RECLOC'] == recloc]['Path'].values[0]
            individual[recloc] = random.choice(alternate_flights)
    return individual

def genetic(passenger_df, flight_info):
    population = initialize_population(passenger_df)

    for generation in range(GENERATIONS):
        population_fitness = [(indiv, fitness(indiv, passenger_df, flight_info)) for indiv in population]
        population_fitness.sort(key = lambda x: x[1], reverse = True)
        print(f'Generation {generation}: Best Fitness = {population_fitness[0][1]}')

        selected_parents = select([indiv for indiv, _ in population_fitness], passenger_df, flight_info)

        next_generation = []
        while len(next_generation) < POPULATION_SIZE:
            parent_1, parent_2 = random.sample(selected_parents, 2)
            child = crossover(parent_1, parent_2)
            child = mutate(child, passenger_df)
            next_generation.append(child)

        population = next_generation

    best_individual = max(population, key = lambda indiv: fitness(indiv, passenger_df, flight_info))
    return best_individual

def main():
    fname = 'alternative_flights.csv'
    passenger_data = read_data(fname)

    cancelled_filename = 'PRMI-DM_TARGET_FLIGHTS.csv'
    available_filename = 'PRMI-DM-AVAILABLE_FLIGHTS.csv'
    cancelled_flights = read_csv(cancelled_filename)
    available_flights = read_csv(available_filename)
    cancelled_flights = convert_datetime(cancelled_flights)
    available_flights = convert_datetime(available_flights)
    
    available_flight_info = create_flight_info(available_flights)
    cancelled_flight_info = create_flight_info(cancelled_flights)
    flight_info = {**available_flight_info, **cancelled_flight_info}

    best_solution = genetic(passenger_data, flight_info)
    print(best_solution)

if __name__ == '__main__':
    main()