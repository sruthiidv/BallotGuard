import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe, Progressbar, Notebook, Entry, Text, Combobox
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import time
import threading
import json
from datetime import datetime, timedelta

# Import our custom modules
try:
    from database_connector import DatabaseConnector
    from blockchain_connector import BlockchainConnector
    from election_manager import ElectionManager
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Please ensure all files are in the same directory")
    exit(1)

class AdminPanel:
    def __init__(self):
        try:
            print("🚀 Initializing BallotGuard Admin Panel...")
            
            # Initialize connectors
            print("🔄 Loading database connector...")
            self.database = DatabaseConnector()
            
            print("🔄 Loading blockchain connector...")
            self.blockchain = BlockchainConnector()
            
            print("🔄 Loading election manager...")
            self.election_manager = ElectionManager(self.database, self.blockchain)
            
            self.manipulation_attempts = 0
            self.current_election_id = 1
            
            print("🔄 Creating main window...")
            # Create main window
            self.app = ttkb.Window(themename="superhero")
            self.app.title("BallotGuard Admin Panel - Full Integration")
            self.app.geometry("1400x900")
            self.app.minsize(1200, 800)
            
            print("🔄 Setting up UI...")
            self.setup_ui()
            
            print("🔄 Starting auto-update...")
            self.start_auto_update()
            
            print("✅ Admin Panel initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing Admin Panel: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize admin panel:\n{e}")
    
    def setup_ui(self):
        """Create the complete admin interface"""
        try:
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
            
            # Store notebook reference
            self.notebook = notebook
            
            # Create all tabs
            self.create_dashboard_tab(notebook)
            self.create_election_management_tab(notebook)
            self.create_election_creation_tab(notebook)
            self.create_security_monitor_tab(notebook)
            
            print("✅ UI setup completed successfully")
            
        except Exception as e:
            print(f"❌ Error setting up UI: {e}")
            messagebox.showerror("UI Error", f"Failed to setup UI:\n{e}")
    
    def create_dashboard_tab(self, notebook):
        """Enhanced dashboard with better layout for election results"""
        try:
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
                                             text="Loading election data...", 
                                             font=("Arial", 12))
            self.election_status_label.pack()
            
            # Vote statistics cards
            stats_frame = Labelframe(frame, text="Vote Statistics", padding=20)
            stats_frame.pack(fill="x", pady=(0, 20))
            
            stats_grid = Frame(stats_frame)
            stats_grid.pack()
            
            # Create statistics cards
            self.create_stats_cards(stats_grid)
            
            # Main content area with better proportions
            content_frame = Frame(frame)
            content_frame.pack(fill="both", expand=True)
            
            # Left side - Election Results (larger)
            left_panel = Frame(content_frame)
            left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
            
            # Candidate results
            results_frame = Labelframe(left_panel, text="Election Results", padding=20)
            results_frame.pack(fill="both", expand=True)
            
            # Create results container with scrolling
            self.create_results_container(results_frame)
            
            # Right side - Controls and Info
            right_panel = Frame(content_frame)
            right_panel.pack(side="right", fill="y", padx=(15, 0))
            right_panel.configure(width=400)
            
            # Results controls
            controls_frame = Labelframe(right_panel, text="Results Controls", padding=15)
            controls_frame.pack(fill="x", pady=(0, 15))
            
            Button(controls_frame, text="📊 Generate Full Report", 
                   command=self.generate_full_report, bootstyle="primary").pack(fill="x", pady=3)
            
            Button(controls_frame, text="📈 Export Results", 
                   command=self.export_results, bootstyle="success").pack(fill="x", pady=3)
            
            Button(controls_frame, text="🔄 Refresh Data", 
                   command=self.refresh_dashboard, bootstyle="secondary").pack(fill="x", pady=3)
            
            # Quick info panel - BIGGER
            info_frame = Labelframe(right_panel, text="Quick Election Info", padding=15)
            info_frame.pack(fill="both", expand=True)
            
            # Create text area with scrollbar
            text_container = Frame(info_frame)
            text_container.pack(fill="both", expand=True)
            
            self.quick_info_text = Text(text_container, 
                                      height=25,  # Made bigger
                                      width=50,   # Made wider
                                      font=("Consolas", 10), 
                                      wrap=tk.WORD,
                                      bg="#2b2b2b", 
                                      fg="#ffffff")
            
            info_scrollbar = ttk.Scrollbar(text_container, orient="vertical", 
                                         command=self.quick_info_text.yview)
            self.quick_info_text.configure(yscrollcommand=info_scrollbar.set)
            
            self.quick_info_text.pack(side="left", fill="both", expand=True)
            info_scrollbar.pack(side="right", fill="y")
            
            print("✅ Dashboard tab created successfully")
            
        except Exception as e:
            print(f"❌ Error creating dashboard tab: {e}")
    
    def create_results_container(self, parent):
        """Create scrollable results container"""
        try:
            # Create frame with scrollbar for results
            canvas = tk.Canvas(parent, highlightthickness=0)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            
            self.results_container = Frame(canvas)
            
            self.results_container.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=self.results_container, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Store canvas for later
            self.results_canvas = canvas
            
            # Initial placeholder
            Label(self.results_container, text="Loading election results...", 
                  font=("Arial", 14)).pack(pady=20)
            
        except Exception as e:
            print(f"❌ Error creating results container: {e}")
    
    def create_stats_cards(self, parent):
        """Create statistics cards"""
        try:
            # Total votes card
            votes_card = Frame(parent)
            votes_card.pack(side="left", padx=30)
            
            Label(votes_card, text="Total Votes", font=("Arial", 12)).pack()
            self.total_votes_label = Label(votes_card, text="0", 
                                         font=("Arial", 28, "bold"), bootstyle="primary")
            self.total_votes_label.pack()
            
            # Turnout rate card
            turnout_card = Frame(parent)
            turnout_card.pack(side="left", padx=30)
            
            Label(turnout_card, text="Turnout Rate", font=("Arial", 12)).pack()
            self.turnout_label = Label(turnout_card, text="0.0%", 
                                     font=("Arial", 28, "bold"), bootstyle="success")
            self.turnout_label.pack()
            
            # Blockchain blocks card
            blocks_card = Frame(parent)
            blocks_card.pack(side="left", padx=30)
            
            Label(blocks_card, text="Blockchain Blocks", font=("Arial", 12)).pack()
            self.blocks_label = Label(blocks_card, text="0", 
                                    font=("Arial", 28, "bold"), bootstyle="info")
            self.blocks_label.pack()
            
        except Exception as e:
            print(f"❌ Error creating stats cards: {e}")
    
    def create_election_management_tab(self, notebook):
        """Election management tab - simplified"""
        try:
            frame = Frame(notebook)
            notebook.add(frame, text="🗳️ Election Management")
            
            # Elections list
            list_frame = Labelframe(frame, text="All Elections", padding=20)
            list_frame.pack(fill="both", expand=True, pady=(0, 20))
            
            # Simple elections display
            self.elections_listbox = tk.Listbox(list_frame, height=15, font=("Arial", 12))
            self.elections_listbox.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Controls
            controls_frame = Frame(frame)
            controls_frame.pack(fill="x", pady=10)
            
            Button(controls_frame, text="🔄 Refresh Elections", 
                   command=self.refresh_elections_simple, bootstyle="primary").pack(side="left", padx=5)
            
            Button(controls_frame, text="📊 View Selected", 
                   command=self.view_selected_simple, bootstyle="info").pack(side="left", padx=5)
            
            print("✅ Election management tab created successfully")
            
        except Exception as e:
            print(f"❌ Error creating election management tab: {e}")
    
    def create_election_creation_tab(self, notebook):
        """Simple election creation tab"""
        try:
            frame = Frame(notebook)
            notebook.add(frame, text="➕ Create Election")
            
            # Main form
            form_frame = Labelframe(frame, text="Create New Election", padding=30)
            form_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            Label(form_frame, text="Election Title:", font=("Arial", 12)).pack(anchor="w", pady=5)
            self.election_title_var = tk.StringVar()
            Entry(form_frame, textvariable=self.election_title_var, width=60, font=("Arial", 11)).pack(fill="x", pady=5)
            
            # Description
            Label(form_frame, text="Description:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
            self.election_desc_var = tk.StringVar()
            Entry(form_frame, textvariable=self.election_desc_var, width=60, font=("Arial", 11)).pack(fill="x", pady=5)
            
            # Dates
            dates_frame = Frame(form_frame)
            dates_frame.pack(fill="x", pady=15)
            
            Label(dates_frame, text="Start Date (YYYY-MM-DD):", font=("Arial", 12)).pack(side="left")
            self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            Entry(dates_frame, textvariable=self.start_date_var, width=15).pack(side="left", padx=10)
            
            Label(dates_frame, text="End Date:", font=("Arial", 12)).pack(side="left", padx=(20, 0))
            self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            Entry(dates_frame, textvariable=self.end_date_var, width=15).pack(side="left", padx=10)
            
            # Eligible voters
            Label(form_frame, text="Eligible Voters:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
            self.eligible_voters_var = tk.StringVar(value="1000")
            Entry(form_frame, textvariable=self.eligible_voters_var, width=20).pack(anchor="w", pady=5)
            
            # Candidates
            candidates_frame = Labelframe(form_frame, text="Candidates (minimum 2)", padding=20)
            candidates_frame.pack(fill="x", pady=20)
            
            self.candidate_entries = []
            self.candidates_container = Frame(candidates_frame)
            self.candidates_container.pack(fill="x")
            
            # Add initial candidates
            self.add_simple_candidate()
            self.add_simple_candidate()
            
            Button(candidates_frame, text="➕ Add Candidate", 
                   command=self.add_simple_candidate, bootstyle="info").pack(pady=10)
            
            # Controls
            controls_frame = Frame(form_frame)
            controls_frame.pack(fill="x", pady=20)
            
            Button(controls_frame, text="✅ Create Election", 
                   command=self.create_election_simple, bootstyle="primary").pack(side="left", padx=10)
            
            Button(controls_frame, text="🔄 Clear Form", 
                   command=self.clear_form_simple, bootstyle="secondary").pack(side="left", padx=10)
            
            print("✅ Election creation tab created successfully")
            
        except Exception as e:
            print(f"❌ Error creating election creation tab: {e}")
    
    def create_security_monitor_tab(self, notebook):
        """Security monitoring tab"""
        try:
            frame = Frame(notebook)
            notebook.add(frame, text="🔒 Security Monitor")
            
            # Security status
            status_frame = Labelframe(frame, text="Security Status", padding=20)
            status_frame.pack(fill="x", pady=(0, 20))
            
            self.security_status = Label(status_frame, text="✅ System Secure", 
                                       font=("Arial", 16, "bold"), bootstyle="success")
            self.security_status.pack()
            
            self.attempts_label = Label(status_frame, 
                                      text=f"Unauthorized attempts: {self.manipulation_attempts}",
                                      font=("Arial", 12))
            self.attempts_label.pack(pady=5)
            
            # Test buttons
            test_frame = Labelframe(frame, text="⚠️ Test Blockchain Protection", padding=20)
            test_frame.pack(fill="x", pady=(0, 20))
            
            Label(test_frame, text="These actions will BREAK the blockchain chain:", 
                  font=("Arial", 12)).pack(pady=10)
            
            test_buttons = [
                ("⚠️ Try to Change Vote Count", self.test_change_results),
                ("⚠️ Try to Delete Votes", self.test_delete_votes),
                ("⚠️ Try to Reset Chain", self.test_reset_chain),
                ("⚠️ Try to Modify Blockchain", self.test_modify_blockchain)
            ]
            
            for text, command in test_buttons:
                Button(test_frame, text=text, command=command, 
                       bootstyle="warning").pack(fill="x", pady=3)
            
            # Security log
            log_frame = Labelframe(frame, text="Security Audit Log", padding=15)
            log_frame.pack(fill="both", expand=True)
            
            self.security_log = scrolledtext.ScrolledText(log_frame, height=12, 
                                                        bg="#1a1a1a", fg="#00ff00",
                                                        font=("Consolas", 10))
            self.security_log.pack(fill="both", expand=True)
            
            # Initial log entries
            self.log_security("🔐 Admin panel initialized - Full integration active")
            self.log_security("🗄️ Database connector initialized")
            self.log_security("⛓️ Blockchain connector initialized")
            self.log_security("👨‍💼 Administrator privileges: Election management enabled")
            
            print("✅ Security monitor tab created successfully")
            
        except Exception as e:
            print(f"❌ Error creating security monitor tab: {e}")
    
    # Simplified methods
    def add_simple_candidate(self):
        """Add a simple candidate entry"""
        try:
            candidate_frame = Frame(self.candidates_container)
            candidate_frame.pack(fill="x", pady=3)
            
            num = len(self.candidate_entries) + 1
            Label(candidate_frame, text=f"Candidate {num}:", width=12).pack(side="left")
            
            name_var = tk.StringVar()
            Entry(candidate_frame, textvariable=name_var, width=25).pack(side="left", padx=5)
            
            Label(candidate_frame, text="Party:", width=8).pack(side="left")
            party_var = tk.StringVar()
            Entry(candidate_frame, textvariable=party_var, width=20).pack(side="left", padx=5)
            
            self.candidate_entries.append({'name_var': name_var, 'party_var': party_var})
            
        except Exception as e:
            print(f"❌ Error adding candidate: {e}")
    
    def create_election_simple(self):
        """Create election with simple validation"""
        try:
            title = self.election_title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Election title is required!")
                return
            
            # Collect candidates
            candidates = []
            for entry in self.candidate_entries:
                name = entry['name_var'].get().strip()
                if name:
                    candidates.append({
                        'name': name,
                        'party': entry['party_var'].get().strip() or 'Independent',
                        'votes': 0
                    })
            
            if len(candidates) < 2:
                messagebox.showerror("Error", "At least 2 candidates required!")
                return
            
            election_data = {
                'title': title,
                'description': self.election_desc_var.get().strip() or 'No description',
                'start_date': self.start_date_var.get() + "T00:00:00",
                'end_date': self.end_date_var.get() + "T23:59:59",
                'eligible_voters': int(self.eligible_voters_var.get() or 1000),
                'candidates': candidates
            }
            
            success, message, election_id = self.election_manager.create_new_election(election_data)
            
            if success:
                messagebox.showinfo("Success", f"✅ Election created successfully!\nID: {election_id}")
                self.clear_form_simple()
                self.refresh_elections()
                self.log_security(f"📊 New election created: {title} (ID: {election_id})")
            else:
                messagebox.showerror("Error", f"Failed to create election:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error creating election:\n{str(e)}")
    
    def clear_form_simple(self):
        """Clear election form"""
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.eligible_voters_var.set("1000")
        
        for entry in self.candidate_entries:
            entry['name_var'].set("")
            entry['party_var'].set("")
    
    def refresh_elections_simple(self):
        """Simple elections refresh"""
        try:
            self.elections_listbox.delete(0, tk.END)
            success, message, elections = self.database.get_elections()
            
            if success:
                for election in elections:
                    display_text = f"ID: {election['id']} | {election['title']} | {election['status'].upper()}"
                    self.elections_listbox.insert(tk.END, display_text)
            else:
                self.elections_listbox.insert(tk.END, f"Error: {message}")
                
        except Exception as e:
            print(f"❌ Error refreshing elections: {e}")
    
    def view_selected_simple(self):
        """View selected election"""
        try:
            selection = self.elections_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an election to view.")
                return
            
            # Switch to dashboard tab
            self.notebook.select(0)
            messagebox.showinfo("Info", "Switched to Dashboard to view results.")
            
        except Exception as e:
            print(f"❌ Error viewing selected election: {e}")
    
    # Core methods
    def refresh_elections(self):
        """Refresh elections dropdown"""
        try:
            success, message, elections = self.database.get_elections()
            if success and elections:
                election_names = [f"{e['id']}: {e['title']}" for e in elections]
                self.election_combo['values'] = election_names
                
                if election_names:
                    self.election_combo.current(0)
                    self.on_election_changed()
                    
        except Exception as e:
            print(f"❌ Error refreshing elections: {e}")
    
    def on_election_changed(self, event=None):
        """Handle election selection change"""
        try:
            selection = self.election_var.get()
            if selection:
                election_id = int(selection.split(':')[0])
                self.current_election_id = election_id
                self.refresh_dashboard()
        except Exception as e:
            print(f"❌ Error changing election: {e}")
    
    def refresh_dashboard(self):
        """Refresh dashboard data"""
        try:
            success, message, results = self.election_manager.get_comprehensive_results(self.current_election_id)
            
            if success:
                # Update statistics
                self.total_votes_label.config(text=str(results['total_votes']))
                self.turnout_label.config(text=f"{results['turnout_percentage']:.1f}%")
                
                blockchain_info = self.blockchain.get_blockchain_info()
                self.blocks_label.config(text=str(blockchain_info.get('total_blocks', 0)))
                
                # Update status
                status_text = f"📊 {results['title']} | Status: {results['status'].upper()}"
                self.election_status_label.config(text=status_text)
                
                # Update results display
                self.update_results_display(results)
                
                # Update quick info
                self.update_quick_info(results)
                
        except Exception as e:
            print(f"❌ Error refreshing dashboard: {e}")
    
    def update_results_display(self, results):
        """Update results display with better formatting"""
        try:
            # Clear existing results
            for widget in self.results_container.winfo_children():
                widget.destroy()
            
            if not results.get('candidates'):
                Label(self.results_container, text="No candidates found", 
                      font=("Arial", 16)).pack(pady=30)
                return
            
            # Title
            Label(self.results_container, text="🏆 ELECTION RESULTS", 
                  font=("Arial", 20, "bold"), bootstyle="primary").pack(pady=10)
            
            # Display candidates
            for i, candidate in enumerate(results['candidates']):
                rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                
                # Candidate frame
                cand_frame = Labelframe(self.results_container, 
                                      text=f"{rank} {candidate['name']}", 
                                      padding=20)
                cand_frame.pack(fill="x", padx=20, pady=10)
                
                # Info grid
                info_frame = Frame(cand_frame)
                info_frame.pack(fill="x")
                
                # Left side info
                left_info = Frame(info_frame)
                left_info.pack(side="left", fill="x", expand=True)
                
                Label(left_info, text=f"Party: {candidate.get('party', 'Independent')}", 
                      font=("Arial", 12)).pack(anchor="w")
                Label(left_info, text=f"Votes: {candidate['votes']:,}", 
                      font=("Arial", 14, "bold")).pack(anchor="w")
                Label(left_info, text=f"Percentage: {candidate['percentage']:.1f}%", 
                      font=("Arial", 12)).pack(anchor="w")
                
                # Progress bar
                progress_frame = Frame(info_frame)
                progress_frame.pack(side="right", padx=20)
                
                progress = Progressbar(progress_frame, length=300, mode='determinate')
                progress.pack()
                progress.config(value=candidate['percentage'])
            
            # Update scroll region
            self.results_container.update_idletasks()
            self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))
            
        except Exception as e:
            print(f"❌ Error updating results display: {e}")
    
    def update_quick_info(self, results):
        """Update quick info with comprehensive data"""
        try:
            self.quick_info_text.delete('1.0', tk.END)
            
            candidates = results.get('candidates', [])
            leading_candidate = candidates[0] if candidates else None
            
            info_text = f"""
🗳️ ELECTION OVERVIEW
{'='*50}
📊 Title: {results['title']}
🔄 Status: {results['status'].upper()}
📅 Election ID: {results.get('election_id', 'N/A')}

👥 PARTICIPATION METRICS  
{'='*50}
✅ Total Votes Cast: {results['total_votes']:,}
👤 Eligible Voters: {results['eligible_voters']:,}
📈 Turnout Rate: {results['turnout_percentage']:.1f}%
❌ Abstentions: {results['eligible_voters'] - results['total_votes']:,}

🏆 LEADING CANDIDATE
{'='*50}
"""
            
            if leading_candidate:
                info_text += f"""👑 Name: {leading_candidate['name']}
🎯 Party: {leading_candidate.get('party', 'Independent')}
🗳️ Votes: {leading_candidate['votes']:,}
📊 Percentage: {leading_candidate['percentage']:.1f}%"""
                
                if len(candidates) > 1:
                    margin = leading_candidate['votes'] - candidates[1]['votes']
                    info_text += f"\n🎖️ Margin: +{margin:,} votes"
            else:
                info_text += "❌ No candidates available"
            
            info_text += f"""

📋 CANDIDATE SUMMARY
{'='*50}
🎪 Total Candidates: {len(candidates)}"""
            
            for i, candidate in enumerate(candidates[:5]):  # Show top 5
                position = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                info_text += f"""
{position} {candidate['name']}: {candidate['votes']:,} ({candidate['percentage']:.1f}%)"""
            
            if len(candidates) > 5:
                info_text += f"\n... and {len(candidates) - 5} more candidates"
            
            blockchain_verification = results.get('blockchain_verification', {})
            info_text += f"""

🔗 BLOCKCHAIN STATUS
{'='*50}
⛓️ Chain Status: {"✅ INTACT" if blockchain_verification.get('chain_intact') else "❌ COMPROMISED"}
📦 Total Blocks: {blockchain_verification.get('total_blocks', 0):,}
🔍 Verification: {blockchain_verification.get('verification_status', 'Unknown')}

⏰ LAST UPDATED
{'='*50}
🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}
👨‍💼 Generated by: Administrator
🔄 Auto-refresh: Every 10 seconds
"""
            
            self.quick_info_text.insert('1.0', info_text)
            
        except Exception as e:
            print(f"❌ Error updating quick info: {e}")
    
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
        
        self.update_security_status()
    
    def update_security_status(self):
        """Update security status"""
        self.attempts_label.config(text=f"Unauthorized attempts: {self.manipulation_attempts}")
        
        if self.manipulation_attempts > 0:
            self.security_status.config(text="🔴 Security Breach Detected", bootstyle="danger")
            self.chain_status_label.config(text="🔴 CHAIN BROKEN", bootstyle="danger")
    
    def log_security(self, message):
        """Add to security log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.security_log.insert(tk.END, log_entry)
        self.security_log.see(tk.END)
    
    def generate_full_report(self):
        """Generate full report"""
        try:
            success, message, results = self.election_manager.get_comprehensive_results(self.current_election_id)
            
            if success:
                report_window = tk.Toplevel(self.app)
                report_window.title(f"Full Report - {results['title']}")
                report_window.geometry("800x600")
                
                report_text = scrolledtext.ScrolledText(report_window, font=("Consolas", 11))
                report_text.pack(fill="both", expand=True, padx=20, pady=20)
                
                report_content = f"""
