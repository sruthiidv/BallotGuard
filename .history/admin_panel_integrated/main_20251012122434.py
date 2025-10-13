def create_dashboard_tab(self, notebook):
    """Enhanced dashboard with better layout for election results"""
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
    
    # Vote statistics cards (full width)
    stats_frame = Labelframe(frame, text="Vote Statistics", padding=20)
    stats_frame.pack(fill="x", pady=(0, 20))
    
    stats_grid = Frame(stats_frame)
    stats_grid.pack()
    
    # Create statistics cards
    self.create_stats_cards(stats_grid)
    
    # Main content area with better proportions
    content_frame = Frame(frame)
    content_frame.pack(fill="both", expand=True)
    
    # Left side - Election Results (70% width)
    left_panel = Frame(content_frame)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
    
    # Candidate results with scrollable area
    results_frame = Labelframe(left_panel, text="Election Results", padding=20)
    results_frame.pack(fill="both", expand=True)
    
    # Create scrollable results container
    self.create_scrollable_results_container(results_frame)
    
    # Right side - Controls and Info (30% width)
    right_panel = Frame(content_frame)
    right_panel.pack(side="right", fill="both", padx=(15, 0))
    
    # Make right panel have fixed width but expandable height
    right_panel.configure(width=400)
    
    # Results controls
    controls_frame = Labelframe(right_panel, text="Results Controls", padding=15)
    controls_frame.pack(fill="x", pady=(0, 15))
    
    Button(controls_frame, text="📊 Generate Full Report", 
           command=self.generate_full_report, bootstyle="primary").pack(fill="x", pady=3)
    
    Button(controls_frame, text="📈 Export Results", 
           command=self.export_results, bootstyle="success").pack(fill="x", pady=3)
    
    Button(controls_frame, text="🔍 Detailed Analytics", 
           command=self.show_detailed_analytics, bootstyle="info").pack(fill="x", pady=3)
    
    Button(controls_frame, text="🔄 Refresh Data", 
           command=self.refresh_dashboard, bootstyle="secondary").pack(fill="x", pady=3)
    
    # Bigger Quick info panel
    info_frame = Labelframe(right_panel, text="Quick Election Info", padding=15)
    info_frame.pack(fill="both", expand=True)
    
    # Create bigger text area with better scrolling
    text_container = Frame(info_frame)
    text_container.pack(fill="both", expand=True)
    
    self.quick_info_text = Text(text_container, height=20, width=45, 
                              font=("Arial", 11), wrap=tk.WORD,
                              bg="#2b2b2b", fg="#ffffff",
                              selectbackground="#404040")
    info_scrollbar = ttk.Scrollbar(text_container, orient="vertical", 
                                 command=self.quick_info_text.yview)
    self.quick_info_text.configure(yscrollcommand=info_scrollbar.set)
    
    self.quick_info_text.pack(side="left", fill="both", expand=True)
    info_scrollbar.pack(side="right", fill="y")
    
    # Load initial data
    self.refresh_elections()

def create_scrollable_results_container(self, parent):
    """Create a scrollable container for election results"""
    # Create canvas and scrollbar for results
    results_canvas = tk.Canvas(parent, highlightthickness=0)
    results_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=results_canvas.yview)
    
    # Create scrollable frame
    self.results_container = Frame(results_canvas)
    
    # Configure scrolling
    self.results_container.bind(
        "<Configure>",
        lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all"))
    )
    
    results_canvas.create_window((0, 0), window=self.results_container, anchor="nw")
    results_canvas.configure(yscrollcommand=results_scrollbar.set)
    
    # Pack canvas and scrollbar
    results_canvas.pack(side="left", fill="both", expand=True)
    results_scrollbar.pack(side="right", fill="y")
    
    # Store canvas reference for later use
    self.results_canvas = results_canvas
    
    # Bind mousewheel to canvas
    def _on_mousewheel(event):
        results_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    results_canvas.bind("<MouseWheel>", _on_mousewheel)

