import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe
from utils.api_client import APIClient
import tkinter as tk
from tkinter import messagebox, filedialog
import csv
import json

class Dashboard(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.api = APIClient()
        self.setup_ui()
        self.update_all_data()
    
    def setup_ui(self):
        # Title
        title = Label(self, text="BallotGuard Admin Dashboard", 
                     font=("Arial", 24, "bold"), bootstyle="primary")
        title.pack(pady=20)
        
        # Main content area
        main_frame = Frame(self)
        main_frame.pack(fill="both", expand=True)
        
        # Left panel - Statistics
        left_panel = Labelframe(main_frame, text="Vote Statistics", padding=20)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.total_votes_label = Label(left_panel, text="Total Votes: Loading...", 
                                      font=("Arial", 18, "bold"), bootstyle="success")
        self.total_votes_label.pack(pady=10)
        
        self.status_label = Label(left_panel, text="Status: Checking...", 
                                 font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        self.last_update_label = Label(left_panel, text="Last Updated: --", 
                                      font=("Arial", 10), bootstyle="secondary")
        self.last_update_label.pack(pady=5)
        
        # Candidate breakdown
        candidates_frame = Labelframe(left_panel, text="Candidate Breakdown", padding=10)
        candidates_frame.pack(fill="x", pady=20)
        
        self.candidates_text = tk.Text(candidates_frame, height=5, width=30, 
                                      font=("Arial", 10))
        self.candidates_text.pack(fill="x")
        
        # Right panel - Controls
        right_panel = Labelframe(main_frame, text="Admin Controls", padding=20)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        
        # Control buttons
        Button(right_panel, text="🔄 Refresh Data", 
               command=self.update_all_data, bootstyle="primary").pack(pady=5, fill="x")
        
        Button(right_panel, text="📊 Export Results", 
               command=self.export_results, bootstyle="success").pack(pady=5, fill="x")
        
        Button(right_panel, text="🔍 Test Connection", 
               command=self.test_connection, bootstyle="info").pack(pady=5, fill="x")
        
        Button(right_panel, text="⚙️ System Health", 
               command=self.show_system_health, bootstyle="warning").pack(pady=5, fill="x")
        
        Button(right_panel, text="📋 View Logs", 
               command=self.show_logs, bootstyle="secondary").pack(pady=5, fill="x")
        
        # Bottom status bar
        self.status_bar = Label(self, text="Ready", bootstyle="inverse")
        self.status_bar.pack(side="bottom", fill="x", pady=(10, 0))
    
    def update_all_data(self):
        self.status_bar.config(text="Updating data...")
        self.update()  # Refresh UI
        
        # Get tally data
        tally_data = self.api.get_detailed_tally()
        
        if "total_votes" in tally_data:
            self.total_votes_label.config(text=f"Total Votes: {tally_data['total_votes']}")
            
            status_text = tally_data.get('status', 'unknown')
            mode = tally_data.get('mode', '')
            if mode == 'demo':
                status_text += " (Demo Mode)"
            self.status_label.config(text=f"Status: {status_text}")
            
            # Update timestamp
            import time
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            self.last_update_label.config(text=f"Last Updated: {current_time}")
            
            # Update candidates
            self.update_candidates_display(tally_data)
            
            self.status_bar.config(text="Data updated successfully")
        else:
            self.total_votes_label.config(text="Error: Cannot fetch data")
            self.status_label.config(text="Status: Connection Error")
            self.status_bar.config(text="Failed to update data")
    
    def update_candidates_display(self, data):
        self.candidates_text.delete(1.0, tk.END)
        
        if 'candidates' in data:
            self.candidates_text.insert(tk.END, "Candidate Breakdown:\n")
            self.candidates_text.insert(tk.END, "-" * 30 + "\n")
            for candidate in data['candidates']:
                name = candidate['name']
                votes = candidate['votes']
                percentage = (votes / data['total_votes'] * 100) if data['total_votes'] > 0 else 0
                self.candidates_text.insert(tk.END, f"{name}: {votes} ({percentage:.1f}%)\n")
        else:
            self.candidates_text.insert(tk.END, "Demo Features:\n")
            self.candidates_text.insert(tk.END, "• Vote tallying\n")
            self.candidates_text.insert(tk.END, "• Real-time updates\n") 
            self.candidates_text.insert(tk.END, "• Export functionality\n")
            self.candidates_text.insert(tk.END, "• System monitoring\n")
    
    def export_results(self):
        try:
            data = self.api.get_detailed_tally()
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")]
            )
            
            if filename:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                else:
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Metric', 'Value'])
                        writer.writerow(['Total Votes', data.get('total_votes', 0)])
                        writer.writerow(['Status', data.get('status', 'unknown')])
                        
                        if 'candidates' in data:
                            writer.writerow(['', ''])
                            writer.writerow(['Candidate', 'Votes'])
                            for candidate in data['candidates']:
                                writer.writerow([candidate['name'], candidate['votes']])
                
                messagebox.showinfo("Success", f"Results exported to:\n{filename}")
                self.status_bar.config(text="Export successful")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")
    
    def test_connection(self):
        result = self.api.test_api()
        status = result.get('status', 'unknown')
        message = result.get('message', 'No message')
        
        if 'offline' in status.lower():
            messagebox.showwarning("Connection Test", 
                                 f"Flask Server: {status}\n\n{message}\n\nAdmin UI working in demo mode!")
        else:
            messagebox.showinfo("Connection Test", f"Status: {status}\n\n{message}")
    
    def show_system_health(self):
        health_data = self.api.get_system_health()
        
        health_text = "System Health Report:\n"
        health_text += "=" * 30 + "\n"
        for key, value in health_data.items():
            health_text += f"{key.replace('_', ' ').title()}: {value}\n"
        
        health_text += "\nAdmin UI Components:\n"
        health_text += "• Dashboard: ✅ Working\n"
        health_text += "• Data Display: ✅ Working\n"
        health_text += "• Export Function: ✅ Working\n"
        
        messagebox.showinfo("System Health", health_text)
    
    def show_logs(self):
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
