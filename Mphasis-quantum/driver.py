from data_processor import DataProcessor
from bqm_solver import BQMSolver


def main():
    available_flights = 'data_files/PRMI-DM-AVAILABLE_FLIGHTS.csv'
    cancelled_flights = 'data_files/PRMI-DM_TARGET_FLIGHTS_test.csv'
    target_flights_path = "data_files/PRMI-DM_TARGET_FLIGHTS.csv"
    pnr_path = "data_files/PRMI_DM_ALL_PNRs.csv"

    data_processor = DataProcessor()
    bqm_solver = BQMSolver()

    pnr_list, available_flights, flights_out_dic, flights_in_dic, flights_out_in_dic, flights_2legs_out_in_dic = data_processor.load_and_process_data(
        available_flights, cancelled_flights, target_flights_path, pnr_path)
    
    # Define CVM factors
    cvm_factor = {}
    cvm_factor["one_one"] = int(1e4)
    cvm_factor["one_multi"] = int(1e2)
    cvm_factor["multi_one"] = int(1e3)
    cvm_factor["multi_multi"] = int(1e1)
    cvm_factor["forced_one"] = int(1.5e3)

    best_sample, best_energy = bqm_solver.solve_reaccomodation(pnr_list, available_flights, flights_out_in_dic, flights_2legs_out_in_dic, cvm_factor)
    bqm_solver.process_results(best_sample, pnr_list, available_flights)


if __name__ == "__main__":
    main()