def update_results_display(self, results):
    """Update the results display with candidate information - IMPROVED"""
    # Clear existing results
    for widget in self.results_container.winfo_children():
        widget.destroy()
    
    if not results['candidates']:
        Label(self.results_container, text="No candidates found", 
              font=("Arial", 16, "bold")).pack(pady=30)
        return
    
    # Title for results
    title_frame = Frame(self.results_container)
    title_frame.pack(fill="x", pady=(0, 20), padx=20)
    
    Label(title_frame, text="🏆 CANDIDATE RESULTS", 
          font=("Arial", 18, "bold"), bootstyle="primary").pack()
    
    Label(title_frame, text=f"Total Votes Cast: {results['total_votes']}", 
          font=("Arial", 12)).pack(pady=(5, 0))
    
    # Display each candidate with better styling
    for i, candidate in enumerate(results['candidates']):
        # Main candidate container
        candidate_container = Frame(self.results_container)
        candidate_container.pack(fill="x", pady=10, padx=20)
        
        # Rank badge
        rank_color = "primary" if i == 0 else "secondary" if i == 1 else "light"
        rank_symbol = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        
        candidate_frame = Labelframe(candidate_container, 
                                   text=f"{rank_symbol} {candidate['name']}", 
                                   padding=20,
                                   bootstyle=rank_color)
        candidate_frame.pack(fill="x")
        
        # Candidate details in a grid
        details_grid = Frame(candidate_frame)
        details_grid.pack(fill="x")
        
        # Left column - Basic info
        left_details = Frame(details_grid)
        left_details.pack(side="left", fill="x", expand=True)
        
        # Party info
        party_frame = Frame(left_details)
        party_frame.pack(fill="x", pady=2)
        Label(party_frame, text="Party:", font=("Arial", 10, "bold")).pack(side="left")
        Label(party_frame, text=candidate.get('party', 'Independent'), 
              font=("Arial", 10)).pack(side="left", padx=(10, 0))
        
        # Vote count
        votes_frame = Frame(left_details)
        votes_frame.pack(fill="x", pady=2)
        Label(votes_frame, text="Votes:", font=("Arial", 10, "bold")).pack(side="left")
        Label(votes_frame, text=f"{candidate['votes']:,}", 
              font=("Arial", 12, "bold"), bootstyle="primary").pack(side="left", padx=(10, 0))
        
        # Percentage
        pct_frame = Frame(left_details)
        pct_frame.pack(fill="x", pady=2)
        Label(pct_frame, text="Percentage:", font=("Arial", 10, "bold")).pack(side="left")
        Label(pct_frame, text=f"{candidate['percentage']:.1f}%", 
              font=("Arial", 12, "bold"), bootstyle="success").pack(side="left", padx=(10, 0))
        
        # Right column - Progress visualization
        right_details = Frame(details_grid)
        right_details.pack(side="right", fill="x", expand=True, padx=(30, 0))
        
        # Progress bar with percentage
        progress_label_frame = Frame(right_details)
        progress_label_frame.pack(fill="x")
        
        Label(progress_label_frame, text="Vote Share", 
              font=("Arial", 10, "bold")).pack(anchor="w")
        
        progress = Progressbar(right_details, length=400, mode='determinate',
                             bootstyle=f"{rank_color}-striped", 
                             style=f"{rank_color}.Horizontal.TProgressbar")
        progress.pack(fill="x", pady=(5, 0))
        progress.config(value=candidate['percentage'])
        
        # Add vote difference from leader (if not the leader)
        if i > 0:
            vote_diff = results['candidates'][0]['votes'] - candidate['votes']
            diff_frame = Frame(left_details)
            diff_frame.pack(fill="x", pady=2)
            Label(diff_frame, text="Behind leader:", font=("Arial", 9)).pack(side="left")
            Label(diff_frame, text=f"-{vote_diff:,} votes", 
                  font=("Arial", 9), bootstyle="warning").pack(side="left", padx=(10, 0))
    
    # Update canvas scroll region
    self.results_container.update_idletasks()
    self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

