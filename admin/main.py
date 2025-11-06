<<<<<<< HEAD
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Frame, Label, Entry, Button, Labelframe
from datetime import datetime, timedelta
from election_manager import ElectionManager
from database_connector import DatabaseConnector

class AdminPanelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗳️ BallotGuard - Admin Panel")
        self.root.geometry("1100x700")

        # Initialize connectors
        self.database = DatabaseConnector()
        self.election_manager = ElectionManager(self.database)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_election_creation_tab(self.notebook)
        self.create_election_management_tab(self.notebook)

    # ===========================
    # TAB 1: CREATE NEW ELECTION
    # ===========================
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

        # Candidates section
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

        Button(controls_frame, text="✅ Create Election", command=self.create_election_simple).pack(side="left", padx=10)
        Button(controls_frame, text="🔄 Clear Form", command=self.clear_form_simple).pack(side="left", padx=10)

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
        if not messagebox.askyesno("Confirm", f"Create election '{title}'?"):
            return
        success, msg, eid = self.election_manager.create_new_election(data)
        if success:
            messagebox.showinfo("Success", f"Election created! ID {eid}")
            self.clear_form_simple()
            self.refresh_elections_simple()
            self.notebook.select(1)
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

    # ===========================
    # TAB 2: MANAGE ELECTIONS
    # ===========================
    def create_election_management_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="🗂️ Election Management")

        top_frame = Frame(frame)
        top_frame.pack(fill="x", pady=10)

        Button(top_frame, text="🔄 Refresh", command=self.refresh_elections_simple).pack(side="left", padx=10)
        Button(top_frame, text="❌ Delete Selected", command=self.delete_selected_election).pack(side="left", padx=10)

        self.elections_listbox = tk.Listbox(frame, width=120, height=20, font=("Consolas", 11))
        self.elections_listbox.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh_elections_simple()

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
            messagebox.showwarning("Warning", "Select an election to delete.")
            return
        selected_text = self.elections_listbox.get(selection[0])
        election_id = selected_text.split("|")[0].replace("ID:", "").strip()
        if not messagebox.askyesno("Confirm", f"Delete election {election_id}?"):
            return
        success, msg = self.database.delete_election(election_id)
        if success:
            messagebox.showinfo("Deleted", msg)
            self.refresh_elections_simple()
        else:
            messagebox.showerror("Error", msg)

# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = AdminPanelApp(root)
    root.mainloop()
=======
"""Small launcher for the client GUI.

The voting UI's entrypoint in `client_app/voting/app.py` defines a
`main()` function (creates the Tk app and calls `mainloop`). Older
code imported `run_ui`, which does not exist and caused a crash when
running `python client_app\main.py`.

We import and call `main()` so `python client_app\main.py` works from
both cmd.exe and PowerShell.
"""

from client_app.voting.app import main


if __name__ == "__main__":
    main()
>>>>>>> client-app__blockchain
