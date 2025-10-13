# main.py
import ttkbootstrap as ttkb
from ttkbootstrap import Frame, Label, Button, Labelframe, Progressbar, Notebook, Entry, Text, Combobox
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import time
import requests
import random
from datetime import datetime, timedelta

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
        self.database = DatabaseConnector()
        self.blockchain = BlockchainConnector()
        self.election_manager = ElectionManager(self.database, self.blockchain)
        self.current_election_id = 1

        self.app = ttkb.Window(themename="superhero")
        self.app.title("BallotGuard Admin Panel")
        self.app.geometry("1200x900")
        self.setup_ui()
        self.refresh_elections()
        self.app.mainloop()

    def setup_ui(self):
        notebook = Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)
        self.notebook = notebook

        # Dashboard tab (keep your implementation)
        dashboard = Frame(notebook)
        notebook.add(dashboard, text="Dashboard & Results")
        # ... add your dashboard code here or re-use existing ...

        self.create_election_management_tab(notebook)
        self.create_election_creation_tab(notebook)

    def create_election_creation_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="➕ Create Election")

        form_frame = Labelframe(frame, text="Create New Election", padding=30)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        Label(form_frame, text="Election Title:", font=("Arial", 12)).pack(anchor="w", pady=5)
        self.election_title_var = tk.StringVar()
        Entry(form_frame, textvariable=self.election_title_var, width=60).pack(fill="x", pady=5)

        Label(form_frame, text="Description:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
        self.election_desc_var = tk.StringVar()
        Entry(form_frame, textvariable=self.election_desc_var, width=60).pack(fill="x", pady=5)

        dates_frame = Frame(form_frame)
        dates_frame.pack(fill="x", pady=15)
        Label(dates_frame, text="Start Date (YYYY-MM-DD):", font=("Arial", 12)).pack(side="left")
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        Entry(dates_frame, textvariable=self.start_date_var, width=15).pack(side="left", padx=10)
        Label(dates_frame, text="End Date:", font=("Arial", 12)).pack(side="left", padx=(20, 0))
        self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        Entry(dates_frame, textvariable=self.end_date_var, width=15).pack(side="left", padx=10)

        Label(form_frame, text="Eligible Voters:", font=("Arial", 12)).pack(anchor="w", pady=(15, 5))
        self.eligible_voters_var = tk.StringVar(value="1000")
        Entry(form_frame, textvariable=self.eligible_voters_var, width=20).pack(anchor="w", pady=5)

        candidates_frame = Labelframe(form_frame, text="Candidates (minimum 2)", padding=20)
        candidates_frame.pack(fill="x", pady=20)
        self.candidate_entries = []
        self.candidates_container = Frame(candidates_frame)
        self.candidates_container.pack(fill="x")
        self.add_simple_candidate()
        self.add_simple_candidate()
        Button(candidates_frame, text="➕ Add Candidate", command=self.add_simple_candidate).pack(pady=10)

        controls_frame = Frame(form_frame)
        controls_frame.pack(fill="x", pady=20)
        Button(controls_frame, text="✅ Create Election", command=self.create_election_simple, bootstyle="success").pack(side="left", padx=10)
        Button(controls_frame, text="🔄 Clear Form", command=self.clear_form_simple, bootstyle="secondary").pack(side="left", padx=10)

    def add_simple_candidate(self):
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
            party = entry['party_var'].get().strip() or "Independent"
            if name:
                candidates.append({"name": name, "party": party})
        if len(candidates) < 2:
            messagebox.showerror("Validation Error", "At least 2 candidates needed")
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
            self.refresh_elections()
            self.refresh_elections_simple()
            self.notebook.select(1)  # Switch to management tab after creation
        else:
            messagebox.showerror("Error", msg)

    def clear_form_simple(self):
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.eligible_voters_var.set("1000")
        for entry in self.candidate_entries:
            entry['name_var'].set("")
            entry['party_var'].set("")

    def create_election_management_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="Election Management")
        list_frame = Labelframe(frame, text="All Elections", padding=20)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        self.elections_listbox = tk.Listbox(list_frame, height=15, font=("Arial", 12))
        self.elections_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        controls_frame = Frame(frame)
        controls_frame.pack(fill="x", pady=10)
        Button(controls_frame, text="🔄 Refresh Elections", command=self.refresh_elections_simple, bootstyle="primary").pack(side="left", padx=5)
        Button(controls_frame, text="❌ Delete Selected", command=self.delete_selected_election, bootstyle="danger").pack(side="left", padx=5)
        self.refresh_elections_simple()

    def refresh_elections(self):
        # Also update dropdowns etc. in other tabs if needed
        pass

    def refresh_elections_simple(self):
        self.elections_listbox.delete(0, tk.END)
        success, message, elections = self.database.get_elections()
        if success:
            for election in elections:
                display_text = f"ID:{election['id']} | {election['title']} | {election['status']}"
                self.elections_listbox.insert(tk.END, display_text)
        else:
            self.elections_listbox.insert(tk.END, f"Error: {message}")

    def delete_selected_election(self):
        selection = self.elections_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an election to delete.")
            return
        selected_text = self.elections_listbox.get(selection[0])
        election_id = int(selected_text.split("|")[0].replace("ID:", "").strip())
        if not messagebox.askyesno("Confirm Delete", f"Delete election ID {election_id}? This cannot be undone."):
            return
        try:
            r = requests.delete(f"{self.database.flask_server_url}/api/elections/{election_id}", timeout=10)
            if r.status_code == 200:
                messagebox.showinfo("Deleted", f"Election {election_id} deleted.")
                self.refresh_elections_simple()
            else:
                messagebox.showerror("Delete Failed", r.text)
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    AdminPanel()