def update_quick_info(self, results):
    """Update quick info panel with comprehensive election data"""
    self.quick_info_text.delete('1.0', tk.END)
    
    candidates = results.get('candidates', [])
    leading_candidate = candidates[0] if candidates else None
    
    # More detailed quick info
    info_text = f"""═══════════════════════════════
🗳️  ELECTION OVERVIEW
═══════════════════════════════
📊 Title: {results['title']}
🔄 Status: {results['status'].upper()}
📅 Election ID: {results.get('election_id', 'N/A')}

═══════════════════════════════
👥  PARTICIPATION METRICS  
═══════════════════════════════
✅ Total Votes Cast: {results['total_votes']:,}
👤 Eligible Voters: {results['eligible_voters']:,}
📈 Turnout Rate: {results['turnout_percentage']:.1f}%
❌ Abstentions: {results['eligible_voters'] - results['total_votes']:,}

═══════════════════════════════
🏆  LEADING CANDIDATE
═══════════════════════════════"""

    if leading_candidate:
        info_text += f"""
👑 Name: {leading_candidate['name']}
🎯 Party: {leading_candidate.get('party', 'Independent')}
🗳️  Votes: {leading_candidate['votes']:,}
📊 Percentage: {leading_candidate['percentage']:.1f}%"""
        
        if len(candidates) > 1:
            margin = leading_candidate['votes'] - candidates[1]['votes']
            info_text += f"""
🎖️  Margin: +{margin:,} votes"""
    else:
        info_text += """
❌ No candidates available"""

    info_text += f"""

═══════════════════════════════
📋  CANDIDATE SUMMARY
═══════════════════════════════
🎪 Total Candidates: {len(candidates)}"""

    # Show top 3 candidates summary
    for i, candidate in enumerate(candidates[:3]):
        position = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
        info_text += f"""
{position} {candidate['name']}: {candidate['votes']:,} ({candidate['percentage']:.1f}%)"""

    if len(candidates) > 3:
        info_text += f"""
... and {len(candidates) - 3} more candidates"""

    info_text += f"""

═══════════════════════════════
🔗  BLOCKCHAIN STATUS
═══════════════════════════════
⛓️  Chain Status: {"✅ INTACT" if results['blockchain_verification']['chain_intact'] else "❌ COMPROMISED"}
📦 Total Blocks: {results['blockchain_verification']['total_blocks']:,}
🔍 Verification: {results['blockchain_verification']['verification_status']}
🔗 Latest Hash: {results['blockchain_verification']['last_block_hash'][:20]}...

═══════════════════════════════
📊  COMPETITION ANALYSIS
═══════════════════════════════"""

    # Add competition analysis if available
    analytics = results.get('analytics', {})
    if analytics:
        vote_analysis = analytics.get('vote_distribution_analysis', {})
        info_text += f"""
🏁 Competition Level: {vote_analysis.get('competitive_balance', 'N/A')}
📈 Distribution Type: {vote_analysis.get('distribution_type', 'N/A')}
🎯 Concentration Index: {vote_analysis.get('concentration_index', 'N/A')}"""
        
        margin_info = analytics.get('margin_of_victory', {})
        if margin_info:
            info_text += f"""
🏆 Victory Margin: {margin_info.get('absolute_margin', 0)} votes
📊 Margin Percentage: {margin_info.get('percentage_margin', 0):.1f}%
✅ Decisive Win: {"Yes" if margin_info.get('decisive') else "No"}"""

    info_text += f"""

═══════════════════════════════
⏰  LAST UPDATED
═══════════════════════════════
🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}
👨‍💼 Generated by: Administrator
🔄 Auto-refresh: Every 10 seconds
"""
    
    self.quick_info_text.insert('1.0', info_text)
    
    # Make text read-only but allow selection
    self.quick_info_text.config(state='normal')

