import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import tkinter.scrolledtext as scrolledtext
from tkinter.ttk import Frame as TTKFrame, Label, Button, LabelFrame as Labelframe, Entry, Notebook, Combobox
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import time
import os

try:
    from utils.api_client import APIClient
    print("✅ API client imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

class AdminPanel:
    def __init__(self):
        try:
            print("🚀 Initializing BallotGuard Admin Panel...")
            self.api = APIClient()
            self.current_election_id = None
            self.party_symbols = {}  # Will be loaded from server
            
            # Load party symbols from server
            try:
                success, symbols = self.api.get_party_symbols()
                if success:
                    self.party_symbols = symbols
                    print(f"✅ Loaded party symbols: {list(symbols.keys())}")
                else:
                    print("⚠️ Could not load party symbols from server, using defaults")
                    self.party_symbols = {
                        "BJP": "🌸", "INC": "✋", "AAP": "🧹", 
                        "CPI": "🌾", "TMC": "🌿", "Independent": "⭐", "": "🗳️"
                    }
            except Exception as e:
                print(f"⚠️ Error loading symbols: {e}, using defaults")
                self.party_symbols = {
                    "BJP": "🌸", "INC": "✋", "AAP": "🧹", 
                    "CPI": "🌾", "TMC": "🌿", "Independent": "⭐", "": "🗳️"
                }
            
            self.app = tk.Tk()
            self.app.title("BallotGuard Admin Panel")
            self.app.geometry("1400x900")
            self.app.minsize(1200, 750)
            
            # Center window on screen
            self.center_window()
            
            # COLORS - Light Theme
            self.BG_PRIMARY = "#ffffff"
            self.BG_SECONDARY = "#f8f9fa"
            self.BG_TERTIARY = "#e9ecef"
            self.ACCENT_BLUE = "#3b82f6"
            self.ACCENT_BLUE_LIGHT = "#2563eb"
            self.ACCENT_BLUE_DARK = "#1e40af"
            self.SUCCESS_COLOR = "#10b981"
            self.DANGER_COLOR = "#ef4444"
            self.TEXT_PRIMARY = "#1f2937"
            self.TEXT_SECONDARY = "#6b7280"
            
            self.app.configure(bg=self.BG_PRIMARY)
            
            self.style = ttk.Style()
            self.style.theme_use('clam')
            
            self.style.configure('TFrame', background=self.BG_PRIMARY)
            self.style.configure('TLabel', background=self.BG_PRIMARY, foreground=self.TEXT_PRIMARY, 
                               font=('Segoe UI', 10))
            self.style.configure('Header.TLabel', 
                               font=('Segoe UI Semibold', 24, 'bold'), 
                               foreground=self.ACCENT_BLUE_LIGHT, 
                               background=self.BG_SECONDARY)
            
            self.style.configure('TLabelframe', 
                               background=self.BG_SECONDARY, 
                               foreground=self.TEXT_PRIMARY,
                               borderwidth=1,
                               relief='solid',
                               bordercolor=self.BG_TERTIARY)
            self.style.configure('TLabelframe.Label', 
                               background=self.BG_SECONDARY, 
                               foreground=self.ACCENT_BLUE_LIGHT, 
                               font=('Segoe UI Semibold', 12, 'bold'))
            
            self.style.configure('TNotebook', background=self.BG_PRIMARY, borderwidth=0)
            self.style.configure('TNotebook.Tab', 
                               background=self.BG_SECONDARY, 
                               foreground=self.TEXT_SECONDARY,
                               padding=[25, 14],
                               borderwidth=0,
                               font=("Segoe UI Semibold", 11, 'bold'))
            self.style.map('TNotebook.Tab', 
                          background=[('selected', self.ACCENT_BLUE), ('active', self.BG_TERTIARY)],
                          foreground=[('selected', '#ffffff')])
            
            self.style.configure('TEntry', 
                               fieldbackground=self.BG_TERTIARY, 
                               foreground=self.TEXT_PRIMARY,
                               borderwidth=1,
                               relief='solid',
                               bordercolor='#d1d5db')
            
            self.style.configure('Success.TButton', 
                               font=('Segoe UI Semibold', 12, 'bold'), 
                               padding=15,
                               borderwidth=0,
                               relief='flat',
                               borderradius=8)
            self.style.map('Success.TButton',
                          background=[('pressed', '#059669'), ('active', '#34d399')])
            
            self.style.configure('Primary.TButton', 
                               font=('Segoe UI Semibold', 11, 'bold'), 
                               padding=12,
                               borderwidth=0,
                               relief='flat',
                               borderradius=6)
            self.style.map('Primary.TButton',
                          background=[('pressed', self.ACCENT_BLUE_DARK), ('active', self.ACCENT_BLUE_LIGHT)])
            
            self.style.configure('Secondary.TButton', 
                               font=('Segoe UI Semibold', 11, 'bold'), 
                               padding=12,
                               borderwidth=0,
                               relief='flat',
                               borderradius=6)
            self.style.map('Secondary.TButton',
                          background=[('pressed', self.BG_PRIMARY), ('active', '#334155')])
            
            self.style.configure('Danger.TButton', 
                               font=('Segoe UI Semibold', 10, 'bold'), 
                               padding=10,
                               borderwidth=0,
                               relief='flat',
                               borderradius=6)
            self.style.map('Danger.TButton',
                          background=[('pressed', '#dc2626'), ('active', '#f87171')])
            
            # Variables
            self.election_title_var = tk.StringVar()
            self.election_desc_var = tk.StringVar()
            self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            self.start_time_var = tk.StringVar(value="09:00")
            self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            self.end_time_var = tk.StringVar(value="17:00")
            self.eligible_voters_var = tk.StringVar(value="5000")
            self.candidate_entries = []
            
            print("🔄 Setting up UI...")
            self.setup_ui()
            print("✅ Admin Panel initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def center_window(self):
        """Center the window on the screen"""
        self.app.update_idletasks()
        width = self.app.winfo_width()
        height = self.app.winfo_height()
        x = (self.app.winfo_screenwidth() // 2) - (width // 2)
        y = (self.app.winfo_screenheight() // 2) - (height // 2)
        self.app.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup main UI"""
        try:
            # TITLE - using tk.Frame for background color
            title_frame = tk.Frame(self.app, bg=self.BG_SECONDARY)
            title_frame.pack(fill="x", padx=0, pady=0)
            
            inner_title = tk.Frame(title_frame, bg=self.BG_SECONDARY)
            inner_title.pack(fill="x", padx=30, pady=20)
            
            # Left side - Logo and Title
            left_side = tk.Frame(inner_title, bg=self.BG_SECONDARY)
            left_side.pack(side="left")
            
            # Load logo from voter UI assets
            logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'client_app', 'assets', 'Untitled design.png')
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    logo_img = logo_img.resize((50, 50), Image.Resampling.LANCZOS)
                    self.logo_photo = ImageTk.PhotoImage(logo_img)
                    # Add a background frame for the logo
                    logo_frame = tk.Frame(left_side, bg=self.ACCENT_BLUE, padx=8, pady=8)
                    logo_frame.pack(side="left", padx=(0, 15))
                    logo_label = tk.Label(logo_frame, image=self.logo_photo, bg=self.ACCENT_BLUE, borderwidth=0)
                    logo_label.pack()
                except Exception as e:
                    print(f"⚠️ Could not load logo: {e}")
                    # Fallback to emoji
                    logo_label = tk.Label(left_side, text="🗳️", font=("Segoe UI", 32), 
                                        bg=self.BG_SECONDARY, fg=self.ACCENT_BLUE)
                    logo_label.pack(side="left", padx=(0, 15))
            else:
                # Fallback to emoji
                logo_label = tk.Label(left_side, text="🗳️", font=("Segoe UI", 32), 
                                    bg=self.BG_SECONDARY, fg=self.ACCENT_BLUE)
                logo_label.pack(side="left", padx=(0, 15))
            
            Label(left_side, text="BallotGuard Election Manager", 
                  style='Header.TLabel').pack(side="left")
            
            status_frame = tk.Frame(inner_title, bg=self.BG_SECONDARY)
            status_frame.pack(side="right")
            self.db_status_label = Label(status_frame, text="● CHECKING...", 
                                       font=('Segoe UI', 11, 'bold'), 
                                       foreground="orange", 
                                       background=self.BG_SECONDARY)
            self.db_status_label.pack(side="right", padx=(0, 10))
            
            # Check server connection
            self.check_server_connection()
            
            # Divider
            tk.Frame(self.app, bg=self.ACCENT_BLUE, height=4).pack(fill="x", padx=0, pady=0)
            
            # TABS
            notebook = Notebook(self.app)
            notebook.pack(fill="both", expand=True, padx=20, pady=20)
            self.notebook = notebook
            
            # Create tabs
            self.create_dashboard_tab(notebook)
            self.create_election_creation_tab(notebook)
            self.create_security_monitor_tab(notebook)
            
            print("✅ UI setup completed successfully")
            
        except Exception as e:
            print(f"❌ Error in setup_ui: {e}")
            import traceback
            traceback.print_exc()
    
    def check_server_connection(self):
        """Check if the server is reachable and update the status label"""
        try:
            # Try to get system health or elections list as a connection test
            success, response = self.api.get_system_health()
            if success:
                self.db_status_label.config(
                    text="● SERVER CONNECTED",
                    foreground=self.SUCCESS_COLOR
                )
            else:
                self.db_status_label.config(
                    text="● SERVER UNREACHABLE",
                    foreground=self.DANGER_COLOR
                )
        except Exception as e:
            # If health endpoint doesn't exist, try elections as fallback
            try:
                success, response = self.api.get_elections()
                if success:
                    self.db_status_label.config(
                        text="● SERVER CONNECTED",
                        foreground=self.SUCCESS_COLOR
                    )
                else:
                    self.db_status_label.config(
                        text="● SERVER UNREACHABLE",
                        foreground=self.DANGER_COLOR
                    )
            except Exception:
                self.db_status_label.config(
                    text="● SERVER OFFLINE",
                    foreground=self.DANGER_COLOR
                )
    
    def create_dashboard_tab(self, notebook):
        """Dashboard tab"""
        try:
            frame = TTKFrame(notebook)
            frame.configure(style='TFrame')
            notebook.add(frame, text="📊 Dashboard")

            # Selector frame with better padding
            selector_frame = Labelframe(frame, text="📋 Current Election", padding=15)
            selector_frame.pack(fill="x", pady=(15, 12), padx=20)

            # Configure grid for responsive layout
            selector_frame.grid_columnconfigure(1, weight=1)
            
            Label(selector_frame, text="Select Election:", font=("Segoe UI Semibold", 11), 
                  foreground=self.TEXT_SECONDARY, background=self.BG_SECONDARY).grid(row=0, column=0, sticky="w", padx=(0, 12))
            
            self.election_var = tk.StringVar()
            self.election_combo = Combobox(selector_frame, textvariable=self.election_var, 
                                          state="readonly", font=("Segoe UI", 11))
            self.election_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12))
            self.election_combo.bind("<<ComboboxSelected>>", self.on_election_changed)

            Button(selector_frame, text="🔄 Refresh", command=self.refresh_elections, 
                   style='Primary.TButton').grid(row=0, column=2, sticky="e")

            # Status label with better spacing
            self.election_status_label = Label(frame, 
                                             text="👈 Select an election to view status", 
                                             font=("Segoe UI Semibold", 12, 'bold'), 
                                             foreground=self.ACCENT_BLUE_LIGHT)
            self.election_status_label.pack(fill="x", padx=20, pady=(12, 8))

            # Winner label (empty until results available)
            self.winner_label = Label(frame, 
                                      text="", 
                                      font=("Segoe UI Semibold", 15, 'bold'), 
                                      foreground=self.SUCCESS_COLOR)
            self.winner_label.pack(fill="x", padx=20, pady=(5, 12))

            # Action buttons frame with better layout
            action_buttons_frame = tk.Frame(frame, bg=self.BG_PRIMARY)
            action_buttons_frame.pack(fill="x", padx=20, pady=(0, 12))
            
            # Configure grid for equal-width buttons
            action_buttons_frame.grid_columnconfigure(0, weight=1)
            action_buttons_frame.grid_columnconfigure(1, weight=1)
            
            # Open election button - change from DRAFT to OPEN
            open_btn = Button(action_buttons_frame, text="🟢 Open Election", 
                   command=self.open_current_election, 
                   style='Secondary.TButton')
            open_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
            
            # End election button - manually close and show results
            end_btn = Button(action_buttons_frame, text="⏹️ End Election", 
                   command=self.end_current_election, 
                   style='Secondary.TButton')
            end_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

            # Results frame with better padding
            results_frame = Labelframe(frame, text="📊 Live Results", padding=15)
            results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

            self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                         height=18, 
                                                         font=("Consolas", 10),
                                                         bg="#ffffff", 
                                                         fg=self.TEXT_PRIMARY,
                                                         insertbackground=self.ACCENT_BLUE,
                                                         borderwidth=0,
                                                         relief="flat")
            self.results_text.pack(fill="both", expand=True, padx=3, pady=3)
            
            print("✅ Dashboard tab created")
        except Exception as e:
            print(f"❌ Error in dashboard: {e}")
    
    def create_election_creation_tab(self, notebook):
        """Create Election Tab - ALL CONTENT VISIBLE"""
        try:
            # Main container using tk.Frame (NOT ttk.Frame!)
            main_frame = tk.Frame(notebook, bg=self.BG_PRIMARY)
            main_frame.pack(fill="both", expand=True)
            notebook.add(main_frame, text="➕ Create Election")
            
            # Content area - tk.Frame with bg - CENTER IT
            content_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
            content_frame.pack(fill="both", expand=True, side="top", padx=50, pady=20)
            
            # Scrollable content
            canvas = tk.Canvas(content_frame, bg=self.BG_PRIMARY, highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.BG_PRIMARY)
            
            scrollable_frame.bind("<Configure>", 
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Bind canvas resize to update window width
            def on_canvas_configure(event):
                canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
            canvas.bind('<Configure>', on_canvas_configure)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Mouse wheel
            def on_wheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", on_wheel)
            
            # FORM CONTENT - with better horizontal spacing
            form_frame = Labelframe(scrollable_frame, text="📋 Create New Election", padding=30)
            form_frame.pack(fill="both", expand=True, padx=40, pady=25)
            
            # Election Title
            Label(form_frame, text="📝 Election Title:", 
                  font=("Segoe UI Semibold", 11, 'bold'), 
                  foreground=self.ACCENT_BLUE_LIGHT).pack(anchor="w", pady=(5, 6))
            Entry(form_frame, textvariable=self.election_title_var, 
                  font=("Segoe UI", 11)).pack(fill="x", ipady=7, pady=(0, 15))
            
            # Description
            Label(form_frame, text="📝 Description:", 
                  font=("Segoe UI Semibold", 11, 'bold'), 
                  foreground=self.ACCENT_BLUE_LIGHT).pack(anchor="w", pady=(0, 6))
            Entry(form_frame, textvariable=self.election_desc_var, 
                  font=("Segoe UI", 11)).pack(fill="x", ipady=7, pady=(0, 15))
            
            # Timeline Section
            timeline_frame = Labelframe(form_frame, text="📅 Election Timeline", padding=15)
            timeline_frame.pack(fill="x", pady=(10, 15))
            
            Label(timeline_frame, text="🟢 START", 
                  font=("Segoe UI Semibold", 11, 'bold'), 
                  foreground=self.SUCCESS_COLOR).pack(anchor="w", pady=(0, 8))
            
            start_row = tk.Frame(timeline_frame, bg=self.BG_SECONDARY)
            start_row.pack(fill="x", pady=(0, 10))
            Label(start_row, text="Date:", font=("Segoe UI Semibold", 10),
                  background=self.BG_SECONDARY).pack(side="left", padx=(0, 6))
            Entry(start_row, textvariable=self.start_date_var, 
                  font=("Segoe UI", 11), width=16).pack(side="left", padx=4, ipady=5)
            Label(start_row, text="Time:", font=("Segoe UI Semibold", 10),
                  background=self.BG_SECONDARY).pack(side="left", padx=(12, 6))
            Entry(start_row, textvariable=self.start_time_var, 
                  font=("Segoe UI", 11), width=10).pack(side="left", padx=4, ipady=5)
            
        # NOTE: End time removed from the form. Elections are ended manually
        # by the administrator using the Dashboard -> End Election button.
            
            # Voters
            Label(form_frame, text="👥 Eligible Voters:", 
                  font=("Segoe UI Semibold", 11, 'bold'), 
                  foreground=self.ACCENT_BLUE_LIGHT).pack(anchor="w", pady=(10, 6))
            Entry(form_frame, textvariable=self.eligible_voters_var, 
                  font=("Segoe UI", 11)).pack(fill="x", ipady=7, pady=(0, 15))
            
            # Candidates
            cand_section = Labelframe(form_frame, text="🏛️ Candidates", padding=15)
            cand_section.pack(fill="both", expand=True, pady=(10, 15))
            
            header = tk.Frame(cand_section, bg=self.BG_SECONDARY)
            header.pack(fill="x", pady=(0, 10))
            Label(header, text="Minimum 2 candidates required", 
                  font=("Segoe UI Semibold", 10), 
                  foreground=self.TEXT_SECONDARY,
                  background=self.BG_SECONDARY).pack(side="left")
            self.candidates_count_label = Label(header, text="Count: 0", 
                                              font=("Segoe UI Semibold", 10, 'bold'), 
                                              foreground=self.SUCCESS_COLOR,
                                              background=self.BG_SECONDARY)
            self.candidates_count_label.pack(side="right")
            
            # Candidates container
            cand_canvas = tk.Canvas(cand_section, bg=self.BG_SECONDARY, 
                                   highlightthickness=0, height=180)
            cand_scrollbar = ttk.Scrollbar(cand_section, orient="vertical", command=cand_canvas.yview)
            self.candidates_container = tk.Frame(cand_canvas, bg=self.BG_SECONDARY)
            
            self.candidates_container.bind("<Configure>",
                lambda e: cand_canvas.configure(scrollregion=cand_canvas.bbox("all")))
            
            cand_canvas.create_window((0, 0), window=self.candidates_container, anchor="nw")
            cand_canvas.configure(yscrollcommand=cand_scrollbar.set, bg=self.BG_SECONDARY)
            cand_canvas.pack(side="left", fill="both", expand=True)
            cand_scrollbar.pack(side="right", fill="y")
            
            self.add_candidate_field()
            self.add_candidate_field()
            
            add_cand_btn = tk.Frame(cand_section, bg=self.BG_SECONDARY)
            add_cand_btn.pack(fill="x", pady=(10, 5))
            Button(add_cand_btn, text="+ Add Candidate", 
                   command=self.add_candidate_field, 
                   style="Secondary.TButton").pack(padx=10)
            
            # BOTTOM BUTTON AREA - ALWAYS VISIBLE using tk.Frame
            button_area = tk.Frame(main_frame, bg=self.BG_SECONDARY)
            button_area.pack(fill="x", side="bottom", padx=90, pady=20)
            
            submit_btn = Button(button_area, text="✓ Submit & Save to Database", 
                               command=self.submit_election_to_db, 
                               style="Success.TButton")
            submit_btn.pack(fill="x", pady=(0, 10), ipady=12)
            
            clear_btn = Button(button_area, text="🗑️ Clear Form", 
                              command=self.clear_election_form, 
                              style="Secondary.TButton")
            clear_btn.pack(fill="x", ipady=10)
            
            print("✅ Election creation tab created successfully")
            
        except Exception as e:
            print(f"❌ Error in election creation tab: {e}")
            import traceback
            traceback.print_exc()
    
    def add_candidate_field(self):
        """Add candidate"""
        try:
            cand_frame = tk.Frame(self.candidates_container, bg=self.BG_PRIMARY)
            cand_frame.pack(fill="x", pady=6, padx=8)
            
            inner = tk.Frame(cand_frame, bg=self.BG_TERTIARY, highlightbackground=self.BG_TERTIARY, 
                           highlightthickness=1)
            inner.pack(fill="x", padx=12, pady=8)
            
            num = len(self.candidate_entries) + 1
            Label(inner, text=f"#{num}", 
                 font=("Segoe UI Semibold", 11, 'bold'), 
                 foreground=self.ACCENT_BLUE, 
                 background=self.BG_TERTIARY).pack(side="left", padx=12, pady=8)
            
            # Candidate Name
            Label(inner, text="Name:", 
                 font=("Segoe UI Semibold", 10), 
                 foreground=self.TEXT_SECONDARY, 
                 background=self.BG_TERTIARY).pack(side="left", padx=(8, 8))
            
            name_var = tk.StringVar()
            Entry(inner, textvariable=name_var, font=("Segoe UI", 11), width=28).pack(side="left", padx=6, ipady=6)
            
            # Party Dropdown
            Label(inner, text="Party:", 
                 font=("Segoe UI Semibold", 10), 
                 foreground=self.TEXT_SECONDARY, 
                 background=self.BG_TERTIARY).pack(side="left", padx=(15, 8))
            
            party_var = tk.StringVar()
            # Create list of party options with symbols
            party_options = [f"{symbol} {party}" if party else "🗳️ Independent" 
                           for party, symbol in self.party_symbols.items() if party]
            party_options.append("🗳️ Independent")  # Always add Independent option
            
            party_combo = Combobox(inner, textvariable=party_var, 
                                  values=party_options,
                                  state="readonly",
                                  font=("Segoe UI", 11), 
                                  width=22)
            party_combo.pack(side="left", padx=6, ipady=6)
            # Set default to Independent
            party_combo.current(len(party_options) - 1)
            
            Button(inner, text="✕", 
                   command=lambda: self.remove_candidate_field(num),
                   style="Danger.TButton", width=3).pack(side="right", padx=12, pady=8)
            
            self.candidate_entries.append({
                'frame': cand_frame,
                'name_var': name_var,
                'party_var': party_var,
                'party_combo': party_combo,
                'number': num
            })
            
            self.update_candidate_count()
            
        except Exception as e:
            print(f"❌ Error adding candidate: {e}")
    
    def remove_candidate_field(self, num):
        """Remove candidate"""
        try:
            if len(self.candidate_entries) <= 2:
                messagebox.showwarning("Warning", "Minimum 2 candidates required!")
                return
            
            for candidate in self.candidate_entries:
                if candidate['number'] == num:
                    candidate['frame'].destroy()
                    self.candidate_entries.remove(candidate)
                    break
            
            self.update_candidate_count()
        except Exception as e:
            print(f"❌ Error removing: {e}")
    
    def update_candidate_count(self):
        """Update count"""
        try:
            count = len(self.candidate_entries)
            color = self.DANGER_COLOR if count < 2 else self.SUCCESS_COLOR
            self.candidates_count_label.config(text=f"Count: {count}", foreground=color)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def submit_election_to_db(self):
        """Submit election"""
        try:
            title = self.election_title_var.get().strip()
            if not title:
                messagebox.showerror("Error", "Election title required!")
                return
            
            candidates = []
            for entry in self.candidate_entries:
                name = entry['name_var'].get().strip()
                if name:
                    # Extract party name from dropdown value (format: "🌸 BJP" or "🗳️ Independent")
                    party_selection = entry['party_var'].get().strip()
                    if party_selection:
                        # Split by space and take the last part (party name)
                        parts = party_selection.split(' ', 1)
                        party = parts[1] if len(parts) > 1 else 'Independent'
                    else:
                        party = 'Independent'
                    
                    candidates.append({
                        'name': name,
                        'party': party
                    })
            
            if len(candidates) < 2:
                messagebox.showerror("Error", "Minimum 2 candidates required!")
                return
            
            try:
                start_dt = datetime.strptime(f"{self.start_date_var.get()} {self.start_time_var.get()}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{self.end_date_var.get()} {self.end_time_var.get()}", "%Y-%m-%d %H:%M")
                
                if end_dt <= start_dt:
                    messagebox.showerror("Error", "End must be after start!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Date format: YYYY-MM-DD HH:MM")
                return
            
            try:
                voters = int(self.eligible_voters_var.get())
                if voters <= 0:
                    messagebox.showerror("Error", "Voters must be > 0!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Voters must be a number!")
                return
            
            election_data = {
                'name': title,
                'description': self.election_desc_var.get().strip() or 'No description',
                'start_date': f"{self.start_date_var.get()}T{self.start_time_var.get()}:00",
                # End date removed; admin will manually end the election
                'eligible_voters': voters,
                'candidates': candidates
            }
            
            result = messagebox.askokcancel("Confirm",
                f"Create '{title}' with {len(candidates)} candidates?")
            
            if not result:
                return
            
            success, response = self.api.create_election(election_data)
            
            if success:
                election_id = response.get('election_id', 'Unknown')
                messagebox.showinfo("✅ Success!",
                    f"Election created!\n\nID: {election_id}\nTitle: {title}")
                
                self.clear_election_form()
                self.refresh_elections()
            else:
                messagebox.showerror("Error", f"Failed: {response}")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def clear_election_form(self):
        """Clear form"""
        try:
            self.election_title_var.set("")
            self.election_desc_var.set("")
            self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.start_time_var.set("09:00")
            self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
            self.end_time_var.set("17:00")
            self.eligible_voters_var.set("5000")
            
            for entry in self.candidate_entries:
                entry['name_var'].set("")
                entry['party_var'].set("")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def create_security_monitor_tab(self, notebook):
        """Security tab"""
        try:
            frame = TTKFrame(notebook)
            frame.configure(style='TFrame')
            notebook.add(frame, text="🔒 Security")
            
            status_frame = Labelframe(frame, text="System Status", padding=20)
            status_frame.pack(fill="x", pady=(0, 20), padx=15)
            
            self.security_status = Label(status_frame, text="✓ System Secure", 
                                       font=("Segoe UI", 14, "bold"), 
                                       foreground=self.SUCCESS_COLOR)
            self.security_status.pack()
            # Voter approvals area
            voters_frame = Labelframe(frame, text="Voter Approvals (Per-Election)", padding=12)
            voters_frame.pack(fill="x", padx=15, pady=(0, 12))

            inner_voters = tk.Frame(voters_frame, bg=self.BG_SECONDARY)
            inner_voters.pack(fill="both", expand=True)

            # Election selector for approval
            election_select_frame = tk.Frame(inner_voters, bg=self.BG_SECONDARY)
            election_select_frame.pack(fill="x", pady=(0, 8))
            
            Label(election_select_frame, text="Select Election for Approval:", 
                  font=("Segoe UI", 10, 'bold'), 
                  foreground=self.TEXT_SECONDARY, 
                  background=self.BG_SECONDARY).pack(side="left", padx=(0, 10))
            
            self.approval_election_var = tk.StringVar()
            self.approval_election_combo = Combobox(election_select_frame, 
                                                   textvariable=self.approval_election_var, 
                                                   state="readonly", 
                                                   font=("Segoe UI", 9),
                                                   width=40)
            self.approval_election_combo.pack(side="left", padx=(0, 10))

            # List of pending voters
            self.pending_voters_listbox = tk.Listbox(inner_voters, height=6, font=("Segoe UI", 10))
            self.pending_voters_listbox.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6)

            voters_buttons = tk.Frame(inner_voters, bg=self.BG_SECONDARY)
            voters_buttons.pack(side="right", fill="y", padx=(8, 0), pady=6)

            Button(voters_buttons, text="🔄 Refresh", command=self.refresh_pending_voters, style='Primary.TButton').pack(fill="x", pady=4)
            Button(voters_buttons, text="✅ Approve for Election", command=self.approve_selected_voter, style='Success.TButton').pack(fill="x", pady=4)

            # System log
            log_frame = Labelframe(frame, text="System Log", padding=15)
            log_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

            self.security_log = scrolledtext.ScrolledText(log_frame, height=15, 
                                                        bg=self.BG_PRIMARY, 
                                                        fg=self.SUCCESS_COLOR,
                                                        font=("Consolas", 9))
            self.security_log.pack(fill="both", expand=True)

            # Initial state
            self.log_security("🔐 Admin panel initialized")
            self.log_security("✅ System ready")
            # Populate pending voters on tab creation
            try:
                self.refresh_pending_voters()
            except Exception:
                pass

            print("✅ Security tab created")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def refresh_elections(self):
        """Refresh"""
        try:
            success, response = self.api.get_elections()
            if success:
                names = [f"{e.get('election_id')}: {e.get('name')}" for e in response]
                self.election_combo['values'] = names
                if names:
                    self.election_combo.current(0)
                    self.on_election_changed()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def on_election_changed(self, event=None):
        """Election changed"""
        try:
            selection = self.election_var.get()
            if selection:
                election_id = selection.split(':')[0].strip()
                self.current_election_id = election_id
                self.refresh_dashboard()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def refresh_dashboard(self):
        """Refresh"""
        try:
            if not self.current_election_id:
                return
            
            success, election = self.api.get_election(self.current_election_id)
            if not success:
                return

            status = election.get('status', 'unknown').upper()
            self.election_status_label.config(text=f"✓ {election.get('name')}  •  {status}")
            
            ok, results = self.api.api_request("GET", f"/elections/{self.current_election_id}/results")
            
            self.results_text.config(state='normal')
            self.results_text.delete('1.0', tk.END)
            
            if ok:
                self.results_text.insert(tk.END, f"Total Votes: {results.get('total_votes', 0)}\n")
                self.results_text.insert(tk.END, "=" * 50 + "\n\n")
                
                for r in results.get('results', []):
                    name = r.get('name', 'Unknown')
                    party = r.get('party', '')
                    votes = r.get('votes', 0)
                    
                    # Get symbol for party
                    symbol = self.party_symbols.get(party, self.party_symbols.get('', '🗳️'))
                    
                    # Display with symbol
                    self.results_text.insert(tk.END, f"{symbol} {name} ({party}): {votes} votes\n")
            else:
                # No results yet or endpoint unreachable
                self.results_text.insert(tk.END, "Results not available yet.\n")

            # Update winner label if available
            try:
                winner = results.get('winner') if isinstance(results, dict) else None
                if winner:
                    if isinstance(winner, dict) and winner.get('tie'):
                        # For tie, show all winners with their symbols
                        winner_strs = []
                        for w in winner.get('winners', []):
                            name = w.get('name', w.get('candidate_id'))
                            party = w.get('party', '')
                            symbol = self.party_symbols.get(party, self.party_symbols.get('', '🗳️'))
                            winner_strs.append(f"{symbol} {name}")
                        names = ', '.join(winner_strs)
                        self.winner_label.config(text=f"TIE: {names}", foreground=self.DANGER_COLOR)
                    else:
                        name = winner.get('name', winner.get('candidate_id'))
                        party = winner.get('party', '')
                        votes = winner.get('votes', 0)
                        symbol = self.party_symbols.get(party, self.party_symbols.get('', '🗳️'))
                        self.winner_label.config(text=f"Winner: {symbol} {name} ({party}) — {votes} votes", 
                                               foreground=self.SUCCESS_COLOR)
                else:
                    self.winner_label.config(text="")
            except Exception:
                # Clear if any issue
                try:
                    self.winner_label.config(text="")
                except Exception:
                    pass
            
            self.results_text.config(state='disabled')
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def log_security(self, message):
        """Log"""
        timestamp = time.strftime("%H:%M:%S")
        self.security_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.security_log.see(tk.END)

    def refresh_pending_voters(self):
        """Fetch voters with pending status and populate the listbox"""
        try:
            # Refresh elections list for approval dropdown
            success, elections = self.api.get_elections()
            if success:
                election_names = [f"{e.get('election_id')}: {e.get('name')}" for e in elections]
                self.approval_election_combo['values'] = election_names
                if election_names and not self.approval_election_var.get():
                    self.approval_election_combo.current(0)
            
            # Fetch pending voters
            ok, resp = self.api.get_voters()
            self.pending_voters_listbox.delete(0, tk.END)
            if not ok:
                # resp may be friendly string
                self.log_security(f"Failed to fetch voters: {resp}")
                return

            # resp expected to be a list of voters
            pending = [v for v in resp if v.get('status') == 'pending']
            if not pending:
                self.pending_voters_listbox.insert(tk.END, "No pending voters")
                return

            for v in pending:
                ts = v.get('created_at')
                try:
                    created = datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S') if ts else 'N/A'
                except Exception:
                    created = str(ts)
                voter_name = v.get('name', 'Anonymous')
                display = f"{v.get('voter_id')}  |  {voter_name}  |  {created}"
                self.pending_voters_listbox.insert(tk.END, display)
        except Exception as e:
            self.log_security(f"Error refreshing voters: {e}")

    def approve_selected_voter(self):
        """Approve the selected pending voter for the selected election via API"""
        try:
            # Check if election is selected
            election_selection = self.approval_election_var.get()
            if not election_selection:
                messagebox.showwarning("No Election", "Please select an election first.")
                return
            
            # Extract election_id
            election_id = election_selection.split(':')[0].strip()
            
            # Check if voter is selected
            sel = self.pending_voters_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a voter to approve.")
                return
            
            text = self.pending_voters_listbox.get(sel[0])
            if text == "No pending voters":
                return
                
            voter_id = text.split('|')[0].strip()

            # Call API with election_id
            ok, resp = self.api.approve_voter(voter_id, election_id)
            if not ok:
                messagebox.showerror("Approve Failed", f"Failed to approve voter: {resp}")
                self.log_security(f"Failed to approve {voter_id} for {election_id}: {resp}")
                return

            messagebox.showinfo("Approved", f"Voter {voter_id} approved for election {election_id}.")
            self.log_security(f"✅ Voter {voter_id} approved for election {election_id}")
            # Refresh list
            self.refresh_pending_voters()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_security(f"Error approving voter: {e}")

    def open_current_election(self):
        """Open the currently selected election (change from DRAFT to OPEN)"""
        try:
            if not self.current_election_id:
                messagebox.showwarning("No Election", "Please select an election first.")
                return
            
            # Get election details to check current status
            success, election = self.api.get_election(self.current_election_id)
            if not success:
                messagebox.showerror("Error", "Could not fetch election details.")
                return
            
            current_status = election.get('status', 'unknown').upper()
            
            if current_status == 'OPEN':
                messagebox.showinfo("Already Open", "This election is already open!")
                return
            elif current_status == 'CLOSED':
                messagebox.showwarning("Cannot Open", "This election has already ended. Cannot reopen a closed election.")
                return
            
            confirm = messagebox.askyesno(
                "Confirm Open Election", 
                f"Open '{election.get('name')}'?\n\n"
                "This will IMMEDIATELY:\n"
                "• Change status from DRAFT → OPEN\n"
                "• Allow approved voters to start voting NOW\n"
                "• Make the election visible to voters\n\n"
                "Note: Start/End dates are informational only.\n"
                "Opening happens right now when you click Yes."
            )
            if not confirm:
                return

            ok, resp = self.api.election_action(self.current_election_id, 'open')
            if not ok:
                messagebox.showerror("Error", f"Failed to open election: {resp}")
                return
            
            messagebox.showinfo(
                "Success", 
                f"✅ Election '{election.get('name')}' is now OPEN!\n\n"
                "Approved voters can start voting immediately."
            )
            self.log_security(f"✅ Election {self.current_election_id} opened for voting")
            self.refresh_dashboard()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening election: {str(e)}")
            print(f"❌ Error in open_current_election: {e}")

    def end_current_election(self):
        """End the currently selected election and display results"""
        try:
            if not self.current_election_id:
                messagebox.showwarning("No Election", "Please select an election first.")
                return

            confirm = messagebox.askyesno("Confirm End Election", "Are you sure you want to end this election? This will close voting and compute results.")
            if not confirm:
                return

            ok, resp = self.api.election_action(self.current_election_id, 'close')
            if not ok:
                messagebox.showerror("Error", f"Failed to end election: {resp}")
                return

            # Fetch results
            ok2, results = self.api.api_request('GET', f"/elections/{self.current_election_id}/results")
            if not ok2:
                messagebox.showinfo("Election Ended", "Election closed but results could not be fetched.")
                self.log_security(f"Election {self.current_election_id} closed; results fetch failed: {results}")
                self.refresh_dashboard()
                return

            # Show a simple results dialog
            total = results.get('total_votes', 0)
            winner = results.get('winner')
            msg = f"Election ended. Total votes: {total}\n\n"
            if winner:
                if isinstance(winner, dict) and winner.get('tie'):
                    names = ', '.join([w.get('name', w.get('candidate_id')) for w in winner.get('winners', [])])
                    msg += f"Result: TIE between: {names}\n"
                else:
                    msg += f"Winner: {winner.get('name', winner.get('candidate_id'))} with {winner.get('votes',0)} votes\n"
            else:
                msg += "No winner (no votes cast)\n"

            # Also populate the dashboard results area
            self.results_text.config(state='normal')
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert(tk.END, msg + "\nDetailed results:\n")
            for r in results.get('results', []):
                self.results_text.insert(tk.END, f"{r.get('name')}: {r.get('votes')} votes ({r.get('percentage'):.1f}%)\n")
            self.results_text.config(state='disabled')

            messagebox.showinfo("Election Results", msg)
            self.log_security(f"Election {self.current_election_id} ended. {msg.splitlines()[0]}")
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def block_selected_voter(self):
        """Block the selected voter via API"""
        try:
            sel = self.pending_voters_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a voter to block.")
                return
            text = self.pending_voters_listbox.get(sel[0])
            voter_id = text.split('|')[0].strip()

            confirm = messagebox.askokcancel("Confirm Block", f"Block voter {voter_id}? This will prevent them from voting.")
            if not confirm:
                return

            ok, resp = self.api.block_voter(voter_id)
            if not ok:
                messagebox.showerror("Block Failed", f"Failed to block voter: {resp}")
                self.log_security(f"Failed to block {voter_id}: {resp}")
                return

            messagebox.showinfo("Blocked", f"Voter {voter_id} blocked.")
            self.log_security(f"⛔ Voter blocked: {voter_id}")
            # Refresh list
            self.refresh_pending_voters()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def run(self):
        """Run"""
        try:
            print("🚀 Starting...")
            self.refresh_elections()
            self.app.mainloop()
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    try:
        app = AdminPanel()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()