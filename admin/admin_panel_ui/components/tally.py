import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from utils.api_client import APIClient
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(parent_dir, 'utils'))
    from api_client import APIClient

class TallyComponent(ttk.Frame):
    def __init__(self, parent, api_client: APIClient):
        super().__init__(parent)
        self.api_client = api_client
        self.selected_election = None
        self.setup_ui()
        self.load_elections()

    def setup_ui(self):
        self.style = ttk.Style()
        
        # Custom styles
        self.style.configure("Title.TLabel", 
                           font=("Segoe UI", 16, "bold"), 
                           foreground="#2c3e50")
        
        self.style.configure("Stats.TLabel", 
                           font=("Segoe UI", 12),
                           foreground="#1e40af")
                           
        self.style.configure("Winner.TLabel",
                           font=("Segoe UI", 14, "bold"),
                           foreground="#059669")
        
        # Title
        ttk.Label(self, 
                 text="🗳️ Election Results & Blockchain Verification",
                 style="Title.TLabel").pack(pady=(0, 20))
        
        # Election Selector
        selector_frame = ttk.LabelFrame(self, text="Select Election", padding=10)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        selection_container = ttk.Frame(selector_frame)
        selection_container.pack(fill=tk.X, expand=True)
        
        self.election_var = tk.StringVar()
        self.election_combobox = ttk.Combobox(selection_container, 
                                             textvariable=self.election_var,
                                             font=("Segoe UI", 11))
        self.election_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.election_combobox.bind('<<ComboboxSelected>>', self.on_election_selected)
        
        refresh_btn = ttk.Button(selection_container,
                               text="🔄 Refresh",
                               command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT)

        # Results Display
        self.results_frame = ttk.LabelFrame(self, text="Election Results", padding=15)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Winner Display
        self.winner_frame = ttk.Frame(self.results_frame)
        self.winner_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.winner_label = ttk.Label(self.winner_frame, text="", style="Winner.TLabel")
        self.winner_label.pack()

        # Stats Frame
        stats_frame = ttk.Frame(self.results_frame)
        stats_frame.pack(fill=tk.X, pady=10)

        self.total_voters_label = ttk.Label(stats_frame, text="Total Eligible Voters: -")
        self.total_voters_label.pack(side=tk.LEFT, padx=10)

        self.votes_cast_label = ttk.Label(stats_frame, text="Votes Cast: -")
        self.votes_cast_label.pack(side=tk.LEFT, padx=10)

        self.turnout_label = ttk.Label(stats_frame, text="Turnout: -")
        self.turnout_label.pack(side=tk.LEFT, padx=10)

        # Blockchain Status Frame
        self.blockchain_frame = ttk.LabelFrame(self.results_frame, text="Blockchain Status", padding=10)
        self.blockchain_frame.pack(fill=tk.X, pady=10)

        self.blockchain_status_label = ttk.Label(self.blockchain_frame, text="Not verified")
        self.blockchain_status_label.pack(side=tk.LEFT, padx=10)

        verify_button = ttk.Button(self.blockchain_frame, text="Verify Blockchain", command=self.verify_blockchain)
        verify_button.pack(side=tk.RIGHT, padx=10)

        # Candidates Results Frame
        self.candidates_frame = ttk.Frame(self.results_frame)
        self.candidates_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Paillier Info
        ttk.Label(self.results_frame, 
                 text="🔒 Results are computed using Paillier homomorphic encryption.\nOnly the final tally is decrypted, preserving vote privacy.",
                 foreground="navy").pack(pady=10)

    def load_elections(self):
        try:
            success, elections = self.api_client.get_elections()
            if not success:
                messagebox.showerror("Error", f"Failed to load elections: {elections}")
                return
            self.election_combobox['values'] = [f"{e['name']} ({e['election_id']}) - {e['status']}" 
                                              for e in elections]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load elections: {str(e)}")

    def on_election_selected(self, event):
        if not self.election_var.get():
            return

        election_id = self.election_var.get().split('(')[1].split(')')[0]
        self.selected_election = election_id
        self.load_results(election_id)

    def load_results(self, election_id):
        try:
            success, results = self.api_client.get_election_results(election_id)
            if not success:
                messagebox.showerror("Error", f"Failed to load results: {results}")
                return
            
            # Update stats
            self.total_voters_label.config(text=f"Total Eligible Voters: {results.get('eligible_voters', 'N/A')}")
            self.votes_cast_label.config(text=f"Votes Cast: {results.get('total_votes', 0)}")
            turnout = results.get('turnout_percentage', 0)
            self.turnout_label.config(text=f"Turnout: {turnout:.1f}%" if isinstance(turnout, (int, float)) else "Turnout: N/A")

            # Clear existing candidate results
            for widget in self.candidates_frame.winfo_children():
                widget.destroy()

            # Create header
            header_frame = ttk.Frame(self.candidates_frame)
            header_frame.pack(fill=tk.X, pady=5)
            ttk.Label(header_frame, text="Candidate", width=30).pack(side=tk.LEFT, padx=5)
            ttk.Label(header_frame, text="Votes", width=10).pack(side=tk.LEFT, padx=5)
            ttk.Label(header_frame, text="Percentage", width=10).pack(side=tk.LEFT, padx=5)

            # Display candidate results
            results_container = ttk.Frame(self.candidates_frame)
            results_container.pack(fill=tk.BOTH, expand=True)

            # Scrollable canvas for results
            canvas = tk.Canvas(results_container, height=400)
            scrollbar = ttk.Scrollbar(results_container, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
            canvas.configure(yscrollcommand=scrollbar.set)

            # Calculate maximum votes for winner highlighting
            max_votes = max(c['votes'] for c in results['results']) if results['results'] else 0

            # Update winner display
            winners = [c for c in results['results'] if c['votes'] == max_votes]
            if winners:
                if len(winners) > 1:
                    # Tie scenario
                    names = ", ".join(w['name'] for w in winners)
                    self.winner_label.config(
                        text=f"🏆 TIE between: {names}\nEach with {max_votes} votes",
                        foreground="orange"
                    )
                else:
                    # Clear winner
                    winner = winners[0]
                    self.winner_label.config(
                        text=f"🏆 WINNER: {winner['name']}\n{winner['votes']} votes ({winner['percentage']:.1f}%)",
                        foreground="green"
                    )
            else:
                self.winner_label.config(text="No votes cast yet", foreground="gray")

            # Style for candidates
            for candidate in results['results']:
                candidate_frame = ttk.Frame(scrollable_frame)
                candidate_frame.pack(fill=tk.X, pady=5, padx=10)
                
                # Container for name and party
                info_frame = ttk.Frame(candidate_frame)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # Name with winner indicator
                name_text = f"{candidate['name']} 🏆" if candidate['votes'] == max_votes else candidate['name']
                name_color = "#059669" if candidate['votes'] == max_votes else "#2c3e50"
                
                ttk.Label(info_frame, 
                         text=name_text,
                         font=("Segoe UI", 12, "bold"),
                         foreground=name_color).pack(anchor=tk.W)
                
                # Party if available
                if candidate.get('party'):
                    ttk.Label(info_frame,
                            text=candidate['party'],
                            font=("Segoe UI", 10),
                            foreground="gray").pack(anchor=tk.W)
                
                # Votes and percentage
                stats_frame = ttk.Frame(candidate_frame)
                stats_frame.pack(side=tk.RIGHT, padx=10)
                
                ttk.Label(stats_frame,
                         text=f"{candidate['votes']} votes",
                         font=("Segoe UI", 11, "bold")).pack(side=tk.RIGHT, padx=5)
                
                ttk.Label(stats_frame,
                         text=f"{candidate['percentage']:.1f}%",
                         font=("Segoe UI", 11)).pack(side=tk.RIGHT, padx=5)
                
                # Progress bar
                progress = ttk.Progressbar(candidate_frame, 
                                         length=400, 
                                         maximum=100,
                                         mode='determinate',
                                         style="Candidate.Horizontal.TProgressbar")
                progress['value'] = candidate['percentage']
                progress.pack(fill=tk.X, pady=(5, 0))
                
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load election results: {str(e)}")

    def refresh_data(self):
        """Refresh all data"""
        self.load_elections()
        if self.selected_election:
            self.load_results(self.selected_election)
            self.verify_blockchain()
            
    def verify_blockchain(self):
        """Verify blockchain integrity"""
        if not self.selected_election:
            messagebox.showwarning("Warning", "Please select an election first")
            return

        try:
            success, verification = self.api_client.verify_blockchain(self.selected_election)
            if not success:
                messagebox.showerror("Error", f"Blockchain verification failed: {verification}")
                return
            
            if verification.get('status') == 'valid':
                self.blockchain_status_label.config(
                    text=f"✓ Chain verified - {verification.get('total_blocks', 'N/A')} blocks",
                    foreground="green"
                )
            else:
                self.blockchain_status_label.config(
                    text=f"⚠ {verification.get('message', 'Verification failed')}",
                    foreground="red"
                )
                
            messagebox.showinfo(
                "Blockchain Verification",
                f"Status: {verification.get('status', 'unknown').upper()}\n" +
                f"Total Blocks: {verification.get('total_blocks', 'N/A')}\n" +
                f"Message: {verification.get('message', 'No message')}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Blockchain verification failed: {str(e)}")