def show_detailed_analytics(self):
    """Show detailed analytics in a new window - IMPROVED"""
    try:
        success, message, results = self.election_manager.get_comprehensive_results(self.current_election_id)
        
        if success:
            analytics_window = tk.Toplevel(self.app)
            analytics_window.title(f"📊 Detailed Analytics - {results['title']}")
            analytics_window.geometry("900x700")
            analytics_window.minsize(800, 600)
            
            # Create notebook for different analytics sections
            analytics_notebook = Notebook(analytics_window)
            analytics_notebook.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Overview tab
            overview_frame = Frame(analytics_notebook)
            analytics_notebook.add(overview_frame, text="📊 Overview")
            
            overview_text = scrolledtext.ScrolledText(overview_frame, font=("Consolas", 11),
                                                    bg="#2b2b2b", fg="#ffffff")
            overview_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Detailed analytics tab
            detailed_frame = Frame(analytics_notebook)
            analytics_notebook.add(detailed_frame, text="🔍 Detailed Analysis")
            
            detailed_text = scrolledtext.ScrolledText(detailed_frame, font=("Consolas", 11),
                                                    bg="#2b2b2b", fg="#ffffff")
            detailed_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            analytics = results.get('analytics', {})
            
            overview_content = f"""
🗳️ ELECTION ANALYTICS OVERVIEW
════════════════════════════════════════════════════════

📊 BASIC INFORMATION
═══════════════════
Election: {results['title']}
Status: {results['status'].upper()}
Total Votes: {results['total_votes']:,}
Eligible Voters: {results['eligible_voters']:,}
Turnout: {results['turnout_percentage']:.2f}%

🏆 WINNER ANALYSIS
═════════════════
Winner: {analytics.get('winner', {}).get('name', 'N/A')}
Winning Votes: {analytics.get('winner', {}).get('votes', 0):,}
Winning Percentage: {analytics.get('winner', {}).get('percentage', 0):.1f}%

🎯 VICTORY MARGIN
════════════════
Absolute Margin: {analytics.get('margin_of_victory', {}).get('absolute_margin', 0):,} votes
Percentage Margin: {analytics.get('margin_of_victory', {}).get('percentage_margin', 0):.2f}%
Decisive Victory: {"✅ Yes" if analytics.get('margin_of_victory', {}).get('decisive') else "❌ No"}

📈 PARTICIPATION
═══════════════
Total Eligible: {analytics.get('voter_participation', {}).get('total_eligible', 0):,}
Total Voted: {analytics.get('voter_participation', {}).get('total_voted', 0):,}
Turnout Rate: {analytics.get('voter_participation', {}).get('turnout_rate', 0):.2f}%
Abstentions: {analytics.get('voter_participation', {}).get('abstentions', 0):,}

🏁 COMPETITION
═════════════
Competition Level: {analytics.get('vote_distribution_analysis', {}).get('competitive_balance', 'N/A')}
Distribution Type: {analytics.get('vote_distribution_analysis', {}).get('distribution_type', 'N/A')}
"""
            
            detailed_content = f"""
🔍 DETAILED STATISTICAL ANALYSIS
════════════════════════════════════════════════════════

📊 VOTE DISTRIBUTION METRICS
═══════════════════════════
Distribution Type: {analytics.get('vote_distribution_analysis', {}).get('distribution_type', 'N/A')}
Concentration Index: {analytics.get('vote_distribution_analysis', {}).get('concentration_index', 'N/A')}
Competitive Balance: {analytics.get('vote_distribution_analysis', {}).get('competitive_balance', 'N/A')}

📈 STATISTICAL SUMMARY
═════════════════════
Mean Votes per Candidate: {analytics.get('vote_distribution_analysis', {}).get('statistical_summary', {}).get('mean_votes', 0):.1f}
Vote Range: {analytics.get('vote_distribution_analysis', {}).get('statistical_summary', {}).get('vote_range', 0):,}
Standard Deviation: {analytics.get('vote_distribution_analysis', {}).get('statistical_summary', {}).get('standard_deviation', 0):.2f}

🏆 CANDIDATE PERFORMANCE BREAKDOWN
═════════════════════════════════"""
            
            for i, candidate in enumerate(results['candidates']):
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                detailed_content += f"""
{rank_emoji} {candidate['name']}
   Party: {candidate.get('party', 'Independent')}
   Votes: {candidate['votes']:,}
   Percentage: {candidate['percentage']:.2f}%
   Vote Share Rank: #{i+1}"""
                
                if i > 0:
                    vote_diff = results['candidates'][0]['votes'] - candidate['votes']
                    detailed_content += f"""
   Behind Leader: -{vote_diff:,} votes ({((vote_diff/results['candidates'][0]['votes'])*100):.1f}%)"""
                
                detailed_content += "\n"
            
            detailed_content += f"""
⛓️ BLOCKCHAIN INTEGRITY REPORT
═════════════════════════════
Chain Status: {results['blockchain_verification']['verification_status']}
Chain Intact: {"✅ Yes" if results['blockchain_verification']['chain_intact'] else "❌ No"}
Total Blocks: {results['blockchain_verification']['total_blocks']:,}
Latest Block Hash: {results['blockchain_verification']['last_block_hash']}

📊 DATA SOURCE VERIFICATION
══════════════════════════
Report Generated: {results['report_metadata']['generated_at']}
Data Sources: {results['report_metadata']['data_source']}
Report Version: {results['report_metadata']['report_version']}
Generated By: {results['report_metadata']['generated_by']}
"""
            
            overview_text.insert('1.0', overview_content)
            overview_text.config(state='disabled')
            
            detailed_text.insert('1.0', detailed_content)
            detailed_text.config(state='disabled')
            
        else:
            messagebox.showerror("Analytics Error", message)
            
    except Exception as e:
        messagebox.showerror("Error", f"Error showing analytics:\n{str(e)}")
