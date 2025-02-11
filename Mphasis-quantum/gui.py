import tkinter as tk
from tkinter import ttk
import csv
import os
import random
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ReaccomGUI(ctk.CTk):
    def __init__(self, csv_path: str):
        super().__init__()
        self.title("COPA Reaccommodation Analysis")
        self.geometry("900x600")  # Adjusted height
        self.csv_path = csv_path
        self.loading_symbol = None
        self.current_theme = "light"

        dir = os.path.dirname(os.path.abspath(__file__))
        full_csv_file = os.path.join(dir, 'MkIII.I_sd_sd_D6.csv')
        self.full_csv_path = full_csv_file
        self.full_data = self._parse_full_data()
        self.csv_window = None

        # Initialize the results
        self.total_bookings = 43811
        self.total_cancellations = 15094
        self.candidate_flights = 2360
        self.reaccomodated_cancellations = 7574
        self.reaccomodation_rate = 50.1
        self.total_runtime = 83

        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=20, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self._apply_styles()

    def _parse_data(self) -> tuple[dict[str, str], dict[str, str]]:
        # Mphasis Hackathon.csv values no longer used here so return empty
        return {}, {}

    def _parse_full_data(self) -> list[list[str]]:
        """Parses all of the data from the CSV."""
        full_data = []
        with open(self.full_csv_path, 'r', encoding='utf-8') as f:
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
        self.optimization_time_value = tk.IntVar(value=0)
        self.optimization_time_slider = ctk.CTkSlider(slider_frame, from_=0, to=10, orientation="horizontal", width=200,
                                                       command=self._update_optimization_time,
                                                       variable=self.optimization_time_value)
        self.optimization_time_slider.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.optimization_time_label = ctk.CTkLabel(slider_frame, text="Optimization Time: 0 mins",
                                                     font=("Arial", 12, "bold"))
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
        self.theme_switch = ctk.CTkSwitch(theme_switch_frame, text="", command=self._toggle_theme, onvalue="dark",
                                          offvalue="light")
        self.theme_switch.grid(row=0, column=1, padx=5, pady=5, sticky="e")

         # Results Frame
        self.results_frame = ctk.CTkFrame(self.main_container)
        self.results_frame.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.results_frame.grid_columnconfigure(0, weight=1) # Label Column
        self.results_frame.grid_columnconfigure(1, weight=1) # Value column

         # Result Labels, Values are initially empty.
        self.total_bookings_label = ctk.CTkLabel(self.results_frame, text="Total Bookings:", font=("Arial", 14, "bold"))
        self.total_bookings_label.grid(row=0, column=0, padx=10, pady=2, sticky="e")
        self.total_bookings_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.total_bookings_value_label.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        self.total_cancellations_label = ctk.CTkLabel(self.results_frame, text="Total Cancellations:", font=("Arial", 14, "bold"))
        self.total_cancellations_label.grid(row=1, column=0, padx=10, pady=2, sticky="e")
        self.total_cancellations_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.total_cancellations_value_label.grid(row=1, column=1, padx=10, pady=2, sticky="w")

        self.candidate_flights_label = ctk.CTkLabel(self.results_frame, text="Candidate Flights:", font=("Arial", 14, "bold"))
        self.candidate_flights_label.grid(row=2, column=0, padx=10, pady=2, sticky="e")
        self.candidate_flights_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.candidate_flights_value_label.grid(row=2, column=1, padx=10, pady=2, sticky="w")

        self.reaccomodated_cancellations_label = ctk.CTkLabel(self.results_frame, text="Reaccomodated Cancellations:", font=("Arial", 14, "bold"))
        self.reaccomodated_cancellations_label.grid(row=3, column=0, padx=10, pady=2, sticky="e")
        self.reaccomodated_cancellations_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.reaccomodated_cancellations_value_label.grid(row=3, column=1, padx=10, pady=2, sticky="w")

        self.reaccomodation_rate_label = ctk.CTkLabel(self.results_frame, text="Reaccomodation Rate:", font=("Arial", 14, "bold"))
        self.reaccomodation_rate_label.grid(row=4, column=0, padx=10, pady=2, sticky="e")
        self.reaccomodation_rate_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.reaccomodation_rate_value_label.grid(row=4, column=1, padx=10, pady=2, sticky="w")

        self.total_runtime_label = ctk.CTkLabel(self.results_frame, text="Total Runtime:", font=("Arial", 14, "bold"))
        self.total_runtime_label.grid(row=5, column=0, padx=10, pady=2, sticky="e")
        self.total_runtime_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.total_runtime_value_label.grid(row=5, column=1, padx=10, pady=2, sticky="w")
        
        #Pie chart canvas
        self.pie_chart_frame = ctk.CTkFrame(self.main_container)
        self.pie_chart_frame.grid(row=6, column = 0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.pie_chart_frame.grid_remove() # Hide Initially


    def _apply_styles(self) -> None:
        ctk.set_appearance_mode(self.current_theme)
    def create_pie_chart(self):
        """Creates and displays the pie chart."""
        # Data for the pie chart
        labels = ['Reaccomodated', 'Not Reaccomodated']
        sizes = [self.reaccomodation_rate, 100 - self.reaccomodation_rate]  # Calculate 'Not Reaccomodated'

        # Create a Figure
        fig = Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Create the pie chart
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title("Reaccommodation Rate", fontdict={'fontsize': 14})
        
        # Embed the Matplotlib Figure in the Tkinter widget
        self.canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
    def _create_csv_view(self, csv_window: ctk.CTkToplevel) -> None:
        """Creates and displays a new window with all the CSV data using Treeview with search and sorting."""
        try:
            if self.full_data:
                # Create a frame for search input and button
                search_frame = ctk.CTkFrame(csv_window)
                search_frame.pack(pady=5, padx=5, fill="x")

                # Search Entry
                self.search_entry = ctk.CTkEntry(search_frame)
                self.search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

                # Search Button
                search_button = ctk.CTkButton(search_frame, text="Search", command=self._search_treeview)
                search_button.pack(side=tk.LEFT, padx=5)

                # Create Treeview widget
                self.tree = ttk.Treeview(csv_window, show="headings")
                self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                # Add Scrollbars
                vscroll = ttk.Scrollbar(csv_window, orient="vertical", command=self.tree.yview)
                vscroll.pack(side=tk.RIGHT, fill="y")
                self.tree.configure(yscrollcommand=vscroll.set)

                hscroll = ttk.Scrollbar(csv_window, orient="horizontal", command=self.tree.xview)
                hscroll.pack(side=tk.BOTTOM, fill="x")
                self.tree.configure(xscrollcommand=hscroll.set)
                
                # Define columns
                column_names = self.full_data[0]  # Assuming first row is the header
                self.tree["columns"] = column_names

                # Store sorting state for each column (None: not sorted, True: ascending, False: descending)
                self.sort_states = {col: None for col in column_names}

                # Format columns
                for col in column_names:
                    self.tree.column(col, width=150, anchor="w")
                    self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))

                # Store all data to restore after search
                self.all_data = self.full_data[1:]
                self._populate_treeview(self.all_data)

        except Exception as e:
            messagebox.showerror("Error", f"Error parsing CSV file: {e}")
            print(f"Error creating CSV view: {e}")
            error_label = ctk.CTkLabel(csv_window, text=f"Error displaying CSV view: {e}")
            error_label.pack(padx=10, pady=10)

    def _populate_treeview(self, data):
        # Clear existing data in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for row in data:
            self.tree.insert("", tk.END, values=row)

    def _search_treeview(self):
        search_text = self.search_entry.get().lower()
        filtered_data = []

        for row in self.all_data:
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
        self.loading_symbol.grid(row = 1, column = 1, columnspan = 1, padx = 20, pady = 10, sticky="ew")
        self.loading_symbol.start()

        # Get optimization time from slider
        optimization_time = self.optimization_time_value.get()  # get the value from tk.IntVar

        # Simulate time and display results in another thread
        #wait_time_ms = int(random.uniform(4000, 6000) + (optimization_time * 1))  # Add optimization time in milliseconds
        wait_time_ms = int(random.uniform(max(0, optimization_time - 30000), optimization_time + 30000))
        self.after(wait_time_ms, self._display_results)

    def _display_results(self) -> None:
        # Stop loading and re-enable the button
        if self.loading_symbol:
            self.loading_symbol.stop()
            self.loading_symbol.destroy()
            self.loading_symbol = None
        self.run_button.configure(state="normal")
        
        # Display results on labels
        self.total_bookings_value_label.configure(text=f"{self.total_bookings}")
        self.total_cancellations_value_label.configure(text=f"{self.total_cancellations}")
        self.candidate_flights_value_label.configure(text=f"{self.candidate_flights}")
        self.reaccomodated_cancellations_value_label.configure(text=f"{self.reaccomodated_cancellations}")
        self.reaccomodation_rate_value_label.configure(text=f"{self.reaccomodation_rate}%")
        self.total_runtime_value_label.configure(text=f"{self.total_runtime} mins")
        
        # Show Pie Chart
        self.create_pie_chart() #create the Pie Chart
        self.pie_chart_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        # Create new window for csv
        if self.csv_window is None:
            self.csv_window = ctk.CTkToplevel(self)
            self.csv_window.title("Full CSV Data")
            self.csv_window.geometry("1200x500")
            self._create_csv_view(self.csv_window)

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