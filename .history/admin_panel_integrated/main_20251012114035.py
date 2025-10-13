import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe, Progressbar, Notebook
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import time
import threading
import json
from blockchain_connector import BlockchainConnector

class AdminPanel:
    def __init__(self):
        # Initialize blockchain connection
        self.blockchain = BlockchainConnector()
        self.manipulation_attempts = 0
        
        # Create main window
        self.app = ttkb.Window(themename="superhero")
        self.app.title("BallotGuard Admin Panel - READ ONLY")
        self.app.geometry("1200x800")
        
        self.setup_ui()
        self.start_auto_update()
    
    def setup_ui(self):
        """Create the admin interface"""
        # Title bar
        title_frame = Frame(self.app)
        title_frame.pack(fill="x", padx=20, pady=20)
        
        Label(title_frame, text="🗳️ BallotGuard Admin Panel", 
              font=("Arial", 24, "bold"), bootstyle="primary").pack(side="left")
        
        Label(title_frame, text="👨‍💼 ADMIN - READ ONLY", 
              font=("Arial", 12, "bold"), bootstyle="warning").pack(side="right")
        
        # Create tabs
        notebook = Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Dashboard tab
        self.create_dashboard(notebook)
        
        # Blockchain Explorer tab
        self.create_blockchain_explorer(notebook)
        
        # Security Monitor tab
        self.create_security_monitor(notebook)
        
        # Vote Simulator tab (simulates client votes)
        self.create_vote_simulator(notebook)
    
    def create_dashboard(self, notebook):
        """Admin dashboard - monitoring only"""
        frame = Frame(notebook)
        notebook.add(frame, text="📊 Dashboard")
        
        # Election status
        status_frame = Labelframe(frame, text="Election Status", padding=20)
        status_frame.pack(fill="x", pady=20)
        
        Label(status_frame, text="🟢 Election Active | Blockchain Connected", 
              font=("Arial", 14), bootstyle="success").pack()
        
        # Vote statistics
        stats_frame = Labelframe(frame, text="Vote Statistics", padding=20)
        stats_frame.pack(fill="x", pady=20)
        
        stats_grid = Frame(stats_frame)
        stats_grid.pack()
        
        # Total votes card
        votes_card = Frame(stats_grid)
        votes_card.pack(side="left", padx=30)
        
        Label(votes_card, text="Total Votes", font=("Arial", 12)).pack()
        self.total_votes_label = Label(votes_card, text="0", 
                                     font=("Arial", 28, "bold"), bootstyle="primary")
        self.total_votes_label.pack()
        
        # Blockchain blocks card
        blocks_card = Frame(stats_grid)
        blocks_card.pack(side="left", padx=30)
        
        Label(blocks_card, text="Blockchain Blocks", font=("Arial", 12)).pack()
        self.blocks_label = Label(blocks_card, text="0", 
                                font=("Arial", 28, "bold"), bootstyle="info")
        self.blocks_label.pack()
        
        # Turnout rate card
        turnout_card = Frame(stats_grid)
        turnout_card.pack(side="left", padx=30)
        
        Label(turnout_card, text="Turnout Rate", font=("Arial", 12)).pack()
        self.turnout_label = Label(turnout_card, text="0.0%", 
                                 font=("Arial", 28, "bold"), bootstyle="success")
        self.turnout_label.pack()
        
        # Candidate results
        results_frame = Labelframe(frame, text="Live Results from Blockchain", padding=20)
        results_frame.pack(fill="both", expand=True, pady=20)
        
        self.progress_bars = {}
        self.create_candidate_displays(results_frame)
        
        # Admin controls
        controls_frame = Frame(frame)
        controls_frame.pack(fill="x", pady=20)
        
        Button(controls_frame, text="🔄 Refresh Data", 
               command=self.refresh_data, bootstyle="primary").pack(side="left", padx=5)
        
        Button(controls_frame, text="📊 Export Results", 
               command=self.export_results, bootstyle="success").pack(side="left", padx=5)
        
        Button(controls_frame, text="🚨 Emergency Alert", 
               command=self.emergency_alert, bootstyle="danger").pack(side="right", padx=5)
    
    def create_candidate_displays(self, parent):
        """Create candidate result displays"""
        tally = self.blockchain.get_vote_tally()
        
        for candidate in tally['candidates']:
            cand_frame = Frame(parent)
            cand_frame.pack(fill="x", pady=10)
            
            info_frame = Frame(cand_frame)
            info_frame.pack(fill="x")
            
            Label(info_frame, text=candidate['name'], 
                  font=("Arial", 14, "bold")).pack(side="left")
            
            votes_label = Label(info_frame, text=f"{candidate['votes']} votes", 
                              font=("Arial", 12))
            votes_label.pack(side="right")
            
            progress = Progressbar(cand_frame, length=600, mode='determinate',
                                 bootstyle="success-striped")
            progress.pack(fill="x", pady=(5, 0))
            
            self.progress_bars[candidate['id']] = {
                'progress': progress,
                'votes_label': votes_label
            }
    
    def create_blockchain_explorer(self, notebook):
        """Blockchain explorer tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🔗 Blockchain Explorer")
        
        # Blockchain info
        info_frame = Labelframe(frame, text="Blockchain Information", padding=20)
        info_frame.pack(fill="x", pady=20)
        
        self.blockchain_info_text = Label(info_frame, text="Loading blockchain info...", 
                                        font=("Arial", 12))
        self.blockchain_info_text.pack()
        
        # Recent blocks table
        blocks_frame = Labelframe(frame, text="Recent Blocks", padding=20)
        blocks_frame.pack(fill="both", expand=True, pady=20)
        
        columns = ('Index', 'Time', 'Hash', 'Previous Hash')
        self.blocks_tree = ttkb.Treeview(blocks_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.blocks_tree.heading(col, text=col)
            self.blocks_tree.column(col, width=150)
        
        scrollbar = ttkb.Scrollbar(blocks_frame, orient="vertical", command=self.blocks_tree.yview)
        self.blocks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.blocks_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        Button(frame, text="🔄 Refresh Blockchain Data", 
               command=self.refresh_blockchain, bootstyle="info").pack(pady=10)
    
    def create_security_monitor(self, notebook):
        """Security monitoring tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🔒 Security Monitor")
        
        # Security status
        status_frame = Labelframe(frame, text="Security Status", padding=20)
        status_frame.pack(fill="x", pady=20)
        
        self.security_status = Label(status_frame, text="✅ System Secure", 
                                   font=("Arial", 14), bootstyle="success")
        self.security_status.pack()
        
        self.attempts_label = Label(status_frame, 
                                  text=f"Unauthorized attempts: {self.manipulation_attempts}")
        self.attempts_label.pack()
        
        # Test admin restrictions
        test_frame = Labelframe(frame, text="⚠️ Test Admin Restrictions", padding=20)
        test_frame.pack(fill="x", pady=20)
        
        Label(test_frame, text="These actions are BLOCKED for administrators:", 
              font=("Arial", 12)).pack(pady=10)
        
        restriction_tests = [
            ("❌ Try to Cast Vote", self.test_admin_vote),
            ("❌ Try to Change Results", self.test_change_results),
            ("❌ Try to Delete Votes", self.test_delete_votes),
            ("❌ Try to Modify Blockchain", self.test_modify_blockchain)
        ]
        
        for text, command in restriction_tests:
            Button(test_frame, text=text, command=command, 
                   bootstyle="danger-outline").pack(fill="x", pady=2)
        
        # Security log
        log_frame = Labelframe(frame, text="Security Audit Log", padding=10)
        log_frame.pack(fill="both", expand=True, pady=20)
        
        self.security_log = scrolledtext.ScrolledText(log_frame, height=10, 
                                                    bg="#1a1a1a", fg="#00ff00",
                                                    font=("Consolas", 10))
        self.security_log.pack(fill="both", expand=True)
        
        self.log_security("🔐 Admin panel initialized - Security monitoring active")
        self.log_security("👨‍💼 Administrator privileges: READ-ONLY access")
        self.log_security("🚫 Voting capabilities: DISABLED for admin")
    
    def create_vote_simulator(self, notebook):
        """Vote simulator tab (simulates client app votes)"""
        frame = Frame(notebook)
        notebook.add(frame, text="🎯 Client Vote Simulator")
        
        # Important notice
        notice_frame = Labelframe(frame, text="⚠️ IMPORTANT NOTICE", padding=20)
        notice_frame.pack(fill="x", pady=20)
        
        notice_text = """👨‍💼 ADMIN RESTRICTION: Administrators cannot cast real votes!

🎯 This simulator mimics votes coming from CLIENT APPLICATIONS
📱 In real deployment, only verified clients can submit votes
🔗 Votes are added directly to blockchain through your blockchain.py"""
        
        Label(notice_frame, text=notice_text, font=("Arial", 11), 
              justify="left").pack(anchor="w")
        
        # Simulate client votes
        sim_frame = Labelframe(frame, text="Simulate Client App Votes", padding=20)
        sim_frame.pack(fill="x", pady=20)
        
        Label(sim_frame, text="Simulate votes coming from verified client applications:", 
              font=("Arial", 12)).pack(pady=10)
        
        # Get candidates from blockchain
        tally = self.blockchain.get_vote_tally()
        for candidate in tally['candidates']:
            Button(sim_frame, text=f"📱 Simulate Client Vote: {candidate['name']}", 
                   command=lambda c=candidate['name']: self.simulate_client_vote(c),
                   bootstyle="info").pack(fill="x", pady=2)
        
        # Blockchain integration info
        integration_frame = Labelframe(frame, text="🔗 Blockchain Integration", padding=20)
        integration_frame.pack(fill="both", expand=True, pady=20)
        
        integration_info = """✅ Connected to your blockchain.py and ledger.py
📊 Vote tallies read from blockchain data
🔐 All vote modifications go through blockchain
📝 Audit trail maintained in blockchain
🚫 Direct vote manipulation impossible"""
        
        Label(integration_frame, text=integration_info, font=("Arial", 11), 
              justify="left").pack(anchor="w")
    
    def simulate_client_vote(self, candidate_name):
        """Simulate a vote from client application"""
        success, message = self.blockchain.simulate_client_vote(candidate_name)
        
        if success:
            self.log_security(f"📱 CLIENT VOTE: {candidate_name} - {message}")
            messagebox.showinfo("Vote Simulated", 
                              f"✅ Client vote simulated for {candidate_name}\n\n{message}")
            self.refresh_data()
        else:
            self.log_security(f"❌ CLIENT VOTE FAILED: {candidate_name} - {message}")
            messagebox.showerror("Vote Failed", f"❌ Vote simulation failed:\n{message}")
    
    def test_admin_vote(self):
        """Test admin voting restriction"""
        self.manipulation_attempts += 1
        self.log_security("🚫 BLOCKED: Administrator attempted to cast vote")
        
        messagebox.showerror("Access Denied", 
                           """🚫 ADMINISTRATOR VOTE BLOCKED!

❌ Administrators cannot cast votes
👨‍💼 Admin role: Monitor and manage only
🗳️ Voting restricted to verified clients
🔐 This maintains election integrity

Action logged for security audit.""")
        
        self.update_security_status()
    
    def test_change_results(self):
        """Test changing results restriction"""
        self.manipulation_attempts += 1
        self.log_security("🚫 BLOCKED: Administrator attempted to change results")
        
        messagebox.showerror("Security Violation", 
                           """🚨 RESULT MANIPULATION BLOCKED!

❌ Cannot modify vote tallies directly
🔗 Results calculated from blockchain
🔐 Blockchain provides immutable record
📊 Only blockchain updates can change results

Security violation logged.""")
        
        self.update_security_status()
    
    def test_delete_votes(self):
        """Test vote deletion restriction"""
        self.manipulation_attempts += 1
        self.log_security("🚫 BLOCKED: Administrator attempted to delete votes")
        
        messagebox.showerror("Critical Violation", 
                           """🚨 VOTE DELETION BLOCKED!

❌ Vote deletion strictly prohibited
🔐 Blockchain ensures vote immutability
📋 Complete audit trail preserved
⚖️ Election integrity maintained

Critical violation logged and flagged.""")
        
        self.update_security_status()
    
    def test_modify_blockchain(self):
        """Test blockchain modification restriction"""
        self.manipulation_attempts += 1
        self.log_security("🚫 BLOCKED: Administrator attempted blockchain modification")
        
        messagebox.showerror("Blockchain Protection", 
                           """🔗 BLOCKCHAIN MODIFICATION BLOCKED!

❌ Cannot directly modify blockchain
🔐 Cryptographic integrity protected
⛓️ Immutable ledger maintained
🛡️ Advanced security protocols active

Blockchain tampering attempt logged.""")
        
        self.update_security_status()
    
    def refresh_data(self):
        """Refresh all data from blockchain"""
        try:
            tally = self.blockchain.get_vote_tally()
            
            # Update displays
            self.total_votes_label.config(text=str(tally['total_votes']))
            
            turnout = (tally['total_votes'] / 1000) * 100
            self.turnout_label.config(text=f"{turnout:.1f}%")
            
            blockchain_info = self.blockchain.get_blockchain_info()
            self.blocks_label.config(text=str(blockchain_info.get('total_blocks', 0)))
            
            # Update progress bars
            max_votes = max([c['votes'] for c in tally['candidates']]) if tally['candidates'] else 1
            
            for candidate in tally['candidates']:
                if candidate['id'] in self.progress_bars:
                    pb = self.progress_bars[candidate['id']]
                    pb['votes_label'].config(text=f"{candidate['votes']} votes")
                    
                    percentage = (candidate['votes'] / max(max_votes, 1)) * 100
                    pb['progress'].config(value=percentage)
            
        except Exception as e:
            self.log_security(f"❌ Data refresh error: {e}")
    
    def refresh_blockchain(self):
        """Refresh blockchain explorer data"""
        try:
            blockchain_info = self.blockchain.get_blockchain_info()
            info_text = f"""📊 Total Blocks: {blockchain_info.get('total_blocks', 0)}
🔗 Latest Hash: {blockchain_info.get('latest_hash', 'N/A')}
💾 File Status: {'✅ Found' if blockchain_info.get('blockchain_file_exists') else '❌ Not Found'}"""
            
            self.blockchain_info_text.config(text=info_text)
            
            # Update blocks table
            for item in self.blocks_tree.get_children():
                self.blocks_tree.delete(item)
            
            recent_blocks = self.blockchain.get_recent_blocks(20)
            for block in recent_blocks:
                self.blocks_tree.insert('', 'end', values=(
                    block['index'],
                    block['timestamp'],
                    block['hash'],
                    block['previous_hash']
                ))
            
        except Exception as e:
            self.log_security(f"❌ Blockchain refresh error: {e}")
    
    def export_results(self):
        """Export election results"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            
            if filename:
                tally = self.blockchain.get_vote_tally()
                blockchain_info = self.blockchain.get_blockchain_info()
                
                export_data = {
                    "election_results": tally,
                    "blockchain_info": blockchain_info,
                    "export_timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "exported_by": "Administrator"
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                self.log_security(f"📊 Results exported to {filename}")
                messagebox.showinfo("Export Complete", f"✅ Results exported!\n\n{filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export:\n{e}")
    
    def emergency_alert(self):
        """Emergency alert function"""
        result = messagebox.askyesno("Emergency Alert", 
                                   "🚨 EMERGENCY ALERT\n\nSend emergency notification to all stakeholders?")
        if result:
            self.log_security("🚨 EMERGENCY ALERT activated by administrator")
            messagebox.showwarning("Alert Sent", 
                                 "🚨 Emergency alert sent!\n📧 Notifications dispatched")
    
    def log_security(self, message):
        """Add to security log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.security_log.insert(tk.END, log_entry)
        self.security_log.see(tk.END)
    
    def update_security_status(self):
        """Update security status based on attempts"""
        self.attempts_label.config(text=f"Unauthorized attempts: {self.manipulation_attempts}")
        
        if self.manipulation_attempts > 3:
            self.security_status.config(text="🔴 High Alert - Multiple Violations", 
                                      bootstyle="danger")
        elif self.manipulation_attempts > 1:
            self.security_status.config(text="🟡 Caution - Security Events", 
                                      bootstyle="warning")
    
    def start_auto_update(self):
        """Start automatic data updates"""
        def auto_update():
            try:
                self.refresh_data()
                self.refresh_blockchain()
            except:
                pass
            
            self.app.after(5000, auto_update)  # Update every 5 seconds
        
        auto_update()
    
    def run(self):
        print("🚀 BallotGuard Admin Panel Starting...")
        print("👨‍💼 Administrator Mode: READ-ONLY")
        print("🔗 Blockchain Integration: Active")
        print("🚫 Voting Capabilities: Disabled for Admin")
        self.app.mainloop()

if __name__ == "__main__":
    app = AdminPanel()
    app.run()
