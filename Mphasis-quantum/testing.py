import os
import csv

dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(dir, 'Mphasis Hackathon.csv')

def parse_csv(filename):
    """Parses the given CSV file and extracts relevant data for single and two-legged flights."""

    single_leg_data = {}
    two_leg_data = {}
    current_section = None  # Tracks whether we are in single leg or two leg section

    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Handle section headers
            if "Cancellations in single legged flights" in "".join(row):
                current_section = "single"
                continue
            if "Single leg cancellations in 2 legged flights" in "".join(row):
                current_section = "two"
                continue

            # Process data rows
            if row and len(row) > 2 and row[1].strip() == "ALL":
                try:
                    if current_section == "single":
                        single_leg_data["Cancelled PNRs"] = int(row[3]) if row[3] else 0
                        single_leg_data["Cancelled Passengers"] = int(row[4]) if row[4] else 0
                        single_leg_data["Reccomodated PNRs"] = int(row[5]) if row[5] else 0
                        single_leg_data["Reaccomodated Seats"] = int(row[6]) if row[6] else 0
                        single_leg_data["Overbooked Seats"] = int(row[7]) if row[7] else 0
                        single_leg_data["Multiple Bookings"] = int(row[8]) if row[8] else 0
                        accuracy = row[12].strip() # Corrected index
                        if accuracy and accuracy != "N/A":
                            single_leg_data["Accuracy"] = float(accuracy.replace('%', ''))
                        else:
                            single_leg_data["Accuracy"] = "N/A"
                        single_leg_data["Qubits"] = int(row[13]) if row[13] else 0 # Corrected index



                    elif current_section == "two":
                        two_leg_data["Cancelled PNRs"] = int(row[3]) if row[3] else 0
                        two_leg_data["Cancelled Passengers"] = int(row[4]) if row[4] else 0
                        two_leg_data["Reccomodated PNRs"] = int(row[5]) if row[5] else 0
                        two_leg_data["Reaccomodated Seats"] = int(row[6]) if row[6] else 0
                        two_leg_data["Overbooked Seats"] = int(row[7]) if row[7] else 0
                        two_leg_data["Multiple Bookings"] = int(row[8]) if row[8] else 0
                        accuracy = row[12].strip() # Corrected Index
                        if accuracy and accuracy != "N/A":
                            two_leg_data["Accuracy"] = float(accuracy.replace('%', ''))
                        else:
                            two_leg_data["Accuracy"] = "N/A"
                        two_leg_data["Qubits"] = int(row[13]) if row[13] else 0 # Corrected index
                except (ValueError, IndexError) as e:
                    print(f"Error parsing row: {row}. Error: {e}")
                    continue

    return single_leg_data, two_leg_data

single_leg_data, two_leg_data = parse_csv(csv_file)
print(single_leg_data, two_leg_data)