BALLOTGUARD ELECTION REPORT
{'='*50}
Election: {results['title']}
Status: {results['status'].upper()}
Total Votes: {results['total_votes']:,}
Eligible Voters: {results['eligible_voters']:,}
Turnout: {results['turnout_percentage']:.2f}%

CANDIDATE RESULTS:
{'='*50}
"""
                
                for i, candidate in enumerate(results['candidates']):
                    report_content += f"{i+1}. {candidate['name']} ({candidate.get('party', 'Independent')})\n"
                    report_content += f"   Votes: {candidate['votes']:,} ({candidate['percentage']:.2f}%)\n\n"
                
                report_content += f"""
BLOCKCHAIN VERIFICATION:
{'='*50}
Chain Status: {"INTACT" if results['blockchain_verification']['chain_intact'] else "COMPROMISED"}
Total Blocks: {results['blockchain_verification']['total_blocks']:,}
Verification: {results['blockchain_verification']['verification_status']}

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                report_text.insert('1.0', report_content)
                report_text.config(state='disabled')
                
            else:
                messagebox.showerror("Report Error", f"Failed to generate report:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report:\n{str(e)}")
    
    def export_results(self):
        """Export election results"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            
            if filename:
                success, message, export_data = self.election_manager.export_election_data(
                    self.current_election_id, include_voter_details=False)
                
                if success:
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                    
                    messagebox.showinfo("Export Complete", f"✅ Results exported to:\n{filename}")
                else:
                    messagebox.showerror("Export Error", message)
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
    
    def start_auto_update(self):
        """Start automatic updates"""
        def auto_update():
            try:
                self.refresh_dashboard()
            except:
                pass
            self.app.after(15000, auto_update)  # Update every 15 seconds
        
        # Initial delay before first update
        self.app.after(2000, auto_update)
    
    def run(self):
        """Run the admin panel"""
        try:
            print("🚀 BallotGuard Admin Panel Starting...")
            print("🗄️ Database Integration: Active")
            print("⛓️ Blockchain Integration: Active") 
            print("📊 Election Management: Enabled")
            print("👨‍💼 Administrator Mode: Full Access")
            print("✅ Admin Panel ready!")
            
            # Load initial data
            self.refresh_elections()
            
            # Start the application
            self.app.mainloop()
            
        except Exception as e:
            print(f"❌ Error running admin panel: {e}")
            messagebox.showerror("Runtime Error", f"Failed to run admin panel:\n{e}")

def main():
    """Main function"""
    try:
        print("🔄 Starting BallotGuard Admin Panel...")
        app = AdminPanel()
        app.run()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        messagebox.showerror("Critical Error", f"Failed to start application:\n{e}")

if __name__ == "__main__":
    main()
