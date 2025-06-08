import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt  # Import pyplot for subplots
from matplotlib import colors as mcolors
import numpy as np
from datetime import datetime

class ReaccomGUI(ctk.CTk):
    def __init__(self, csv_path: str):
        super().__init__()
        self.title("COPA Reaccommodation Analysis")
        self.geometry("900x650")
        self.csv_path = csv_path
        self.loading_symbol = None
        ctk.set_appearance_mode("system")
        self.current_theme = ctk.get_appearance_mode()

        try:
            dir_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            dir_path = os.getcwd()

        full_csv_file = os.path.join(dir_path, 'Results_DWAVE.csv')
        self.full_csv_path = full_csv_file
        try:
            self.full_data = self._parse_full_data()
        except FileNotFoundError:
            messagebox.showerror("Error", f"CSV file not found: {self.full_csv_path}")
            self.full_data = [['Error'], ['File not found']]
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {e}")
            self.full_data = [['Error'], [f'Could not read file: {e}']]

        self.csv_window = None
        self.graph_window = None
        self.canvas = None

        self.total_cancellations = 15096
        self.reaccomodated_passengers = 8606
        self.num_reaccomodations = 11693
        self.feasible_reaccomodations = 11693
        self.reaccomodation_rate = 57.0084
        self.total_runtime = 16
        self.num_variables = 125452

        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=20, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.create_widgets()

    def _parse_data(self) -> tuple[dict[str, str], dict[str, str]]:
        return {}, {}

    def _parse_full_data(self) -> list[list[str]]:
        full_data = []
        if not os.path.exists(self.full_csv_path):
             raise FileNotFoundError(f"CSV file not found at path: {self.full_csv_path}")

        with open(self.full_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
                full_data.append(header)
                for row in reader:
                    full_data.append(row)
            except StopIteration:
                full_data.append(['Info'])
            except Exception as e:
                raise

        if not full_data or len(full_data) < 2:
            if not full_data: full_data.append(['Info'])

        return full_data

    def _prepare_cvm_plot_data(self):
        reaccom_cvms = []
        if not self.full_data or len(self.full_data) < 2:
            return None, None

        header = self.full_data[0]
        header_lower = [h.lower() for h in header]

        try:
            cvm_idx = header_lower.index('cvm')
            alt_dep_key_idx = header_lower.index('alt_dep_key')
        except ValueError:
            messagebox.showerror("CSV Error", "A required column (CVM or ALT_DEP_KEY) was not found in Results_DWAVE.csv.")
            return None, None

        for row in self.full_data[1:]:
            if len(row) > alt_dep_key_idx and row[alt_dep_key_idx].strip():
                try:
                    cvm_value = float(row[cvm_idx])
                    reaccom_cvms.append(cvm_value)
                except (ValueError, TypeError):
                    continue
        
        if not reaccom_cvms:
            messagebox.showinfo("Info", "No re-accommodated passengers with valid CVM found.")
            return None, None

        num_bins = 15
        counts, bin_edges = np.histogram(reaccom_cvms, bins=num_bins)
        bin_labels = [f"{bin_edges[i]:.3f} - {bin_edges[i+1]:.3f}" for i in range(len(counts))]
        
        return bin_labels, counts

    def _prepare_delay_plot_data(self):
        delays_in_hours = []
        if not self.full_data or len(self.full_data) < 2:
            return None, None

        header = self.full_data[0]
        header_lower = [h.lower() for h in header]

        try:
            orig_dep_idx = header_lower.index('dep_dtmz')
            alt_dep_idx = header_lower.index('alt_dep_dtmz')
            alt_dep_key_idx = header_lower.index('alt_dep_key')
        except ValueError:
            messagebox.showerror("CSV Error", "A required column (DEP_DTMZ, ALT_DEP_DTMZ, or ALT_DEP_KEY) was not found.")
            return None, None

        date_format = "%Y-%m-%d %H:%M"
        
        for row in self.full_data[1:]:
            is_reaccom = len(row) > alt_dep_key_idx and row[alt_dep_key_idx].strip()
            has_orig_date = len(row) > orig_dep_idx and row[orig_dep_idx].strip()
            has_alt_date = len(row) > alt_dep_idx and row[alt_dep_idx].strip()

            if is_reaccom and has_orig_date and has_alt_date:
                try:
                    orig_dt = datetime.strptime(row[orig_dep_idx].strip(), date_format)
                    alt_dt = datetime.strptime(row[alt_dep_idx].strip(), date_format)
                    
                    delay = alt_dt - orig_dt
                    delays_in_hours.append(delay.total_seconds() / 3600)
                except (ValueError, TypeError):
                    continue

        if not delays_in_hours:
            messagebox.showinfo("Info", "No valid reaccommodation delays could be calculated. Please check the data in the CSV.")
            return None, None

        max_delay = max(delays_in_hours) if delays_in_hours else 0
        bin_size = 4
        bin_edges = np.arange(0, max_delay + bin_size, bin_size)
        
        counts, _ = np.histogram(delays_in_hours, bins=bin_edges)
        
        bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])} hrs" for i in range(len(counts))]
        
        return bin_labels, counts

    def _prepare_recloc_plot_data(self):
        if not self.full_data or len(self.full_data) < 2:
            return None, None

        header = self.full_data[0]
        header_lower = [h.lower() for h in header]

        try:
            recloc_idx = header_lower.index('recloc')
            alt_dep_key_idx = header_lower.index('alt_dep_key')
        except ValueError:
            messagebox.showerror("CSV Error", "A required column (RECLOC or ALT_DEP_KEY) was not found.")
            return None, None

        # Step 1: Count re-accommodations for each RECLOC
        recloc_counts = {}
        for row in self.full_data[1:]:
            recloc = row[recloc_idx].strip()
            if not recloc:
                continue

            if recloc not in recloc_counts:
                recloc_counts[recloc] = 0
            
            is_reaccom = len(row) > alt_dep_key_idx and row[alt_dep_key_idx].strip()
            if is_reaccom:
                recloc_counts[recloc] += 1

        if not recloc_counts:
            messagebox.showinfo("Info", "No RECLOC data found to analyze.")
            return None, None
            
        # ### FIXED: Aggregate the counts with a cap at 6 ###
        # Step 2: Aggregate the counts, grouping 6 or more together.
        distribution = {}
        max_flights_to_show = 6
        for num_flights in recloc_counts.values():
            # If the number of flights is 6 or more, group it into the max category
            key = min(num_flights, max_flights_to_show)
            distribution[key] = distribution.get(key, 0) + 1
            
        if not distribution:
            return None, None

        # Step 3: Prepare sorted labels and data for plotting with the "6+" label
        sorted_keys = sorted(distribution.keys())
        plot_counts = [distribution[key] for key in sorted_keys]
        
        plot_labels = []
        def pluralize(n):
            return 's' if n != 1 else ''

        for key in sorted_keys:
            # If the key is the max value we're showing, label it as "6+"
            if key == max_flights_to_show:
                plot_labels.append(f"{key}+ Flights")
            else:
                plot_labels.append(f"{key} Flight{pluralize(key)}")

        return plot_labels, plot_counts

    def _create_graph_window(self):
        if self.graph_window is not None and self.graph_window.winfo_exists():
            self.graph_window.lift()
            self.graph_window.focus()
            return
        
        cvm_labels, cvm_counts = self._prepare_cvm_plot_data()
        delay_labels, delay_counts = self._prepare_delay_plot_data()
        recloc_labels, recloc_counts = self._prepare_recloc_plot_data()

        self.graph_window = ctk.CTkToplevel(self)
        self.graph_window.title("Analysis Graphs")
        self.graph_window.geometry("900x950")
        self.graph_window.protocol("WM_DELETE_WINDOW", self._on_graph_close)

        bg_color, text_color = self._get_current_theme_colors()

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 11), facecolor=bg_color)

        # Plot 1: CVM Data
        if cvm_labels is not None and len(cvm_labels) > 0:
            ax1.bar(cvm_labels, cvm_counts, color="#5DADE2")
            ax1.set_title('Re-accommodated Passengers by CVM', color=text_color, fontsize=14)
            ax1.set_xlabel('CVM Bins', color=text_color, fontsize=10)
            ax1.set_ylabel('# of Passengers', color=text_color, fontsize=10)
            ax1.tick_params(axis='x', labelrotation=45, colors=text_color, labelsize=8)
            ax1.tick_params(axis='y', colors=text_color, labelsize=8)
            ax1.grid(axis='y', linestyle='--', alpha=0.6)
            ax1.set_facecolor(bg_color)
            for spine in ax1.spines.values():
                spine.set_edgecolor(text_color)
        else:
            ax1.text(0.5, 0.5, 'CVM data not available', ha='center', va='center', color=text_color)
            ax1.set_facecolor(bg_color)
            ax1.set_xticks([])
            ax1.set_yticks([])

        # Plot 2: Delay Data
        if delay_labels is not None and len(delay_labels) > 0:
            ax2.bar(delay_labels, delay_counts, color="#F5B041")
            ax2.set_title('Re-accommodation Delay Distribution', color=text_color, fontsize=14)
            ax2.set_xlabel('Delay Bins (hours)', color=text_color, fontsize=10)
            ax2.set_ylabel('# of Passengers', color=text_color, fontsize=10)
            ax2.tick_params(axis='x', labelrotation=45, colors=text_color, labelsize=8)
            ax2.tick_params(axis='y', colors=text_color, labelsize=8)
            ax2.grid(axis='y', linestyle='--', alpha=0.6)
            ax2.set_facecolor(bg_color)
            for spine in ax2.spines.values():
                spine.set_edgecolor(text_color)
        else:
            ax2.text(0.5, 0.5, 'Delay data not available', ha='center', va='center', color=text_color)
            ax2.set_facecolor(bg_color)
            ax2.set_xticks([])
            ax2.set_yticks([])

        # Plot 3: Re-accommodations per RECLOC
        if recloc_labels is not None and len(recloc_labels) > 0:
            ax3.bar(recloc_labels, recloc_counts, color="#2ECC71")
            ax3.set_title('Distribution of Alternate Flights per Booking', color=text_color, fontsize=14)
            ax3.set_xlabel('# of Alternate Flights', color=text_color, fontsize=10)
            ax3.set_ylabel('# of Bookings (RECLOCs)', color=text_color, fontsize=10)
            ax3.tick_params(axis='x', labelrotation=45, colors=text_color, labelsize=8)
            ax3.tick_params(axis='y', colors=text_color, labelsize=8)
            ax3.grid(axis='y', linestyle='--', alpha=0.6)
            ax3.set_facecolor(bg_color)
            for spine in ax3.spines.values():
                spine.set_edgecolor(text_color)
        else:
            ax3.text(0.5, 0.5, 'Booking distribution data not available', ha='center', va='center', color=text_color)
            ax3.set_facecolor(bg_color)
            ax3.set_xticks([])
            ax3.set_yticks([])


        fig.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_widgets(self) -> None:
        title_label = ctk.CTkLabel(self, text="COPA Reaccommodation Analysis", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=20, sticky="ew", padx=20)

        slider_frame = ctk.CTkFrame(self, corner_radius=10)
        slider_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
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

        self.run_button = ctk.CTkButton(self, text="Run", command=self._simulate_run, font=("Arial", 14, "bold"))
        self.run_button.grid(row=1, column=1, sticky="e", padx=20, pady=10)

        theme_switch_frame = ctk.CTkFrame(self, corner_radius=10)
        theme_switch_frame.grid(row=1, column=3, sticky="ne", padx=20, pady=10)
        self.theme_switch_label = ctk.CTkLabel(theme_switch_frame, text="Theme Mode:")
        self.theme_switch_label.grid(row=0, column=0, padx=5, pady=5)
        self.theme_switch = ctk.CTkSwitch(theme_switch_frame, text="", command=self._toggle_theme, onvalue="dark",
                                          offvalue="light")
        self.theme_switch.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        if self.current_theme == "dark":
             self.theme_switch.select()
        else:
             self.theme_switch.deselect()

        self.results_frame = ctk.CTkFrame(self.main_container)
        self.results_frame.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)

        self.update_idletasks()

        self.total_cancellations_label = ctk.CTkLabel(self.results_frame, text="Cancellations:", font=("Arial", 14, "bold"))
        self.total_cancellations_label.grid(row=0, column=0, padx=10, pady=2, sticky="e")
        self.total_cancellations_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.total_cancellations_value_label.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        self.reaccom_passengers_label = ctk.CTkLabel(self.results_frame, text="Reaccomodated passengers:", font=("Arial", 14, "bold"))
        self.reaccom_passengers_label.grid(row=1, column=0, padx=10, pady=2, sticky="e")
        self.reaccom_passengers_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.reaccom_passengers_value_label.grid(row=1, column=1, padx=10, pady=2, sticky="w")

        self.num_reaccom_label = ctk.CTkLabel(self.results_frame, text="Number of Reaccomodations:", font=("Arial", 14, "bold"))
        self.num_reaccom_label.grid(row=2, column=0, padx=10, pady=2, sticky="e")
        self.num_reaccom_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.num_reaccom_value_label.grid(row=2, column=1, padx=10, pady=2, sticky="w")

        self.feasible_reaccom_label = ctk.CTkLabel(self.results_frame, text="Total number of feasible reaccomodations:", font=("Arial", 14, "bold"))
        self.feasible_reaccom_label.grid(row=3, column=0, padx=10, pady=2, sticky="e")
        self.feasible_reaccom_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.feasible_reaccom_value_label.grid(row=3, column=1, padx=10, pady=2, sticky="w")

        self.reaccomodation_rate_label = ctk.CTkLabel(self.results_frame, text="Reaccomodation rate:", font=("Arial", 14, "bold"))
        self.reaccomodation_rate_label.grid(row=4, column=0, padx=10, pady=2, sticky="e")
        self.reaccomodation_rate_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.reaccomodation_rate_value_label.grid(row=4, column=1, padx=10, pady=2, sticky="w")

        self.total_runtime_label = ctk.CTkLabel(self.results_frame, text="Runtime:", font=("Arial", 14, "bold"))
        self.total_runtime_label.grid(row=5, column=0, padx=10, pady=2, sticky="e")
        self.total_runtime_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.total_runtime_value_label.grid(row=5, column=1, padx=10, pady=2, sticky="w")

        self.num_variables_label = ctk.CTkLabel(self.results_frame, text="Number of variables:", font=("Arial", 14, "bold"))
        self.num_variables_label.grid(row=6, column=0, padx=10, pady=2, sticky="e")
        self.num_variables_value_label = ctk.CTkLabel(self.results_frame, text="", font=("Arial", 14))
        self.num_variables_value_label.grid(row=6, column=1, padx=10, pady=2, sticky="w")

        self.pie_chart_frame = ctk.CTkFrame(self.main_container)
        self.pie_chart_frame.grid(row=7, column = 0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.pie_chart_frame.grid_remove()

    def _apply_styles(self) -> None:
        pass

    def _get_current_theme_colors(self):
        try:
            temp_frame = ctk.CTkFrame(self)
            temp_label = ctk.CTkLabel(temp_frame, text="")
            self.update_idletasks()
            bg_color = temp_frame.cget("fg_color")
            text_color = temp_label.cget("text_color")
            temp_label.destroy()
            temp_frame.destroy()

            if isinstance(bg_color, (list, tuple)):
                bg_color = bg_color[1] if self.current_theme == "dark" else bg_color[0]
            if isinstance(text_color, (list, tuple)):
                text_color = text_color[1] if self.current_theme == "dark" else text_color[0]

            if not mcolors.is_color_like(bg_color):
                bg_color = 'white' if self.current_theme == "light" else '#2B2B2B'
            if not mcolors.is_color_like(text_color):
                text_color = 'black' if self.current_theme == "light" else 'white'

            return bg_color, text_color

        except Exception:
            bg = 'white' if self.current_theme == "light" else '#2B2B2B'
            txt = 'black' if self.current_theme == "light" else 'white'
            return bg, txt


    def create_pie_chart(self):
        for widget in self.pie_chart_frame.winfo_children():
            widget.destroy()
        self.canvas = None

        labels = ['Reaccomodated', 'Not Reaccomodated']
        rate_percent = self.reaccomodation_rate
        sizes = [rate_percent, 100 - rate_percent]

        bg_color, text_color = self._get_current_theme_colors()
        pie_text_color = 'white' if self.current_theme == 'dark' else 'black'

        try:
            fig = Figure(figsize=(4, 3), dpi=100, facecolor=bg_color)
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg_color)

            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90,
                                              textprops=dict(color=text_color))
            for autotext in autotexts:
                 autotext.set_color(pie_text_color)

            ax.axis('equal')
            ax.set_title("Reaccommodation Rate", fontdict={'fontsize': 14}, color=text_color)

            self.canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        except ValueError as e:
             messagebox.showerror("Plotting Error", f"Failed to create pie chart.\nColor error: {e}\nUsing fallback colors.")
             bg_color_fallback = 'white' if self.current_theme == "light" else 'black'
             text_color_fallback = 'black' if self.current_theme == "light" else 'white'
             fig = Figure(figsize=(4, 3), dpi=100, facecolor=bg_color_fallback)
             ax = fig.add_subplot(111)
             ax.set_facecolor(bg_color_fallback)
             wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.2f%%', startangle=90,
                                              textprops=dict(color=text_color_fallback))
             for autotext in autotexts:
                 autotext.set_color('grey')
             ax.axis('equal')
             ax.set_title("Reaccommodation Rate", fontdict={'fontsize': 14}, color=text_color_fallback)
             self.canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
             self.canvas.draw()
             self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


    def _create_csv_view(self, csv_window: ctk.CTkToplevel) -> None:
        try:
            if self.full_data and len(self.full_data) > 0:
                search_frame = ctk.CTkFrame(csv_window)
                search_frame.pack(pady=5, padx=5, fill="x")

                self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...")
                self.search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
                self.search_entry.bind("<Return>", lambda event: self._search_treeview())

                search_button = ctk.CTkButton(search_frame, text="Search", command=self._search_treeview)
                search_button.pack(side=tk.LEFT, padx=5)
                clear_button = ctk.CTkButton(search_frame, text="Clear", command=self._clear_search)
                clear_button.pack(side=tk.LEFT, padx=5)

                style = ttk.Style()
                self._update_treeview_style(style)

                self.tree = ttk.Treeview(csv_window, show="headings", style="Treeview")
                self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0,5))

                vscroll = ttk.Scrollbar(csv_window, orient="vertical", command=self.tree.yview)
                vscroll.pack(side=tk.RIGHT, fill="y", pady=(0,5))
                self.tree.configure(yscrollcommand=vscroll.set)

                hscroll = ttk.Scrollbar(csv_window, orient="horizontal", command=self.tree.xview)
                hscroll.pack(side=tk.BOTTOM, fill="x", padx=5, pady=(0,5))
                self.tree.configure(xscrollcommand=hscroll.set)

                if not self.full_data: return
                column_names = self.full_data[0]
                self.tree["columns"] = column_names

                self.sort_states = {col: None for col in column_names}

                for col in column_names:
                    self.tree.column(col, width=150, minwidth=80, anchor="w")
                    self.tree.heading(col, text=col + "   ", anchor='w', command=lambda c=col: self._sort_column(c))

                self.all_data = self.full_data[1:] if len(self.full_data) > 1 else []
                self._populate_treeview(self.all_data)

            else:
                 error_label = ctk.CTkLabel(csv_window, text="No CSV data available to display.")
                 error_label.pack(padx=10, pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error creating CSV view: {e}")
            error_label = ctk.CTkLabel(csv_window, text=f"Error displaying CSV view: {e}")
            error_label.pack(padx=10, pady=10)

    def _populate_treeview(self, data):
        if not hasattr(self, 'tree') or not self.tree.winfo_exists(): return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, row in enumerate(data):
            self.tree.insert("", tk.END, values=row)

    def _search_treeview(self):
        if not hasattr(self, 'search_entry') or not hasattr(self, 'all_data') or not hasattr(self, 'tree'):
             return

        search_text = self.search_entry.get().lower().strip()
        if not search_text:
             self._populate_treeview(self.all_data)
             for col in self.sort_states:
                 if hasattr(self, 'tree') and self.tree.winfo_exists():
                    try:
                         self.tree.heading(col, text=col + "   ")
                    except tk.TclError: pass
                 self.sort_states[col] = None
             return

        filtered_data = []
        for row in self.all_data:
            if any(search_text in str(value).lower() for value in row):
                filtered_data.append(row)

        self._populate_treeview(filtered_data)
        for col in self.sort_states:
             if hasattr(self, 'tree') and self.tree.winfo_exists():
                 try:
                     self.tree.heading(col, text=col + "   ")
                 except tk.TclError: pass
             self.sort_states[col] = None

    def _clear_search(self):
         if not hasattr(self, 'search_entry') or not hasattr(self, 'all_data'):
             return
         self.search_entry.delete(0, tk.END)
         self._populate_treeview(self.all_data)
         for col in self.sort_states:
             if hasattr(self, 'tree') and self.tree.winfo_exists():
                 try:
                     self.tree.heading(col, text=col + "   ")
                 except tk.TclError: pass
             self.sort_states[col] = None


    def _sort_column(self, col):
        if not hasattr(self, 'tree') or not self.tree.winfo_exists() or not hasattr(self, 'sort_states'): return

        current_state = self.sort_states.get(col)
        reverse_sort = False

        if current_state is None:
            new_state = True
            reverse_sort = False
            sort_indicator = " ▲"
        elif current_state is True:
            new_state = False
            reverse_sort = True
            sort_indicator = " ▼"
        else:
            new_state = True
            reverse_sort = False
            sort_indicator = " ▲"

        for c in self.sort_states:
             if c != col:
                 try:
                     self.tree.heading(c, text=c + "   ")
                 except tk.TclError: pass
                 self.sort_states[c] = None

        try:
            self.tree.heading(col, text=col + sort_indicator)
        except tk.TclError: pass
        self.sort_states[col] = new_state

        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]

        try:
            def sort_key(x):
                try:
                    val = x[0]
                    return float(val) if val else float('-inf')
                except (ValueError, TypeError):
                    val = x[0] if x[0] is not None else ""
                    return str(val).lower()

            data.sort(key=sort_key, reverse=reverse_sort)

        except Exception:
            data.sort(key=lambda x: str(x[0] if x[0] is not None else "").lower(), reverse=reverse_sort)

        for index, (val, child) in enumerate(data):
            self.tree.move(child, "", index)


    def _update_optimization_time(self, value: float) -> None:
        minutes = int(value)
        self.optimization_time_label.configure(text=f"Optimization Time: {minutes} mins")

    def _simulate_run(self) -> None:
        self.run_button.configure(state="disabled", text="Running...")

        if self.loading_symbol: self.loading_symbol.destroy()
        self.loading_symbol = ttk.Progressbar(self.main_container, mode="indeterminate", length=200)
        self.loading_symbol.grid(row = 1, column = 0, columnspan=2, padx = 20, pady = 10, sticky="ew")
        self.loading_symbol.start(10)

        optimization_time = self.optimization_time_value.get()
        wait_time_ms = 2000
        self.after(wait_time_ms, self._display_results)

    def _display_results(self) -> None:
        if self.loading_symbol:
            self.loading_symbol.stop()
            self.loading_symbol.grid_forget()
        self.run_button.configure(state="normal", text="Run")

        self.total_cancellations_value_label.configure(text=f"{self.total_cancellations:,}")
        self.reaccom_passengers_value_label.configure(text=f"{self.reaccomodated_passengers:,}")
        self.num_reaccom_value_label.configure(text=f"{self.num_reaccomodations:,}")
        self.feasible_reaccom_value_label.configure(text=f"{self.feasible_reaccomodations:,}")
        self.reaccomodation_rate_value_label.configure(text=f"{self.reaccomodation_rate:.4f}%")
        self.total_runtime_value_label.configure(text=f"{self.total_runtime} minutes")
        self.num_variables_value_label.configure(text=f"{self.num_variables:,}")

        self.create_pie_chart()
        self.pie_chart_frame.grid()

        if self.csv_window is None or not self.csv_window.winfo_exists():
            self.csv_window = ctk.CTkToplevel(self)
            self.csv_window.title("Full CSV Data")
            self.csv_window.geometry("1200x500")
            self.csv_window.protocol("WM_DELETE_WINDOW", self._on_csv_close)
            self._create_csv_view(self.csv_window)
        else:
            self.csv_window.lift()
            self.csv_window.focus()
            
        self._create_graph_window()

    def _on_csv_close(self):
        if self.csv_window:
            self.csv_window.destroy()
        self.csv_window = None

    def _on_graph_close(self):
        if self.graph_window:
            self.graph_window.destroy()
        self.graph_window = None

    def _toggle_theme(self) -> None:
        new_mode = "dark" if ctk.get_appearance_mode() == "Light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.current_theme = new_mode

        if self.csv_window and self.csv_window.winfo_exists() and hasattr(self, 'tree'):
             self._update_treeview_style()
        if self.canvas:
             self.create_pie_chart()
        
        if self.graph_window and self.graph_window.winfo_exists():
            self.graph_window.destroy()
            self._create_graph_window()


    def _update_treeview_style(self, style=None):
         if not style: style = ttk.Style()

         bg_color, _ = self._get_current_theme_colors()
         header_text_color = 'black'
         _, data_text_color = self._get_current_theme_colors()

         if self.current_theme == "dark":
             selected_color = '#2B2B2B'
         else:
             selected_color = '#DCE4EE'

         header_bg_color = 'white'

         try:
             style.theme_use("default")
             style.configure("Treeview", background=bg_color, foreground=data_text_color, fieldbackground=bg_color, rowheight=25)
             style.map('Treeview', background=[('selected', selected_color)])
             style.configure("Treeview.Heading", background=header_bg_color, foreground=header_text_color, font=('Arial', 10,'bold'), relief='flat')
             style.map("Treeview.Heading", background=[('active', '#F0F0F0')])

             if hasattr(self, 'tree') and self.tree.winfo_exists():
                 self.tree.update_idletasks()
         except tk.TclError as e:
             pass


def main() -> None:
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        dir_path = os.getcwd()

    csv_file = os.path.join(dir_path, 'Mphasis Hackathon.csv')

    app = ReaccomGUI(csv_file)
    app.mainloop()

if __name__ == "__main__":
    main()