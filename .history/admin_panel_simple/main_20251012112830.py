import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe, Progressbar, Notebook
import tkinter as tk
from tkinter import messagebox
import time
import threading
import random

class SimpleAdminPanel:
    def __init__(self):
        # Vote data
        self.candidates = [
            {'id': 'A', 'name': 'Candidate A', 'votes': 89},
            {'id': 'B', 'name': 'Candidate B', 'votes': 68},
            {'id': 'C', 'name': 'Candidate C', 'votes': 45}
        ]
        self.total_votes = 202
        self.manipulation_attempts = 0
        
        # Create window
        self.app = ttkb.Window(themename="superhero")
        self.app.title("BallotGuard Admin Panel - Interactive Demo")
        self.app.geometry("1000x700")
        
        self.setup_ui()
        self.start_auto_update()
    
    def setup_ui(self):
        """Create the interface"""
        # Title
        Label(self.app, text="🗳️ BallotGuard Admin Panel", 
              font=("Arial", 24, "bold"), bootstyle="primary").pack(pady=20)
        
        # Create tabs
        notebook = Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Dashboard tab
        self.create_dashboard(notebook)
        
        # Vote Simulator tab
        self.create_simulator(notebook)
        
        # Security tab
        self.create_security(notebook)
    
    def create_dashboard(self, notebook):
        """Dashboard with live vote counts"""
        frame = Frame(notebook)
        notebook.add(frame, text="📊 Dashboard")
        
        # Total votes display
        votes_frame = Labelframe(frame, text="Total Votes", padding=20)
        votes_frame.pack(fill="x", pady=20)
        
        self.total_label = Label(votes_frame, text=str(self.total_votes), 
                               font=("Arial", 32, "bold"), bootstyle="success")
        self.total_label.pack()
        
        # Candidate progress bars
        progress_frame = Labelframe(frame, text="Live Vote Breakdown", padding=20)
        progress_frame.pack(fill="both", expand=True, pady=20)
        
        self.progress_bars = {}
        for candidate in self.candidates:
            # Candidate info
            cand_frame = Frame(progress_frame)
            cand_frame.pack(fill="x", pady=10)
            
            Label(cand_frame, text=candidate['name'], 
                  font=("Arial", 14, "bold")).pack(anchor="w")
            
            votes_label = Label(cand_frame, text=f"{candidate['votes']} votes")
            votes_label.pack(anchor="w")
            
            # Progress bar
            progress = Progressbar(cand_frame, length=500, mode='determinate',
                                 bootstyle="success-striped")
            progress.pack(fill="x", pady=5)
            
            self.progress_bars[candidate['id']] = {
                'progress': progress,
                'votes_label': votes_label
            }
        
        # Control buttons
        Button(frame, text="🔄 Refresh Data", command=self.update_display, 
               bootstyle="primary").pack(pady=10)
    
    def create_simulator(self, notebook):
        """Vote simulator tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🎯 Vote Simulator")
        
        Label(frame, text="Cast Votes Interactively", 
              font=("Arial", 18, "bold")).pack(pady=20)
        
        # Manual voting buttons
        manual_frame = Labelframe(frame, text="Manual Voting", padding=20)
        manual_frame.pack(fill="x", pady=20)
        
        for candidate in self.candidates:
            Button(manual_frame, text=f"Vote for {candidate['name']}", 
                   command=lambda c=candidate: self.cast_vote(c),
                   bootstyle="success").pack(side="left", fill="x", expand=True, padx=5)
        
        # Bulk voting
        bulk_frame = Labelframe(frame, text="Bulk Voting", padding=20)
        bulk_frame.pack(fill="x", pady=20)
        
        bulk_controls = Frame(bulk_frame)
        bulk_controls.pack()
        
        Label(bulk_controls, text="Votes to cast:").pack(side="left")
        self.bulk_entry = tk.Entry(bulk_controls, width=10)
        self.bulk_entry.insert(0, "10")
        self.bulk_entry.pack(side="left", padx=10)
        
        for candidate in self.candidates:
            Button(bulk_frame, text=f"Bulk: {candidate['name']}", 
                   command=lambda c=candidate: self.bulk_vote(c),
                   bootstyle="info").pack(side="left", fill="x", expand=True, padx=2)
        
        # Auto simulation
        auto_frame = Labelframe(frame, text="Auto Simulation", padding=20)
        auto_frame.pack(fill="x", pady=20)
        
        self.sim_running = False
        self.sim_button = Button(auto_frame, text="▶️ Start Auto Voting", 
                               command=self.toggle_simulation, bootstyle="primary")
        self.sim_button.pack()
        
        # Reset button
        Button(frame, text="🔄 Reset All Votes", command=self.reset_votes, 
               bootstyle="warning").pack(pady=20)
    
    def create_security(self, notebook):
        """Security testing tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🔒 Security Test")
        
        Label(frame, text="Vote Manipulation Protection Test", 
              font=("Arial", 18, "bold")).pack(pady=20)
        
        # Security status
        status_frame = Labelframe(frame, text="Security Status", padding=20)
        status_frame.pack(fill="x", pady=20)
        
        self.security_status = Label(status_frame, text="✅ All systems secure", 
                                   font=("Arial", 14), bootstyle="success")
        self.security_status.pack()
        
        self.attempts_label = Label(status_frame, 
                                  text=f"Blocked attempts: {self.manipulation_attempts}")
        self.attempts_label.pack()
        
        # Test buttons (these will be blocked)
        tests_frame = Labelframe(frame, text="Try These (Will Be Blocked!)", padding=20)
        tests_frame.pack(fill="x", pady=20)
        
        test_buttons = [
            ("🔢 Try Change Vote Count", "CHANGE_VOTES"),
            ("🗑️ Try Delete Votes", "DELETE_VOTES"), 
            ("✏️ Try Modify Candidate", "MODIFY_CANDIDATE"),
            ("💾 Try Hack Database", "HACK_DATABASE")
        ]
        
        for text, action in test_buttons:
            Button(tests_frame, text=text, 
                   command=lambda a=action: self.test_security(a),
                   bootstyle="warning-outline").pack(fill="x", pady=2)
        
        # Security log
        log_frame = Labelframe(frame, text="Security Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=20)
        
        self.security_log = tk.Text(log_frame, height=8, bg="#1a1a1a", fg="#00ff00")
        self.security_log.pack(fill="both", expand=True)
        self.log_security("System initialized - Security active")
    
    def cast_vote(self, candidate):
        """Cast a single vote"""
        for c in self.candidates:
            if c['id'] == candidate['id']:
                c['votes'] += 1
                break
        
        self.total_votes += 1
        self.update_display()
        messagebox.showinfo("Vote Cast", f"✅ Vote for {candidate['name']} recorded!")
    
    def bulk_vote(self, candidate):
        """Cast multiple votes"""
        try:
            num_votes = int(self.bulk_entry.get())
            if num_votes <= 0:
                raise ValueError
                
            result = messagebox.askyesno("Confirm", 
                                       f"Cast {num_votes} votes for {candidate['name']}?")
            if result:
                for c in self.candidates:
                    if c['id'] == candidate['id']:
                        c['votes'] += num_votes
                        break
                
                self.total_votes += num_votes
                self.update_display()
                messagebox.showinfo("Bulk Vote", f"✅ {num_votes} votes cast!")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")
    
    def toggle_simulation(self):
        """Start/stop auto voting"""
        if not self.sim_running:
            self.sim_running = True
            self.sim_button.config(text="⏸️ Stop Auto Voting", bootstyle="danger")
            self.run_simulation()
        else:
            self.sim_running = False
            self.sim_button.config(text="▶️ Start Auto Voting", bootstyle="primary")
    
    def run_simulation(self):
        """Auto vote simulation"""
        def simulate():
            while self.sim_running:
                candidate = random.choice(self.candidates)
                candidate['votes'] += 1
                self.total_votes += 1
                self.app.after(0, self.update_display)
                time.sleep(0.5)
        
        threading.Thread(target=simulate, daemon=True).start()
    
    def reset_votes(self):
        """Reset all votes to zero"""
        if messagebox.askyesno("Reset", "Reset all votes to zero?"):
            for candidate in self.candidates:
                candidate['votes'] = 0
            self.total_votes = 0
            self.update_display()
            messagebox.showinfo("Reset", "✅ All votes reset!")
    
    def test_security(self, action):
        """Test security protection (will block everything)"""
        self.manipulation_attempts += 1
        
        error_messages = {
            "CHANGE_VOTES": "🚨 BLOCKED: Cannot change vote counts directly!",
            "DELETE_VOTES": "🚨 BLOCKED: Cannot delete votes!",
            "MODIFY_CANDIDATE": "🚨 BLOCKED: Cannot modify candidates!",
            "HACK_DATABASE": "🚨 BLOCKED: Database access denied!"
        }
        
        message = error_messages.get(action, "🚨 BLOCKED: Unauthorized action!")
        
        # Log the attempt
        self.log_security(f"🚫 BLOCKED: {action}")
        
        # Update counter
        self.attempts_label.config(text=f"Blocked attempts: {self.manipulation_attempts}")
        
        # Show security alert
        messagebox.showerror("Security Protection Active", 
                           f"{message}\n\n❌ Action blocked by security system\n✅ Incident logged for audit")
        
        # Change security status if many attempts
        if self.manipulation_attempts > 2:
            self.security_status.config(text="🔴 HIGH ALERT - Multiple attempts!", 
                                      bootstyle="danger")
    
    def log_security(self, message):
        """Add to security log"""
        timestamp = time.strftime("%H:%M:%S")
        self.security_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.security_log.see(tk.END)
    
    def update_display(self):
        """Update all displays"""
        # Update total
        self.total_label.config(text=str(self.total_votes))
        
        # Update progress bars
        max_votes = max([c['votes'] for c in self.candidates])
        
        for candidate in self.candidates:
            pb = self.progress_bars[candidate['id']]
            pb['votes_label'].config(text=f"{candidate['votes']} votes")
            
            percentage = (candidate['votes'] / max(max_votes, 1)) * 100
            pb['progress'].config(value=percentage)
    
    def start_auto_update(self):
        """Auto-refresh display"""
        def auto_update():
            self.update_display()
            self.app.after(2000, auto_update)
        auto_update()
    
    def run(self):
        print("🚀 BallotGuard Simple Admin Panel Starting...")
        self.app.mainloop()

if __name__ == "__main__":
    app = SimpleAdminPanel()
    app.run()
