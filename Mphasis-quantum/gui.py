import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import random
import time
from itertools import islice
import customtkinter as ctk

class ReaccomGUI(ctk.CTk):
    def __init__(self, csv_path: str):
        super().__init__()
        self.title("COPA Reaccommodation Results")
        self.geometry("775x390")
        self.csv_path = csv_path
        self.data_1leg, self.data_2leg = self._parse_data()
        print(f"Data loaded - 1leg: {len(self.data_1leg)} rows, 2leg: {len(self.data_2leg)} rows")
        self.loading_symbol = None
        self.current_theme = "light"
        self.results_displayed = False
        
        dir = os.path.dirname(os.path.abspath(__file__))
        full_csv_file = os.path.join(dir, 'MkIII.I_sd_sd_D6.csv')  # Updated CSV filename
        self.full_csv_path = full_csv_file
        self.full_data = self._parse_full_data()

        # Create main container for results
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=20, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()
        self._apply_styles()

    def _parse_data(self) -> tuple[dict[str, str], dict[str, str]]:
         single_leg_data = {}
         two_leg_data = {}
         current_section = None  # Tracks whether we are in single leg or two leg section
         
         with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            next(reader)
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
                            accuracy = row[12].strip()
                            if accuracy and accuracy != "N/A":
                                single_leg_data["Accuracy"] = float(accuracy.replace('%', ''))
                            else:
                                single_leg_data["Accuracy"] = "N/A"
                            single_leg_data["Qubits"] = int(row[13]) if row[13] else 0


                        elif current_section == "two":
                            two_leg_data["Cancelled PNRs"] = int(row[3]) if row[3] else 0
                            two_leg_data["Cancelled Passengers"] = int(row[4]) if row[4] else 0
                            two_leg_data["Reccomodated PNRs"] = int(row[5]) if row[5] else 0
                            two_leg_data["Reaccomodated Seats"] = int(row[6]) if row[6] else 0
                            two_leg_data["Overbooked Seats"] = int(row[7]) if row[7] else 0
                            two_leg_data["Multiple Bookings"] = int(row[8]) if row[8] else 0
                            accuracy = row[12].strip()
                            if accuracy and accuracy != "N/A":
                                two_leg_data["Accuracy"] = float(accuracy.replace('%', ''))
                            else:
                                two_leg_data["Accuracy"] = "N/A"
                            two_leg_data["Qubits"] = int(row[13]) if row[13] else 0
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing row: {row}. Error: {e}")
                        continue

         return single_leg_data, two_leg_data

    def _parse_full_data(self) -> list[list[str]]:
        """Parses all of the data from the CSV."""
        full_data = []
        with open(self.full_csv_path, 'r', encoding = "utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                full_data.append(row)
        return full_data

    def create_widgets(self) -> None:
        # Title
        title_label = ctk.CTkLabel(self, text="COPA Reaccommodation Analysis", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=20, sticky="ew", padx=20)

        # Slider Frame
        slider_frame = ctk.CTkFrame(self, corner_radius=10)
        slider_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Optimization Time Slider
        self.optimization_time_value = tk.IntVar(value=0)  # Initialize to 0 minutes
        self.optimization_time_slider = ctk.CTkSlider(slider_frame, from_=0, to=10, orientation="horizontal", width=200,
                                                       command=self._update_optimization_time, variable = self.optimization_time_value)
        self.optimization_time_slider.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.optimization_time_label = ctk.CTkLabel(slider_frame, text="Optimization Time: 0 mins", font=("Arial", 12, "bold"))
        self.optimization_time_label.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        slider_frame_label = ctk.CTkLabel(slider_frame, text="Parameters", font=("Arial", 14, "bold"))
        slider_frame_label.grid(row=0, column=2, padx=10, pady=5)

        # Run button
        self.run_button = ctk.CTkButton(self, text="Run", command=self._simulate_run, font=("Arial", 14, "bold"))
        self.run_button.grid(row=1, column=1, sticky="e", padx=20, pady=10)

        # Theme Switcher
        theme_switch_frame = ctk.CTkFrame(self, corner_radius=10)
        theme_switch_frame.grid(row=1, column=3, sticky="ne", padx=20, pady=10)
        self.theme_switch_label = ctk.CTkLabel(theme_switch_frame, text="Theme Mode:")
        self.theme_switch_label.grid(row=0, column=0, padx=5, pady=5)
        self.theme_switch = ctk.CTkSwitch(theme_switch_frame, text="", command=self._toggle_theme, onvalue="dark", offvalue="light")
        self.theme_switch.grid(row=0, column=1, padx=5, pady=5, sticky="e")

    def _apply_styles(self) -> None:
       ctk.set_appearance_mode(self.current_theme)

    def _create_labels(self, results_window: ctk.CTkToplevel) -> None:
        try:
            # Headers
            headers_1leg = ["Cancelled PNRs", "Cancelled Passengers", "Reccomodated PNRs", "Reaccomodated Seats", "Overbooked Seats", "Multiple Bookings", "Accuracy", "Qubits"]
            headers_2leg = ["Cancelled PNRs", "Cancelled Passengers", "Reccomodated PNRs", "Reaccomodated Seats", "Overbooked Seats", "Multiple Bookings", "Accuracy", "Qubits"]
            
            # Setup grid weight for centering purposes (only for header rows)
            for col in range(len(headers_1leg)):
                results_window.grid_columnconfigure(col, weight=1)
            
            # Create header labels for single leg
            ctk.CTkLabel(results_window, text="Single Leg Flight Data", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=len(headers_1leg), padx=10, pady=10, sticky="ew")
            for col, header in enumerate(headers_1leg):
                ctk.CTkLabel(results_window, text=header, font=("Arial", 14, "bold")).grid(row=1, column=col, padx=5, pady=5, sticky="ew")

            # Populate data for single leg
            if self.data_1leg:
                for col, header in enumerate(headers_1leg):
                    value = str(self.data_1leg.get(header, "N/A"))
                    ctk.CTkLabel(results_window, text=value, font=("Arial", 12)).grid(row=2, column=col, padx=5, pady=5, sticky="ew")

            # Setup grid weight for centering purposes (only for header rows)
            for col in range(len(headers_2leg)):
                results_window.grid_columnconfigure(col, weight=1)
            
             # Create header labels for two leg data
            ctk.CTkLabel(results_window, text="Two Leg Flight Data", font=("Arial", 16, "bold")).grid(row=3, column=0, columnspan=len(headers_2leg), padx=10, pady=10, sticky="ew")
            for col, header in enumerate(headers_2leg):
                 ctk.CTkLabel(results_window, text=header, font=("Arial", 14, "bold")).grid(row=4, column=col, padx=5, pady=5, sticky="ew")
                

            # Populate data for two legs
            if self.data_2leg:
                 for col, header in enumerate(headers_2leg):
                     value = str(self.data_2leg.get(header, "N/A"))
                     ctk.CTkLabel(results_window, text=value, font=("Arial", 12)).grid(row=5, column=col, padx=5, pady=5, sticky="ew")
        
        except Exception as e:
            print(f"Error creating labels: {e}")
            error_label = ctk.CTkLabel(results_window, text=f"Error displaying results: {e}")
            error_label.pack(padx=10, pady=10)

    def _create_csv_view(self, results_window: ctk.CTkToplevel) -> None:
        """Creates and displays a new window with all the CSV data using Treeview with search and sorting."""
        try:
            if self.full_data:
                # Create a frame for search input and button
                search_frame = ctk.CTkFrame(results_window)
                search_frame.pack(pady=5, padx=5, fill="x")

                # Search Entry
                self.search_entry = ctk.CTkEntry(search_frame)
                self.search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

                # Search Button
                search_button = ctk.CTkButton(search_frame, text="Search", command=self._search_treeview)
                search_button.pack(side=tk.LEFT, padx=5)

                # Create Treeview widget
                self.tree = ttk.Treeview(results_window, show="headings")
                self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                # Add Scrollbars
                vscroll = ttk.Scrollbar(results_window, orient="vertical", command=self.tree.yview)
                vscroll.pack(side=tk.RIGHT, fill="y")
                self.tree.configure(yscrollcommand=vscroll.set)

                hscroll = ttk.Scrollbar(results_window, orient="horizontal", command=self.tree.xview)
                hscroll.pack(side=tk.BOTTOM, fill="x")
                self.tree.configure(xscrollcommand=hscroll.set)
                
                # Define columns
                column_names = self.full_data[0]  # Assuming first row is the header
                self.tree["columns"] = column_names

                # Store sorting state for each column (None: not sorted, True: ascending, False: descending)
                self.sort_states = {col: None for col in column_names}

                # Format columns (adjust width as needed)
                for col in column_names:
                    self.tree.column(col, width=150, anchor="w")  # Set initial width and anchor
                    self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))  # Add sorting command

                # Store all data to restore after search
                self.all_data = self.full_data[1:]
                self._populate_treeview(self.all_data)

        except Exception as e:
            messagebox.showerror("Error", f"Error parsing CSV file: {e}")
            print(f"Error creating CSV view: {e}")
            error_label = ctk.CTkLabel(results_window, text=f"Error displaying CSV view: {e}")
            error_label.pack(padx=10, pady=10)

    def _populate_treeview(self, data):
        # Clear existing data in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for row in data:
            self.tree.insert("", tk.END, values=row)

    def _search_treeview(self):
        search_text = self.search_entry.get().lower()  # Convert search text to lowercase
        filtered_data = []

        for row in self.all_data:
            # Check if any of the values in the row contains the search text
            if any(search_text in str(value).lower() for value in row):
                filtered_data.append(row)

        self._populate_treeview(filtered_data)

    def _sort_column(self, col):
        """Sorts the treeview by the specified column."""
        current_state = self.sort_states[col]

        if current_state is None:  # Not sorted yet -> sort ascending
            reverse = False
            self.sort_states[col] = True
        elif current_state is True:  # Sorted ascending -> sort descending
            reverse = True
            self.sort_states[col] = False
        else:  # Sorted descending -> no sorting
            reverse = False
            self.sort_states[col] = None # Return to unsorted
            self._populate_treeview(self.all_data) #Repopulate with original data
            return

        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        
        # Sort based on data type (numeric or string)
        try:
            data.sort(key=lambda x: float(x[0]), reverse=reverse)  # Try sorting as float
        except ValueError:
            data.sort(reverse=reverse)  # If float conversion fails, sort as string

        for index, (values, child) in enumerate(data):
            self.tree.move(child, "", index)  # Reorder items in treeview


    def _update_optimization_time(self, value: float) -> None:
        """Updates the optimization time label with the current slider value."""
        minutes = int(value)
        self.optimization_time_label.configure(text=f"Optimization Time: {minutes} mins")
        self.optimization_time_label.configure(font=("Arial", 12, "bold"))  # Make label bold

    def _simulate_run(self) -> None:
        # Disable button during simulation
        self.run_button.configure(state="disabled")
        
        # Loading symbol
        self.loading_symbol = ttk.Progressbar(self.main_container, mode="indeterminate", length=200)
        self.loading_symbol.grid(row = 0, column = 0, columnspan = 4, padx = 20, pady = 10, sticky="ew")
        self.loading_symbol.start()

        # Get optimization time from slider
        optimization_time = self.optimization_time_value.get()  # get the value from tk.IntVar

        # Simulate time and display results in another thread
        wait_time_ms = int(random.uniform(4000, 6000) + (optimization_time * 1000))  # Add optimization time in milliseconds
        self.after(wait_time_ms, self._display_results)

    def _display_results(self) -> None:
        # Stop loading and re-enable the button
        if self.loading_symbol:
            self.loading_symbol.stop()
            self.loading_symbol.destroy()
            self.loading_symbol = None
        self.run_button.configure(state="normal")
        
        # Display results in new window
        results_window = ctk.CTkToplevel(self)
        results_window.title("Reaccomodation Results")
        results_window.geometry("1000x300")
        self._create_labels(results_window)
        results_window.grid_columnconfigure(0, weight=1)
        results_window.grid_rowconfigure(0, weight=1)

        # Create new window for csv
        csv_window = ctk.CTkToplevel(self)
        csv_window.title("Full CSV Data")
        csv_window.geometry("1200x500")
        self._create_csv_view(csv_window)

    def _toggle_theme(self) -> None:
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        ctk.set_appearance_mode(self.current_theme)

def main() -> None:
    dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(dir, 'Mphasis Hackathon.csv')
    app = ReaccomGUI(csv_file)
    app.mainloop()

if __name__ == "__main__":
    main()