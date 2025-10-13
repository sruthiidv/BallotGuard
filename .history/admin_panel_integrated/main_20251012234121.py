import tkinter as tk
from tkinter import messagebox, LabelFrame, Frame
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, timedelta

# Import necessary local modules
from database_connector import DatabaseConnector
from blockchain_connector import BlockchainConnector
from election_manager import ElectionManager

class AdminPanelApp:
    def __init__(self, master):
        self.master = master
        master.title("BallotGuard Admin Panel - Full Integration")
        master.geometry("1000x700")
        
        # --- 1. Initialize Connectors and Manager ---
        self.database = DatabaseConnector()
        self.blockchain = BlockchainConnector()
        self.election_manager = ElectionManager(self.database, self.blockchain)
        
        # --- 2. Styling (Using the 'darkly' theme which suits the screenshot) ---
        style = ttk.Style(theme='darkly')
        
        # --- 3. Main UI Components ---
        self.header_frame = Frame(master, padding=10)
        self.header_frame.pack(fill="x")
        
        Label(self.header_frame, text="BallotGuard Admin Panel", font=("Arial", 20, "bold")).pack(side="left")
        Label(self.header_frame, text="BLOCKCHAIN SECURE", bootstyle="success").pack(side="right")
        
        # Database Status Indicator (Simulation)
        db_status_text = "DATABASE CONNECTED" if self.database.db_available else "DATABASE MOCK MODE"
        db_status_style = "success" if self.database.db_available else "warning"
        Label(self.header_frame, text=db_status_text, bootstyle=db_status_style).pack(side="right", padx=15)

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # --- 4. Create Tabs ---
        self.create_dashboard_tab(self.notebook)
        self.create_election_management_tab(self.notebook) # New tab for management
        self.create_election_creation_tab(self.notebook)  # Your provided code goes here
        self.create_security_monitor_tab(self.notebook)
        
        # Initial data load
        self.refresh_elections()

    # =========================================================================
    # --- CORE TABS ---
    # =========================================================================

    def create_dashboard_tab(self, notebook):
        frame = Frame(notebook, padding=20)
        notebook.add(frame, text="📊 Dashboard & Results")
        Label(frame, text="Dashboard Content - Overall Stats, Results Summary", font=("Arial", 14)).pack()
        
    def create_security_monitor_tab(self, notebook):
        frame = Frame(notebook, padding=20)
        notebook.add(frame, text="🛡️ Security Monitor")
        Label(frame, text="Security Monitoring - Blockchain Integrity Checks", font=("Arial", 14)).pack()
        
    def create_election_management_tab(self, notebook):
        """Creates the Election Management tab where elections can be viewed and deleted."""
        frame = Frame(notebook, padding=20)
        notebook.add(frame, text="🗳️ Election Management")
        
        Label(frame, text="Existing Elections:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Listbox for Elections
        listbox_frame = Frame(frame)
        listbox_frame.pack(fill="both", expand=True)
        
        self.elections_listbox = tk.Listbox(listbox_frame, height=15, width=100)
        self.elections_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.elections_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.elections_listbox.config(yscrollcommand=scrollbar.set)
        
        # Control Buttons
        controls_frame = Frame(frame)
        controls_frame.pack(fill="x", pady=10)
        
        ttk.Button(controls_frame, text="🔄 Refresh List", command=self.refresh_elections, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="🗑️ Delete Selected Election", command=self.delete_election_ui, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="➕ Add New Election", command=lambda: self.notebook.select(self.notebook.index("end") - 1), bootstyle="success").pack(side="left", padx=5)


    # =========================================================================
    # --- ELECTION CRUD OPERATIONS ---
    # =========================================================================

    def delete_election_ui(self):
        """Deletes the selected election from the UI list."""
        try:
            selected_index = self.elections_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Selection Required", "Please select an election to delete.")
                return

            list_text = self.elections_listbox.get(selected_index[0])
            # Parse ID from the list text: "ID:1 | Title | Status"
            election_id_str = list_text.split('|')[0].replace('ID:', '').strip()
            election_id = int(election_id_str)
            title = list_text.split('|')[1].strip()

            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete election '{title}' (ID: {election_id})? This action is permanent."):
                success, msg = self.election_manager.delete_election(election_id)
                if success:
                    messagebox.showinfo("Success", msg)
                    self.refresh_elections()
                else:
                    messagebox.showerror("Error", msg)

        except Exception as e:
            messagebox.showerror("Error", f"Could not process deletion: {str(e)}")

    def refresh_elections(self):
        """Populates the election listbox with current data."""
        self.elections_listbox.delete(0, tk.END)
        success, message, elections = self.database.get_elections()
        if success and elections:
            for election in elections:
                display_text = f"ID:{election.get('id', 'N/A')} | {election.get('title', 'Untitled')} | {election.get('status', 'Unknown')}"
                self.elections_listbox.insert(tk.END, display_text)
        elif success and not elections:
            self.elections_listbox.insert(tk.END, "No elections found.")
        else:
            self.elections_listbox.insert(tk.END, f"Error: {message}")

    # =========================================================================
    # --- YOUR PROVIDED UI CODE (Adapted to Class Methods) ---
    # =========================================================================

    # NOTE: The provided UI functions must be part of the AdminPanelApp class 
    # to access 'self' (for member variables and other methods).

    def create_election_creation_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="➕ Create Election")

        form_frame = LabelFrame(frame, text="Create New Election", padding=30)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollbar for form
        canvas = tk.Canvas(form_frame)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollable_frame = Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        
        Label(scrollable_frame, text="Election Title:", font=("Arial", 12)).pack(anchor="w", pady=5)
        self.election_title_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.election_title_var, width=60).pack(fill="x", pady=5)

        Label(scrollable_frame, text="Description:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
        self.election_desc_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.election_desc_var, width=60).pack(fill="x", pady=5)

        dates_frame = Frame(scrollable_frame)
        dates_frame.pack(fill="x", pady=15)
        Label(dates_frame, text="Start Date (YYYY-MM-DD):", font=("Arial", 12)).pack(side="left")
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(dates_frame, textvariable=self.start_date_var, width=15).pack(side="left", padx=10)
        Label(dates_frame, text="End Date:", font=("Arial", 12)).pack(side="left", padx=(20, 0))
        self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        ttk.Entry(dates_frame, textvariable=self.end_date_var, width=15).pack(side="left", padx=10)

        Label(scrollable_frame, text="Eligible Voters:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
        self.eligible_voters_var = tk.StringVar(value="1000")
        ttk.Entry(scrollable_frame, textvariable=self.eligible_voters_var, width=20).pack(anchor="w", pady=5)

        candidates_frame = LabelFrame(scrollable_frame, text="Candidates (minimum 2)", padding=20)
        candidates_frame.pack(fill="x", pady=20)

        self.candidate_entries = []
        self.candidates_container = Frame(candidates_frame)
        self.candidates_container.pack(fill="x")

        self.add_simple_candidate()
        self.add_simple_candidate()
        ttk.Button(candidates_frame, text="➕ Add Candidate", command=self.add_simple_candidate).pack(pady=10)

        controls_frame = Frame(scrollable_frame)
        controls_frame.pack(fill="x", pady=20)

        ttk.Button(controls_frame, text="✅ Create Election", command=self.create_election_simple, bootstyle="success").pack(side="left", padx=10)
        ttk.Button(controls_frame, text="🔄 Clear Form", command=self.clear_form_simple, bootstyle="secondary").pack(side="left", padx=10)

    def add_simple_candidate(self):
        candidate_frame = Frame(self.candidates_container)
        candidate_frame.pack(fill="x", pady=3)
        num = len(self.candidate_entries) + 1
        Label(candidate_frame, text=f"Candidate {num}:", width=12).pack(side="left")
        name_var = tk.StringVar()
        ttk.Entry(candidate_frame, textvariable=name_var, width=25).pack(side="left", padx=5)
        Label(candidate_frame, text="Party:", width=8).pack(side="left")
        party_var = tk.StringVar()
        ttk.Entry(candidate_frame, textvariable=party_var, width=20).pack(side="left", padx=5)
        
        # Add a remove button for added candidates (not the first two)
        if num > 2:
            ttk.Button(candidate_frame, text="X", command=lambda f=candidate_frame: self.remove_candidate(f), bootstyle="danger-outline", width=3).pack(side="left", padx=5)
            
        self.candidate_entries.append({'name_var': name_var, 'party_var': party_var, 'frame': candidate_frame})

    def remove_candidate(self, frame_to_remove):
        """Removes a candidate entry field from the UI."""
        if len(self.candidate_entries) > 2:
            self.candidate_entries = [entry for entry in self.candidate_entries if entry['frame'] is not frame_to_remove]
            frame_to_remove.destroy()
            self.relabel_candidates()

    def relabel_candidates(self):
        """Updates the Candidate labels after a deletion."""
        for i, entry in enumerate(self.candidate_entries):
            # Assumes the first child of the candidate_frame is the label
            entry['frame'].winfo_children()[0].config(text=f"Candidate {i+1}:")

    def create_election_simple(self):
        title = self.election_title_var.get().strip()
        desc = self.election_desc_var.get().strip()
        start = self.start_date_var.get()
        end = self.end_date_var.get()
        try:
            voters = int(self.eligible_voters_var.get())
            if voters <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Validation Error", "Eligible voters must be positive integer")
            return
        if not title or not desc:
            messagebox.showerror("Validation Error", "Title and description required")
            return
        candidates = []
        for entry in self.candidate_entries:
            name = entry['name_var'].get().strip()
            # Ensure candidate entry is not empty before processing
            if name or entry['party_var'].get().strip(): 
                party = entry['party_var'].get().strip() or "Independent"
                if name:
                    candidates.append({"name": name, "party": party})
        
        if len(candidates) < 2:
            messagebox.showerror("Validation Error", "At least 2 candidates needed with names")
            return
        
        data = {
            "title": title,
            "description": desc,
            "start_date": f"{start}T00:00:00",
            "end_date": f"{end}T23:59:59",
            "eligible_voters": voters,
            "candidates": candidates
        }
        
        if not messagebox.askyesno("Confirm", f"Create election '{title}'?"): return
        
        success, msg, eid = self.election_manager.create_new_election(data)
        
        if success:
            messagebox.showinfo("Success", f"Election created! ID {eid}")
            self.clear_form_simple()
            self.refresh_elections() # Update the Election Management list
            self.notebook.select(1) # Switch to Election Management tab (index 1)
        else:
            messagebox.showerror("Error", msg)

    def clear_form_simple(self):
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.eligible_voters_var.set("1000")
        
        # Clear existing entries and recreate the minimum two
        for entry in self.candidate_entries:
            entry['frame'].destroy()
        self.candidate_entries = []
        self.add_simple_candidate()
        self.add_simple_candidate()


if __name__ == "__main__":
    # Ensure ttkbootstrap is available or fall back to standard tkinter
    try:
        root = ttk.Window(themename="darkly") # Use ttk.Window for themes
    except:
        root = tk.Tk() # Fallback

    app = AdminPanelApp(root)
    root.mainloop()