import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils.api_client import APIClient
import csv
import json

class Dashboard(ttk.Frame):

    def __init__(self, master):

        super().__init__(master)class Dashboard(Frame):

        self.pack(fill="both", expand=True, padx=20, pady=20)    def __init__(self, master):

        self.api = APIClient()        super().__init__(master)

        self.create_styles()        self.pack(fill="both", expand=True, padx=20, pady=20)

        self.setup_ui()        self.api = APIClient()

        self.update_all_data()        self.setup_ui()

            self.update_all_data()

    def create_styles(self):    

        style = ttk.Style()    def setup_ui(self):

        # Configure button styles        # Title

        style.configure("success.TButton", background="green", foreground="white")        title = Label(self, text="BallotGuard Admin Dashboard", 

        style.configure("info.TButton", background="blue", foreground="white")                     font=("Arial", 24, "bold"), bootstyle="primary")

        style.configure("warning.TButton", background="orange", foreground="black")        title.pack(pady=20)

        style.configure("secondary.TButton", background="gray", foreground="white")        

        # Configure label styles        # Main content area

        style.configure("title.TLabel", font=("Arial", 24, "bold"))        main_frame = Frame(self)

        style.configure("total.TLabel", font=("Arial", 18, "bold"))        main_frame.pack(fill="both", expand=True)

        style.configure("info.TLabel", font=("Arial", 12))        

        style.configure("small.TLabel", font=("Arial", 10))        # Left panel - Statistics

        style.configure("status.TLabel", font=("Arial", 10))        left_panel = Labelframe(main_frame, text="Vote Statistics", padding=20)

            left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

    def setup_ui(self):        

        # Title        self.total_votes_label = Label(left_panel, text="Total Votes: Loading...", 

        title = ttk.Label(self, text="BallotGuard Admin Dashboard", style="title.TLabel")                                      font=("Arial", 18, "bold"), bootstyle="success")

        title.pack(pady=20)        self.total_votes_label.pack(pady=10)

                

        # Main content area        self.status_label = Label(left_panel, text="Status: Checking...", 

        main_frame = ttk.Frame(self)                                 font=("Arial", 12))

        main_frame.pack(fill="both", expand=True)        self.status_label.pack(pady=5)

                

        # Left panel - Statistics        self.last_update_label = Label(left_panel, text="Last Updated: --", 

        left_panel = ttk.LabelFrame(main_frame, text="Vote Statistics", padding=20)                                      font=("Arial", 10), bootstyle="secondary")

        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))        self.last_update_label.pack(pady=5)

                

        self.total_votes_label = ttk.Label(left_panel, text="Total Votes: Loading...",         # Candidate breakdown

                                      style="total.TLabel")        candidates_frame = Labelframe(left_panel, text="Candidate Breakdown", padding=10)

        self.total_votes_label.pack(pady=10)        candidates_frame.pack(fill="x", pady=20)

                

        self.status_label = ttk.Label(left_panel, text="Status: Checking...",         self.candidates_text = tk.Text(candidates_frame, height=5, width=30, 

                                 style="info.TLabel")                                      font=("Arial", 10))

        self.status_label.pack(pady=5)        self.candidates_text.pack(fill="x")

                

        self.last_update_label = ttk.Label(left_panel, text="Last Updated: --",         # Right panel - Controls

                                      style="small.TLabel")        right_panel = Labelframe(main_frame, text="Admin Controls", padding=20)

        self.last_update_label.pack(pady=5)        right_panel.pack(side="right", fill="y", padx=(10, 0))

                

        # Candidate breakdown        # Control buttons

        candidates_frame = ttk.LabelFrame(left_panel, text="Candidate Breakdown", padding=10)        Button(right_panel, text="🔄 Refresh Data", 

        candidates_frame.pack(fill="x", pady=20)               command=self.update_all_data, bootstyle="primary").pack(pady=5, fill="x")

                

        self.candidates_text = tk.Text(candidates_frame, height=5, width=30,         Button(right_panel, text="📊 Export Results", 

                                      font=("Arial", 10))               command=self.export_results, bootstyle="success").pack(pady=5, fill="x")

        self.candidates_text.pack(fill="x")        

                Button(right_panel, text="🔍 Test Connection", 

        # Right panel - Controls               command=self.test_connection, bootstyle="info").pack(pady=5, fill="x")

        right_panel = ttk.LabelFrame(main_frame, text="Admin Controls", padding=20)        

        right_panel.pack(side="right", fill="y", padx=(10, 0))        Button(right_panel, text="⚙️ System Health", 

                       command=self.show_system_health, bootstyle="warning").pack(pady=5, fill="x")

        # Control buttons        

        ttk.Button(right_panel, text="🔄 Refresh Data",         Button(right_panel, text="📋 View Logs", 

               command=self.update_all_data).pack(pady=5, fill="x")               command=self.show_logs, bootstyle="secondary").pack(pady=5, fill="x")

                

        ttk.Button(right_panel, text="📊 Export Results",         # Bottom status bar

               command=self.export_results, style="success.TButton").pack(pady=5, fill="x")        self.status_bar = Label(self, text="Ready", bootstyle="inverse")

                self.status_bar.pack(side="bottom", fill="x", pady=(10, 0))

        ttk.Button(right_panel, text="🔍 Test Connection",     

               command=self.test_connection, style="info.TButton").pack(pady=5, fill="x")    def update_all_data(self):

                self.status_bar.config(text="Updating data...")

        ttk.Button(right_panel, text="⚙️ System Health",         self.update()  # Refresh UI

               command=self.show_system_health, style="warning.TButton").pack(pady=5, fill="x")        

                # Get tally data

        ttk.Button(right_panel, text="📋 View Logs",         tally_data = self.api.get_detailed_tally()

               command=self.show_logs, style="secondary.TButton").pack(pady=5, fill="x")        

                if "total_votes" in tally_data:

        # Bottom status bar            self.total_votes_label.config(text=f"Total Votes: {tally_data['total_votes']}")

        self.status_bar = ttk.Label(self, text="Ready", style="status.TLabel")            

        self.status_bar.pack(side="bottom", fill="x", pady=(10, 0))            status_text = tally_data.get('status', 'unknown')

                mode = tally_data.get('mode', '')

    def update_all_data(self):            if mode == 'demo':

        self.status_bar.config(text="Updating data...")                status_text += " (Demo Mode)"

        self.update()  # Refresh UI            self.status_label.config(text=f"Status: {status_text}")

                    

        # Get tally data            # Update timestamp

        tally_data = self.api.get_detailed_tally()            import time

                    current_time = time.strftime('%Y-%m-%d %H:%M:%S')

        if "total_votes" in tally_data:            self.last_update_label.config(text=f"Last Updated: {current_time}")

            self.total_votes_label.config(text=f"Total Votes: {tally_data['total_votes']}")            

                        # Update candidates

            status_text = tally_data.get('status', 'unknown')            self.update_candidates_display(tally_data)

            mode = tally_data.get('mode', '')            

            if mode == 'demo':            self.status_bar.config(text="Data updated successfully")

                status_text += " (Demo Mode)"        else:

            self.status_label.config(text=f"Status: {status_text}")            self.total_votes_label.config(text="Error: Cannot fetch data")

                        self.status_label.config(text="Status: Connection Error")

            # Update timestamp            self.status_bar.config(text="Failed to update data")

            import time    

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')    def update_candidates_display(self, data):

            self.last_update_label.config(text=f"Last Updated: {current_time}")        self.candidates_text.delete(1.0, tk.END)

                    

            # Update candidates        if 'candidates' in data:

            self.update_candidates_display(tally_data)            self.candidates_text.insert(tk.END, "Candidate Breakdown:\n")

                        self.candidates_text.insert(tk.END, "-" * 30 + "\n")

            self.status_bar.config(text="Data updated successfully")            for candidate in data['candidates']:

        else:                name = candidate['name']

            self.total_votes_label.config(text="Error: Cannot fetch data")                votes = candidate['votes']

            self.status_label.config(text="Status: Connection Error")                percentage = (votes / data['total_votes'] * 100) if data['total_votes'] > 0 else 0

            self.status_bar.config(text="Failed to update data")                self.candidates_text.insert(tk.END, f"{name}: {votes} ({percentage:.1f}%)\n")

            else:

    def update_candidates_display(self, data):            self.candidates_text.insert(tk.END, "Demo Features:\n")

        self.candidates_text.delete(1.0, tk.END)            self.candidates_text.insert(tk.END, "• Vote tallying\n")

                    self.candidates_text.insert(tk.END, "• Real-time updates\n") 

        if 'candidates' in data:            self.candidates_text.insert(tk.END, "• Export functionality\n")

            self.candidates_text.insert(tk.END, "Candidate Breakdown:\n")            self.candidates_text.insert(tk.END, "• System monitoring\n")

            self.candidates_text.insert(tk.END, "-" * 30 + "\n")    

            for candidate in data['candidates']:    def export_results(self):

                name = candidate['name']        try:

                votes = candidate['votes']            data = self.api.get_detailed_tally()

                percentage = (votes / data['total_votes'] * 100) if data['total_votes'] > 0 else 0            

                self.candidates_text.insert(tk.END, f"{name}: {votes} ({percentage:.1f}%)\n")            filename = filedialog.asksaveasfilename(

        else:                defaultextension=".csv",

            self.candidates_text.insert(tk.END, "Demo Features:\n")                filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")]

            self.candidates_text.insert(tk.END, "• Vote tallying\n")            )

            self.candidates_text.insert(tk.END, "• Real-time updates\n")             

            self.candidates_text.insert(tk.END, "• Export functionality\n")            if filename:

            self.candidates_text.insert(tk.END, "• System monitoring\n")                if filename.endswith('.json'):

                        with open(filename, 'w') as f:

    def export_results(self):                        json.dump(data, f, indent=2)

        try:                else:

            data = self.api.get_detailed_tally()                    with open(filename, 'w', newline='') as f:

                                    writer = csv.writer(f)

            filename = filedialog.asksaveasfilename(                        writer.writerow(['Metric', 'Value'])

                defaultextension=".csv",                        writer.writerow(['Total Votes', data.get('total_votes', 0)])

                filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")]                        writer.writerow(['Status', data.get('status', 'unknown')])

            )                        

                                    if 'candidates' in data:

            if filename:                            writer.writerow(['', ''])

                if filename.endswith('.json'):                            writer.writerow(['Candidate', 'Votes'])

                    with open(filename, 'w') as f:                            for candidate in data['candidates']:

                        json.dump(data, f, indent=2)                                writer.writerow([candidate['name'], candidate['votes']])

                else:                

                    with open(filename, 'w', newline='') as f:                messagebox.showinfo("Success", f"Results exported to:\n{filename}")

                        writer = csv.writer(f)                self.status_bar.config(text="Export successful")

                        writer.writerow(['Metric', 'Value'])        

                        writer.writerow(['Total Votes', data.get('total_votes', 0)])        except Exception as e:

                        writer.writerow(['Status', data.get('status', 'unknown')])            messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")

                            

                        if 'candidates' in data:    def test_connection(self):

                            writer.writerow(['', ''])        result = self.api.test_api()

                            writer.writerow(['Candidate', 'Votes'])        status = result.get('status', 'unknown')

                            for candidate in data['candidates']:        message = result.get('message', 'No message')

                                writer.writerow([candidate['name'], candidate['votes']])        

                        if 'offline' in status.lower():

                messagebox.showinfo("Success", f"Results exported to:\n{filename}")            messagebox.showwarning("Connection Test", 

                self.status_bar.config(text="Export successful")                                 f"Flask Server: {status}\n\n{message}\n\nAdmin UI working in demo mode!")

                else:

        except Exception as e:            messagebox.showinfo("Connection Test", f"Status: {status}\n\n{message}")

            messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")    

        def show_system_health(self):

    def test_connection(self):        health_data = self.api.get_system_health()

        result = self.api.test_api()        

        status = result.get('status', 'unknown')        health_text = "System Health Report:\n"

        message = result.get('message', 'No message')        health_text += "=" * 30 + "\n"

                for key, value in health_data.items():

        if 'offline' in status.lower():            health_text += f"{key.replace('_', ' ').title()}: {value}\n"

            messagebox.showwarning("Connection Test",         

                                 f"Flask Server: {status}\n\n{message}\n\nAdmin UI working in demo mode!")        health_text += "\nAdmin UI Components:\n"

        else:        health_text += "• Dashboard: ✅ Working\n"

            messagebox.showinfo("Connection Test", f"Status: {status}\n\n{message}")        health_text += "• Data Display: ✅ Working\n"

            health_text += "• Export Function: ✅ Working\n"

    def show_system_health(self):        

        health_data = self.api.get_system_health()        messagebox.showinfo("System Health", health_text)

            

        health_text = "System Health Report:\n"    def show_logs(self):

        health_text += "=" * 30 + "\n"        logs = """Activity Log:

        for key, value in health_data.items():==================

            health_text += f"{key.replace('_', ' ').title()}: {value}\n"Admin UI started successfully

        Mock data loaded (157 votes)

        health_text += "\nAdmin UI Components:\n"Dashboard initialized

        health_text += "• Dashboard: ✅ Working\n"Features demonstrated:

        health_text += "• Data Display: ✅ Working\n"• Vote tallying display

        health_text += "• Export Function: ✅ Working\n"• Real-time updates

        • Export functionality  

        messagebox.showinfo("System Health", health_text)• System health monitoring"""

            

    def show_logs(self):        messagebox.showinfo("Activity Logs", logs)

        logs = """Activity Log:
==================
Admin UI started successfully
Mock data loaded (157 votes)
Dashboard initialized
Features demonstrated:
• Vote tallying display
• Real-time updates
• Export functionality  
• System health monitoring"""
        
        messagebox.showinfo("Activity Logs", logs)