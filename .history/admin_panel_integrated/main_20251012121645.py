import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe, Progressbar, Notebook, Entry, Text, Combobox
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import time
import threading
import json
from datetime import datetime, timedelta
from database_connector import DatabaseConnector
from blockchain_connector import BlockchainConnector
from election_manager import ElectionManager

class AdminPanel:
    def __init__(self):
        # Initialize connectors
        self.database = DatabaseConnector()
        self.blockchain = BlockchainConnector()
        self.election_manager = ElectionManager(self.database, self.blockchain)
        
        self.manipulation_attempts = 0
        self.current_election_id = 1
        
        # Create main window
        self.app = ttkb.Window(themename="superhero")
        self.app.title("BallotGuard Admin Panel - Full Integration")
        self.app.geometry("1400x900")
        self.app.minsize(1200, 800)
        
        self.setup_ui()
        self.start_auto_update()
    
    def setup_ui(self):
        """Create the complete admin interface"""
        # Title bar with status
        title_frame = Frame(self.app)
        title_frame.pack(fill="x", padx=20, pady=20)
        
        Label(title_frame, text="🗳️ BallotGuard Admin Panel", 
              font=("Arial", 24, "bold"), bootstyle="primary").pack(side="left")
        
        # Status indicators
        status_frame = Frame(title_frame)
        status_frame.pack(side="right")
        
        self.chain_status_label = Label(status_frame, text="🟢 BLOCKCHAIN SECURE", 
                                      font=("Arial", 10, "bold"), bootstyle="success")
        self.chain_status_label.pack(side="right", padx=(0, 10))
        
        self.db_status_label = Label(status_frame, text="🟢 DATABASE CONNECTED", 
                                   font=("Arial", 10, "bold"), bootstyle="info")
        self.db_status_label.pack(side="right", padx=(0, 10))
        
        # Create tabs
        notebook = Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab 1: Dashboard & Results
        self.create_dashboard_tab(notebook)
        
        # Tab 2: Election Management
        self.create_election_management_tab(notebook)
        
        # Tab 3: Create New Election
        self.create_election_creation_tab(notebook)
        
        # Tab 4: Security Monitor
        self.create_security_monitor_tab(notebook)
    
    def create_dashboard_tab(self, notebook):
        """Enhanced dashboard with election results"""
        frame = Frame(notebook)
        notebook.add(frame, text="📊 Dashboard & Results")
        
        # Election selector
        selector_frame = Labelframe(frame, text="Current Election", padding=15)
        selector_frame.pack(fill="x", pady=(0, 20))
        
        selector_grid = Frame(selector_frame)
        selector_grid.pack(fill="x")
        
        Label(selector_grid, text="Election:", font=("Arial", 12)).pack(side="left")
        
        self.election_var = tk.StringVar()
        self.election_combo = Combobox(selector_grid, textvariable=self.election_var, 
                                     state="readonly", width=40)
        self.election_combo.pack(side="left", padx=(10, 20))
        self.election_combo.bind("<<ComboboxSelected>>", self.on_election_changed)
        
        Button(selector_grid, text="🔄 Refresh Elections", 
               command=self.refresh_elections, bootstyle="secondary").pack(side="right")
        
        # Current election status
        self.election_status_frame = Labelframe(frame, text="Election Status", padding=15)
        self.election_status_frame.pack(fill="x", pady=(0, 20))
        
        self.election_status_label = Label(self.election_status_frame, 
                                         text="Select an election to view status", 
                                         font=("Arial", 12))
        self.election_status_label.pack()
        
        # Main content area
        content_frame = Frame(frame)
        content_frame.pack(fill="both", expand=True)
        
        # Left side - Statistics
        left_panel = Frame(content_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Vote statistics cards
        stats_frame = Labelframe(left_panel, text="Vote Statistics", padding=20)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        stats_grid = Frame(stats_frame)
        stats_grid.pack()
        
        # Create statistics cards
        self.create_stats_cards(stats_grid)
        
        # Candidate results
        results_frame = Labelframe(left_panel, text="Election Results", padding=20)
        results_frame.pack(fill="both", expand=True)
        
        self.results_container = Frame(results_frame)
        self.results_container.pack(fill="both", expand=True)
        
        # Right side - Controls and Info
        right_panel = Frame(content_frame)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        
        # Results controls
        controls_frame = Labelframe(right_panel, text="Results Controls", padding=15)
        controls_frame.pack(fill="x", pady=(0, 20))
        
        Button(controls_frame, text="📊 Generate Full Report", 
               command=self.generate_full_report, bootstyle="primary").pack(fill="x", pady=2)
        
        Button(controls_frame, text="📈 Export Results", 
               command=self.export_results, bootstyle="success").pack(fill="x", pady=2)
        
        Button(controls_frame, text="🔄 Refresh Data", 
               command=self.refresh_dashboard, bootstyle="secondary").pack(fill="x", pady=2)
        
        # Quick info panel
        info_frame = Labelframe(right_panel, text="Quick Info", padding=15)
        info_frame.pack(fill="both", expand=True)
        
        self.quick_info_text = Text(info_frame, height=12, width=30, 
                                  font=("Arial", 10), wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", 
                                     command=self.quick_info_text.yview)
        self.quick_info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.quick_info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y")
        
        # Load initial data
        self.refresh_elections()
    
    def create_stats_cards(self, parent):
        """Create statistics cards"""
        # Total votes card
        votes_card = Frame(parent)
        votes_card.pack(side="left", padx=20)
        
        Label(votes_card, text="Total Votes", font=("Arial", 12)).pack()
        self.total_votes_label = Label(votes_card, text="0", 
                                     font=("Arial", 24, "bold"), bootstyle="primary")
        self.total_votes_label.pack()
        
        # Turnout rate card
        turnout_card = Frame(parent)
        turnout_card.pack(side="left", padx=20)
        
        Label(turnout_card, text="Turnout Rate", font=("Arial", 12)).pack()
        self.turnout_label = Label(turnout_card, text="0.0%", 
                                 font=("Arial", 24, "bold"), bootstyle="success")
        self.turnout_label.pack()
        
        # Blockchain blocks card
        blocks_card = Frame(parent)
        blocks_card.pack(side="left", padx=20)
        
        Label(blocks_card, text="Blockchain Blocks", font=("Arial", 12)).pack()
        self.blocks_label = Label(blocks_card, text="0", 
                                font=("Arial", 24, "bold"), bootstyle="info")
        self.blocks_label.pack()
    
    def create_election_management_tab(self, notebook):
        """Election management tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🗳️ Election Management")
        
        # Elections list
        list_frame = Labelframe(frame, text="All Elections", padding=20)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Elections table
        columns = ('ID', 'Title', 'Status', 'Start Date', 'Total Votes', 'Candidates')
        self.elections_tree = ttkb.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.elections_tree.heading(col, text=col)
            self.elections_tree.column(col, width=120)
        
        elections_scrollbar = ttkb.Scrollbar(list_frame, orient="vertical", 
                                           command=self.elections_tree.yview)
        self.elections_tree.configure(yscrollcommand=elections_scrollbar.set)
        
        self.elections_tree.pack(side="left", fill="both", expand=True)
        elections_scrollbar.pack(side="right", fill="y")
        
        # Election management controls
        mgmt_controls_frame = Frame(frame)
        mgmt_controls_frame.pack(fill="x", pady=10)
        
        Button(mgmt_controls_frame, text="📊 View Results", 
               command=self.view_selected_election_results, bootstyle="primary").pack(side="left", padx=5)
        
        Button(mgmt_controls_frame, text="📈 Export Data", 
               command=self.export_selected_election, bootstyle="success").pack(side="left", padx=5)
        
        Button(mgmt_controls_frame, text="🔄 Refresh List", 
               command=self.refresh_elections_list, bootstyle="secondary").pack(side="right", padx=5)
        
        # Load elections
        self.refresh_elections_list()
    
    def create_election_creation_tab(self, notebook):
        """Election creation tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="➕ Create Election")
        
        # Scrollable frame for form
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Election form
        form_frame = Labelframe(scrollable_frame, text="Create New Election", padding=20)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        # Basic information
        basic_frame = Labelframe(form_frame, text="Basic Information", padding=15)
        basic_frame.pack(fill="x", pady=(0, 15))
        
        # Title
        title_frame = Frame(basic_frame)
        title_frame.pack(fill="x", pady=5)
        Label(title_frame, text="Election Title:*", width=15, anchor="w").pack(side="left")
        self.election_title_var = tk.StringVar()
        Entry(title_frame, textvariable=self.election_title_var, width=50).pack(side="left", padx=10)
        
        # Description
        desc_frame = Frame(basic_frame)
        desc_frame.pack(fill="x", pady=5)
        Label(desc_frame, text="Description:*", width=15, anchor="w").pack(side="left")
        self.election_desc_var = tk.StringVar()
        Entry(desc_frame, textvariable=self.election_desc_var, width=50).pack(side="left", padx=10)
        
        # Dates
        dates_frame = Frame(basic_frame)
        dates_frame.pack(fill="x", pady=5)
        
        Label(dates_frame, text="Start Date:*", width=15, anchor="w").pack(side="left")
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        Entry(dates_frame, textvariable=self.start_date_var, width=20).pack(side="left", padx=(10, 20))
        
        Label(dates_frame, text="End Date:*", width=15, anchor="w").pack(side="left")
        self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        Entry(dates_frame, textvariable=self.end_date_var, width=20).pack(side="left", padx=10)
        
        # Eligible voters
        voters_frame = Frame(basic_frame)
        voters_frame.pack(fill="x", pady=5)
        Label(voters_frame, text="Eligible Voters:*", width=15, anchor="w").pack(side="left")
        self.eligible_voters_var = tk.StringVar(value="1000")
        Entry(voters_frame, textvariable=self.eligible_voters_var, width=20).pack(side="left", padx=10)
        
        # Candidates section
        candidates_frame = Labelframe(form_frame, text="Candidates", padding=15)
        candidates_frame.pack(fill="x", pady=(0, 15))
        
        # Candidates list
        self.candidates_list_frame = Frame(candidates_frame)
        self.candidates_list_frame.pack(fill="x")
        
        self.candidate_entries = []
        self.add_candidate_entry()  # Add first candidate
        self.add_candidate_entry()  # Add second candidate
        
        # Add candidate button
        Button(candidates_frame, text="➕ Add Candidate", 
               command=self.add_candidate_entry, bootstyle="info").pack(pady=10)
        
        # Form controls
        controls_frame = Frame(form_frame)
        controls_frame.pack(fill="x", pady=20)
        
        Button(controls_frame, text="✅ Create Election", 
               command=self.create_election, bootstyle="primary").pack(side="left", padx=5)
        
        Button(controls_frame, text="🔄 Clear Form", 
               command=self.clear_election_form, bootstyle="secondary").pack(side="left", padx=5)
        
        Button(controls_frame, text="📄 Load Template", 
               command=self.load_election_template, bootstyle="info").pack(side="right", padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_security_monitor_tab(self, notebook):
        """Security monitoring tab"""
        frame = Frame(notebook)
        notebook.add(frame, text="🔒 Security Monitor")
        
        # Security status
        status_frame = Labelframe(frame, text="Security Status", padding=20)
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_grid = Frame(status_frame)
        status_grid.pack(fill="x")
        
        self.security_status = Label(status_grid, text="✅ System Secure", 
                                   font=("Arial", 14), bootstyle="success")
        self.security_status.pack(side="left")
        
        self.attempts_label = Label(status_grid, 
                                  text=f"Unauthorized attempts: {self.manipulation_attempts}")
        self.attempts_label.pack(side="right")
        
        # Test admin restrictions
        test_frame = Labelframe(frame, text="⚠️ Test Blockchain Protection", padding=20)
        test_frame.pack(fill="x", pady=(0, 20))
        
        Label(test_frame, text="These actions will BREAK the blockchain chain:", 
              font=("Arial", 12)).pack(pady=10)
        
        restriction_tests = [
            ("⚠️ Try to Change Vote Count", self.test_change_results),
            ("⚠️ Try to Delete Votes", self.test_delete_votes),
            ("⚠️ Try to Reset Chain", self.test_reset_chain),
            ("⚠️ Try to Modify Blockchain", self.test_modify_blockchain)
        ]
        
        for text, command in restriction_tests:
            Button(test_frame, text=text, command=command, 
                   bootstyle="warning-outline").pack(fill="x", pady=2)
        
        # Security log
        log_frame = Labelframe(frame, text="Security Audit Log", padding=10)
        log_frame.pack(fill="both", expand=True)
        
        self.security_log = scrolledtext.ScrolledText(log_frame, height=10, 
                                                    bg="#1a1a1a", fg="#00ff00",
                                                    font=("Consolas", 10))
        self.security_log.pack(fill="both", expand=True)
        
        self.log_security("🔐 Admin panel initialized - Full integration active")
        self.log_security("🗄️ Database connector initialized")
        self.log_security("⛓️ Blockchain connector initialized")
        self.log_security("👨‍💼 Administrator privileges: Election management enabled")
    
    # Election Management Methods
    def refresh_elections(self):
        """Refresh elections dropdown"""
        try:
            success, message, elections = self.database.get_elections()
            if success:
                election_names = [f"{e['id']}: {e['title']}" for e in elections]
                self.election_combo['values'] = election_names
                
                if election_names:
                    self.election_combo.current(0)
                    self.on_election_changed()
            else:
                messagebox.showerror("Database Error", f"Failed to load elections: {message}")
        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing elections: {str(e)}")
    
    def on_election_changed(self, event=None):
        """Handle election selection change"""
        try:
            selection = self.election_var.get()
            if not selection:
                return
            
            election_id = int(selection.split(':')[0])
            self.current_election_id = election_id
            
            # Update election manager
            success, message, election = self.election_manager.switch_election(election_id)
            
            if success:
                # Update status
                status_text = f"📊 {election['title']} | Status: {election['status'].upper()}"
                self.election_status_label.config(text=status_text)
                
                # Refresh dashboard data
                self.refresh_dashboard()
            else:
                messagebox.showerror("Election Error", message)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error changing election: {str(e)}")
    
    def refresh_dashboard(self):
        """Refresh dashboard with current election data"""
        try:
            # Get comprehensive results
            success, message, results = self.election_manager.get_comprehensive_results(self.current_election_id)
            
            if success:
                # Update statistics
                self.total_votes_label.config(text=str(results['total_votes']))
                self.turnout_label.config(text=f"{results['turnout_percentage']:.1f}%")
                
                # Update blockchain stats
                blockchain_info = self.blockchain.get_blockchain_info()
                self.blocks_label.config(text=str(blockchain_info.get('total_blocks', 0)))
                
                # Update candidate results display
                self.update_results_display(results)
                
                # Update quick info
                self.update_quick_info(results)
                
            else:
                messagebox.showerror("Results Error", message)
                
        except Exception as e:
            self.log_security(f"⚠️ Dashboard refresh error: {str(e)}")
    
    def update_results_display(self, results):
        """Update the results display with candidate information"""
        # Clear existing results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if not results['candidates']:
            Label(self.results_container, text="No candidates found", 
                  font=("Arial", 14)).pack(pady=20)
            return
        
        # Display each candidate
        for i, candidate in enumerate(results['candidates']):
            candidate_frame = Labelframe(self.results_container, 
                                       text=f"#{i+1} - {candidate['name']}", 
                                       padding=15)
            candidate_frame.pack(fill="x", pady=5, padx=10)
            
            # Candidate info
            info_frame = Frame(candidate_frame)
            info_frame.pack(fill="x")
            
            # Left side - basic info
            left_info = Frame(info_frame)
            left_info.pack(side="left", fill="x", expand=True)
            
            Label(left_info, text=f"Party: {candidate.get('party', 'Independent')}", 
                  font=("Arial", 10)).pack(anchor="w")
            Label(left_info, text=f"Votes: {candidate['votes']}", 
                  font=("Arial", 12, "bold")).pack(anchor="w")
            Label(left_info, text=f"Percentage: {candidate['percentage']:.1f}%", 
                  font=("Arial", 10)).pack(anchor="w")
            
            # Right side - progress bar
            progress_frame = Frame(info_frame)
            progress_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
            
            progress = Progressbar(progress_frame, length=300, mode='determinate',
                                 bootstyle="primary" if i == 0 else "secondary")
            progress.pack(fill="x")
            progress.config(value=candidate['percentage'])
    
    def update_quick_info(self, results):
        """Update quick info panel"""
        self.quick_info_text.delete('1.0', tk.END)
        
        info_text = f"""ELECTION OVERVIEW
================
Title: {results['title']}
Status: {results['status'].upper()}

PARTICIPATION
=============
Total Votes: {results['total_votes']}
Eligible Voters: {results['eligible_voters']}
Turnout: {results['turnout_percentage']:.1f}%

LEADING CANDIDATE
================
{results['candidates'][0]['name'] if results['candidates'] else 'None'}
Votes: {results['candidates'][0]['votes'] if results['candidates'] else 0}
Percentage: {results['candidates'][0]['percentage']:.1f}% if results['candidates'] else 0}%

BLOCKCHAIN STATUS
================
Chain Intact: {"✅ Yes" if results['blockchain_verification']['chain_intact'] else "❌ No"}
Total Blocks: {results['blockchain_verification']['total_blocks']}
Verification: {results['blockchain_verification']['verification_status']}
"""
        
        self.quick_info_text.insert('1.0', info_text)
    
    # Election Creation Methods
    def add_candidate_entry(self):
        """Add a new candidate entry field"""
        candidate_frame = Frame(self.candidates_list_frame)
        candidate_frame.pack(fill="x", pady=5)
        
        Label(candidate_frame, text=f"Candidate {len(self.candidate_entries) + 1}:", 
              width=15, anchor="w").pack(side="left")
        
        name_var = tk.StringVar()
        name_entry = Entry(candidate_frame, textvariable=name_var, width=30)
        name_entry.pack(side="left", padx=(10, 20))
        
        Label(candidate_frame, text="Party:", width=8, anchor="w").pack(side="left")
        party_var = tk.StringVar()
        party_entry = Entry(candidate_frame, textvariable=party_var, width=20)
        party_entry.pack(side="left", padx=10)
        
        # Remove button
        remove_btn = Button(candidate_frame, text="🗑️", 
                           command=lambda: self.remove_candidate_entry(candidate_frame),
                           bootstyle="danger-outline")
        remove_btn.pack(side="right", padx=10)
        
        self.candidate_entries.append({
            'frame': candidate_frame,
            'name_var': name_var,
            'party_var': party_var
        })
    
    def remove_candidate_entry(self, candidate_frame):
        """Remove a candidate entry"""
        if len(self.candidate_entries) <= 2:
            messagebox.showwarning("Minimum Candidates", "At least 2 candidates are required!")
            return
        
        # Find and remove the candidate entry
        for i, entry in enumerate(self.candidate_entries):
            if entry['frame'] == candidate_frame:
                candidate_frame.destroy()
                self.candidate_entries.pop(i)
                break
        
        # Update candidate numbers
        for i, entry in enumerate(self.candidate_entries):
            label = entry['frame'].winfo_children()[0]
            label.config(text=f"Candidate {i + 1}:")
    
    def create_election(self):
        """Create new election"""
        try:
            # Collect form data
            election_data = {
                'title': self.election_title_var.get().strip(),
                'description': self.election_desc_var.get().strip(),
                'start_date': self.start_date_var.get() + "T00:00:00",
                'end_date': self.end_date_var.get() + "T23:59:59",
                'eligible_voters': int(self.eligible_voters_var.get()),
                'candidates': []
            }
            
            # Collect candidates
            for entry in self.candidate_entries:
                name = entry['name_var'].get().strip()
                party = entry['party_var'].get().strip()
                
                if name:  # Only add if name is provided
                    candidate = {
                        'name': name,
                        'party': party or 'Independent',
                        'description': '',
                        'votes': 0
                    }
                    election_data['candidates'].append(candidate)
            
            # Create election
            success, message, election_id = self.election_manager.create_new_election(election_data)
            
            if success:
                messagebox.showinfo("Election Created", 
                                  f"✅ Election created successfully!\n\nElection ID: {election_id}\nTitle: {election_data['title']}")
                
                self.log_security(f"📊 New election created: {election_data['title']} (ID: {election_id})")
                
                # Clear form and refresh elections
                self.clear_election_form()
                self.refresh_elections()
                self.refresh_elections_list()
                
            else:
                messagebox.showerror("Election Creation Failed", f"❌ Failed to create election:\n\n{message}")
                
        except ValueError as e:
            messagebox.showerror("Input Error", "Please check your input values (eligible voters must be a number)")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error creating election:\n{str(e)}")
    
    def clear_election_form(self):
        """Clear the election creation form"""
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.eligible_voters_var.set("1000")
        
        # Clear candidates
        for entry in self.candidate_entries:
            entry['name_var'].set("")
            entry['party_var'].set("")
    
    def load_election_template(self):
        """Load election template"""
        template = self.election_manager.get_election_template()
        
        self.election_title_var.set("Sample Election 2024")
        self.election_desc_var.set("Sample election for demonstration")
        
        # Set candidate templates
        if len(self.candidate_entries) >= 2:
            self.candidate_entries[0]['name_var'].set("Alice Johnson")
            self.candidate_entries[0]['party_var'].set("Progressive Party")
            self.candidate_entries[1]['name_var'].set("Bob Smith")
            self.candidate_entries[1]['party_var'].set("Conservative Party")
        
        messagebox.showinfo("Template Loaded", "✅ Election template loaded successfully!")
    
    # Results and Analytics Methods
    def generate_full_report(self):
        """Generate comprehensive election report"""
        try:
            success, message, results = self.election_manager.get_comprehensive_results(self.current_election_id)
            
            if success:
                # Show detailed report window
                self.show_detailed_report(results)
            else:
                messagebox.showerror("Report Error", f"Failed to generate report:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report:\n{str(e)}")
    
    def show_detailed_report(self, results):
        """Show detailed report in new window"""
        report_window = tk.Toplevel(self.app)
        report_window.title(f"Detailed Report - {results['title']}")
        report_window.geometry("800x600")
        
        # Report text
        report_text = scrolledtext.ScrolledText(report_window, font=("Consolas", 11))
        report_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Generate report content
        report_content = f"""
BALLOTGUARD ELECTION REPORT
==========================
Election: {results['title']}
Generated: {results['report_metadata']['generated_at']}
Generated by: {results['report_metadata']['generated_by']}

ELECTION OVERVIEW
================
Status: {results['status'].upper()}
Total Votes: {results['total_votes']}
Eligible Voters: {results['eligible_voters']}
Turnout Rate: {results['turnout_percentage']:.2f}%

CANDIDATE RESULTS
================
"""
        
        for i, candidate in enumerate(results['candidates']):
            report_content += f"{i+1}. {candidate['name']} ({candidate.get('party', 'Independent')})\n"
            report_content += f"   Votes: {candidate['votes']} ({candidate['percentage']:.2f}%)\n\n"
        
        # Analytics
        analytics = results.get('analytics', {})
        report_content += f"""
ELECTION ANALYTICS
==================
Winner: {analytics['winner']['name'] if analytics.get('winner') else 'None'}
Competition Level: {analytics['vote_distribution_analysis']['competitive_balance']}
Distribution Type: {analytics['vote_distribution_analysis']['distribution_type']}

BLOCKCHAIN VERIFICATION
======================
Chain Status: {"INTACT" if results['blockchain_verification']['chain_intact'] else "COMPROMISED"}
Total Blocks: {results['blockchain_verification']['total_blocks']}
Verification: {results['blockchain_verification']['verification_status']}
Latest Block Hash: {results['blockchain_verification']['last_block_hash']}

DATA INTEGRITY
==============
Report Version: {results['report_metadata']['report_version']}
Data Sources: {results['report_metadata']['data_source']}
Timestamp: {results['report_metadata']['generated_at']}
"""
        
        report_text.insert('1.0', report_content)
        report_text.config(state='disabled')
        
        # Export button
        export_btn = Button(report_window, text="📄 Export Report", 
                           command=lambda: self.export_detailed_report(results))
        export_btn.pack(pady=10)
    
    def export_detailed_report(self, results):
        """Export detailed report to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                
                messagebox.showinfo("Export Complete", f"✅ Detailed report exported to:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
    
    def export_results(self):
        """Export current election results"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
            )
            
            if filename:
                success, message, export_data = self.election_manager.export_election_data(
                    self.current_election_id, include_voter_details=True)
                
                if success:
                    if filename.endswith('.json'):
                        with open(filename, 'w') as f:
                            json.dump(export_data, f, indent=2)
                    else:
                        # Convert to CSV format
                        import csv
                        with open(filename, 'w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Candidate', 'Party', 'Votes', 'Percentage'])
                            
                            results = export_data['election_results']
                            for candidate in results['candidates']:
                                writer.writerow([
                                    candidate['name'], 
                                    candidate.get('party', 'Independent'),
                                    candidate['votes'], 
                                    f"{candidate['percentage']:.2f}%"
                                ])
                    
                    messagebox.showinfo("Export Complete", f"✅ Results exported to:\n{filename}")
                else:
                    messagebox.showerror("Export Error", message)
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def refresh_elections_list(self):
        """Refresh elections list in management tab"""
        try:
            # Clear existing items
            for item in self.elections_tree.get_children():
                self.elections_tree.delete(item)
            
            success, message, elections = self.database.get_elections()
            
            if success:
                for election in elections:
                    self.elections_tree.insert('', 'end', values=(
                        election['id'],
                        election['title'],
                        election['status'].upper(),
                        election['start_date'][:10],  # Date only
                        election['total_votes'],
                        len(election['candidates'])
                    ))
            else:
                messagebox.showerror("Database Error", message)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error refreshing elections list:\n{str(e)}")
    
    def view_selected_election_results(self):
        """View results for selected election"""
        selection = self.elections_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an election to view results.")
            return
        
        item = self.elections_tree.item(selection[0])
        election_id = int(item['values'][0])
        
        # Switch to this election and show results
        success, message, election = self.election_manager.switch_election(election_id)
        if success:
            self.current_election_id = election_id
            
            # Update dropdown
            for i, value in enumerate(self.election_combo['values']):
                if value.startswith(f"{election_id}:"):
                    self.election_combo.current(i)
                    break
            
            # Switch to dashboard tab
            notebook = self.app.nametowidget(self.app.nametowidget('.!notebook'))
            notebook.select(0)  # Select first tab (Dashboard)
            self.refresh_dashboard()
        else:
            messagebox.showerror("Error", message)
    
    def export_selected_election(self):
        """Export data for selected election"""
        selection = self.elections_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an election to export.")
            return
        
        item = self.elections_tree.item(selection[0])
        election_id = int(item['values'][0])
        
        # Export election data
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            
            if filename:
                success, message, export_data = self.election_manager.export_election_data(election_id, True)
                
                if success:
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    messagebox.showinfo("Export Complete", f"✅ Election data exported to:\n{filename}")
                else:
                    messagebox.showerror("Export Error", message)
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export election data:\n{str(e)}")
    
    # Security test methods
    def test_change_results(self):
        """Test changing results - will break chain"""
        self.manipulation_attempts += 1
        
        violation = self.blockchain.break_chain_on_admin_modification("VOTE_COUNT_MODIFICATION")
        
        self.log_security("🚨 CHAIN BREAK: Administrator attempted to change results")
        
        messagebox.showerror("🚨 BLOCKCHAIN CHAIN BROKEN!", 
                           """⛓️ BLOCKCHAIN CHAIN HAS BEEN BROKEN!

🚨 Admin attempted to modify vote results
⚠️ Chain integrity compromised
🔒 Values remain intact but untrusted
📊 All blockchain operations halted

⚠️ System requires restart to restore chain integrity!""")
        
        self.update_chain_status()
        self.update_security_status()
    
    def test_delete_votes(self):
        """Test vote deletion - will break chain"""
        self.manipulation_attempts += 1
        
        violation = self.blockchain.break_chain_on_admin_modification("VOTE_DELETION")
        
        self.log_security("🚨 CHAIN BREAK: Administrator attempted to delete votes")
        
        messagebox.showerror("🚨 BLOCKCHAIN CHAIN BROKEN!", 
                           """⛓️ BLOCKCHAIN CHAIN HAS BEEN BROKEN!

🚨 Admin attempted to delete votes
⚠️ Immutability violation detected
🔒 Vote data preserved but chain compromised
📋 Audit trail integrity lost

⚠️ System requires restart to restore chain integrity!""")
        
        self.update_chain_status()
        self.update_security_status()
    
    def test_reset_chain(self):
        """Test chain reset - will break chain"""
        self.manipulation_attempts += 1
        
        violation = self.blockchain.break_chain_on_admin_modification("CHAIN_RESET")
        
        self.log_security("🚨 CHAIN BREAK: Administrator attempted to reset blockchain")
        
        messagebox.showerror("🚨 BLOCKCHAIN CHAIN BROKEN!", 
                           """⛓️ BLOCKCHAIN CHAIN HAS BEEN BROKEN!

🚨 Admin attempted to reset blockchain
⚠️ Complete chain integrity violation
🔒 Historical data compromised
📊 System security breach detected

⚠️ System requires immediate restart!""")
        
        self.update_chain_status()
        self.update_security_status()
    
    def test_modify_blockchain(self):
        """Test blockchain modification - will break chain"""
        self.manipulation_attempts += 1
        
        violation = self.blockchain.break_chain_on_admin_modification("BLOCKCHAIN_TAMPERING")
        
        self.log_security("🚨 CHAIN BREAK: Administrator attempted blockchain tampering")
        
        messagebox.showerror("🚨 BLOCKCHAIN CHAIN BROKEN!", 
                           """⛓️ BLOCKCHAIN CHAIN HAS BEEN BROKEN!

🚨 Admin attempted blockchain tampering
⚠️ Cryptographic integrity destroyed
🔒 Chain hash verification failed
🛡️ Security protocols compromised

⚠️ All blockchain operations suspended!
⚠️ System requires immediate restart!""")
        
        self.update_chain_status()
        self.update_security_status()
    
    def update_chain_status(self):
        """Update chain status indicators"""
        chain_status = self.blockchain.get_chain_status()
        
        if chain_status['broken']:
            self.chain_status_label.config(text="🔴 CHAIN BROKEN", bootstyle="danger")
        else:
            self.chain_status_label.config(text="🟢 BLOCKCHAIN SECURE", bootstyle="success")
    
    def update_security_status(self):
        """Update security status based on attempts"""
        self.attempts_label.config(text=f"Unauthorized attempts: {self.manipulation_attempts}")
        
        chain_status = self.blockchain.get_chain_status()
        
        if chain_status['broken']:
            self.security_status.config(text="🔴 Critical Alert - Chain Compromised", 
                                      bootstyle="danger")
        elif self.manipulation_attempts > 3:
            self.security_status.config(text="🟡 High Alert - Multiple Violations", 
                                      bootstyle="warning")
        elif self.manipulation_attempts > 1:
            self.security_status.config(text="🟡 Caution - Security Events", 
                                      bootstyle="warning")
    
    def log_security(self, message):
        """Add to security log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.security_log.insert(tk.END, log_entry)
        self.security_log.see(tk.END)
    
    def start_auto_update(self):
        """Start automatic data updates"""
        def auto_update():
            try:
                # Only update dashboard if it's the current tab
                current_tab = 0  # Default to dashboard
                self.refresh_dashboard()
            except:
                pass
            
            self.app.after(10000, auto_update)  # Update every 10 seconds
        
        auto_update()
    
    def run(self):
        print("🚀 BallotGuard Full Integration Admin Panel Starting...")
        print("🗄️ Database Integration: Active")
        print("⛓️ Blockchain Integration: Active") 
        print("📊 Election Management: Enabled")
        print("👨‍💼 Administrator Mode: Full Access")
        self.app.mainloop()

if __name__ == "__main__":
    app = AdminPanel()
    app.run()
