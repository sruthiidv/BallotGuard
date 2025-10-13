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
        
        self.chain_status_label = Label(title_frame, text="🟢 BLOCKCHAIN SECURE", 
                                      font=("Arial", 12, "bold"), bootstyle="success")
        self.chain_status_label.pack(side="right")
        
        # Create tabs
        notebook = Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Dashboard tab
        self.create_dashboard(notebook)
        
        # Blockchain Explorer tab
        self.create_blockchain_explorer(notebook)
        
        # Security Monitor tab
        self.create_security_monitor(notebook)
    
    def create_dashboard(self, notebook):
        """Admin dashboard - monitoring only"""
        frame = Frame(notebook)
        notebook.add(frame, text="📊 Dashboard")
        
        # Election status
        status_frame = Labelframe(frame, text="Election Status", padding=20)
        status_frame.pack(fill="x", pady=20)
        
        self.election_status = Label(status_frame, text="🟢 Election Active | Blockchain Secure", 
                                   font=("Arial", 14), bootstyle="success")
        self.election_status.pack()
        
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
                                        font=("Arial", 12), justify="left")
        self.blockchain_info_text.pack(anchor="w")
        
        # Chain integrity status
        integrity_frame = Labelframe(info_frame, text="Chain Integrity", padding=10)
        integrity_frame.pack(fill="x", pady=(10, 0))
        
        self.integrity_status = Label(integrity_frame, text="✅ Chain Integrity Verified", 
                                    font=("Arial", 12), bootstyle="success")
        self.integrity_status.pack()
        
        # Recent blocks table
        blocks_frame = Labelframe(frame, text="Recent Blocks", padding=20)
        blocks_frame.pack(fill="both", expand=True, pady=20)
        
        columns = ('Index', 'Time', 'Hash', 'Previous Hash', 'Status')
        self.blocks_tree = ttkb.Treeview(blocks_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.blocks_tree.heading(col, text=col)
            self.blocks_tree.column(col, width=120)
        
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
        
        self
