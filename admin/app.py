"""
BallotGuard Admin Panel Application
"""

import tkinter as tk
from tkinter import ttk, messagebox, Frame, Label, Entry, Button, Labelframe
from datetime import datetime, timedelta
import requests
import json

class AdminPanelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BallotGuard Admin Panel")
        self.root.geometry("800x600")

        # Server configuration
        self.API_BASE = "http://127.0.0.1:8443"

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_election_creation_tab(self.notebook)
        self.create_election_management_tab(self.notebook)
        self.create_voter_management_tab(self.notebook)
        self.create_ledger_verification_tab(self.notebook)

    def api_request(self, method, endpoint, data=None):
        """Helper for API requests with error handling"""
        try:
            url = f"{self.API_BASE}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json=data)
            
            response.raise_for_status()
            return True, response.json()
        except requests.RequestException as e:
            return False, str(e)

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

        # Candidates section
        candidates_frame = Labelframe(form_frame, text="Candidates (minimum 2)", padding=20)
        candidates_frame.pack(fill="x", pady=20)

        self.candidate_entries = []
        self.candidates_container = Frame(candidates_frame)
        self.candidates_container.pack(fill="x")

        self.add_candidate()
        self.add_candidate()
        Button(candidates_frame, text="➕ Add Candidate", command=self.add_candidate).pack(pady=10)

        controls_frame = Frame(form_frame)
        controls_frame.pack(fill="x", pady=20)

        Button(controls_frame, text="✅ Create Election", command=self.create_election).pack(side="left", padx=10)
        Button(controls_frame, text="🔄 Clear Form", command=self.clear_form).pack(side="left", padx=10)

    def add_candidate(self):
        """Add candidate entry fields"""
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

    def create_election(self):
        """Create new election via API"""
        title = self.election_title_var.get().strip()
        desc = self.election_desc_var.get().strip()
        start = self.start_date_var.get()
        end = self.end_date_var.get()

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
            "name": title,
            "description": desc,
            "start_date": start,
            "end_date": end,
            "candidates": candidates,
        }

        if not messagebox.askyesno("Confirm", f"Create election '{title}'?"):
            return

        success, response = self.api_request("POST", "/elections", data)
        if success:
            messagebox.showinfo("Success", "Election created!")
            self.clear_form()
            self.refresh_elections()
            self.notebook.select(1)  # Switch to management tab
        else:
            messagebox.showerror("Error", str(response))

    def clear_form(self):
        """Clear election creation form"""
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
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

        # Add control buttons
        Button(top_frame, text="🔄 Refresh", command=self.refresh_elections).pack(side="left", padx=5)
        Button(top_frame, text="✅ Open", command=lambda: self.election_action("open")).pack(side="left", padx=5)
        Button(top_frame, text="⏸️ Pause", command=lambda: self.election_action("pause")).pack(side="left", padx=5)
        Button(top_frame, text="▶️ Resume", command=lambda: self.election_action("resume")).pack(side="left", padx=5)
        Button(top_frame, text="⏹️ Close", command=lambda: self.election_action("close")).pack(side="left", padx=5)
        Button(top_frame, text="📊 Tally", command=lambda: self.election_action("tally")).pack(side="left", padx=5)
        Button(top_frame, text="📦 Archive", command=self.archive_election).pack(side="left", padx=5)
        Button(top_frame, text="⚠️ Reset", command=self.reset_election).pack(side="left", padx=5)
        Button(top_frame, text="📥 Export Proof", command=self.export_proof).pack(side="left", padx=5)

        # Elections list
        self.elections_listbox = tk.Listbox(frame, width=120, height=20, font=("Consolas", 11))
        self.elections_listbox.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh_elections()

    def refresh_elections(self):
        """Refresh elections list from API"""
        self.elections_listbox.delete(0, tk.END)
        success, response = self.api_request("GET", "/elections")
        if success:
            for election in response:
                display_text = f"ID:{election['election_id']} | {election['name']} | {election['status']}"
                self.elections_listbox.insert(tk.END, display_text)
        else:
            self.elections_listbox.insert(tk.END, f"Error: {response}")

    def get_selected_election_id(self):
        """Get selected election ID from listbox"""
        selection = self.elections_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select an election first.")
            return None
        selected_text = self.elections_listbox.get(selection[0])
        return selected_text.split("|")[0].replace("ID:", "").strip()

    def election_action(self, action):
        """Perform election action (open/close/pause/etc)"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        if not messagebox.askyesno("Confirm", f"{action.title()} election {election_id}?"):
            return

        success, response = self.api_request("POST", f"/elections/{election_id}/{action}")
        if success:
            messagebox.showinfo("Success", f"Election {action}ed")
            self.refresh_elections()
        else:
            messagebox.showerror("Error", str(response))

    def archive_election(self):
        """Archive election"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        if not messagebox.askyesno("Confirm Archive", 
            "This will archive the election and make it read-only. Continue?"):
            return

        success, response = self.api_request("POST", f"/elections/{election_id}/archive")
        if success:
            messagebox.showinfo("Success", "Election archived")
            self.refresh_elections()
        else:
            messagebox.showerror("Error", str(response))

    def reset_election(self):
        """Reset election (demo only)"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        if not messagebox.askyesno("Confirm Reset", 
            "WARNING: This will reset all election data! Continue?"):
            return

        success, response = self.api_request("POST", f"/elections/{election_id}/reset")
        if success:
            messagebox.showinfo("Success", "Election reset")
            self.refresh_elections()
        else:
            messagebox.showerror("Error", str(response))

    def export_proof(self):
        """Export election proof bundle"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        success, response = self.api_request("GET", f"/elections/{election_id}/proof")
        if success:
            # Save proof bundle to file
            filename = f"proof_bundle_{election_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(response, f, indent=2)
                messagebox.showinfo("Success", f"Proof bundle saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
        else:
            messagebox.showerror("Error", str(response))

    # ===========================
    # TAB 3: VOTER MANAGEMENT
    # ===========================
    def create_voter_management_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="👥 Voter Management")

        top_frame = Frame(frame)
        top_frame.pack(fill="x", pady=10)
        
        Button(top_frame, text="🔄 Refresh", command=self.refresh_voters).pack(side="left", padx=5)
        Button(top_frame, text="✅ Approve", command=self.approve_voter).pack(side="left", padx=5)
        Button(top_frame, text="❌ Block", command=self.block_voter).pack(side="left", padx=5)

        # Voters list
        self.voters_listbox = tk.Listbox(frame, width=120, height=20, font=("Consolas", 11))
        self.voters_listbox.pack(fill="both", expand=True, padx=20, pady=10)

        self.refresh_voters()

    def refresh_voters(self):
        """Refresh voters list from API"""
        self.voters_listbox.delete(0, tk.END)
        success, response = self.api_request("GET", "/voters")
        if success:
            for voter in response:
                display_text = f"ID:{voter['voter_id']} | Status:{voter['status']} | Elections:{len(voter['eligible_elections'])}"
                self.voters_listbox.insert(tk.END, display_text)
        else:
            self.voters_listbox.insert(tk.END, f"Error: {response}")

    def get_selected_voter_id(self):
        """Get selected voter ID from listbox"""
        selection = self.voters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a voter first.")
            return None
        selected_text = self.voters_listbox.get(selection[0])
        return selected_text.split("|")[0].replace("ID:", "").strip()

    def approve_voter(self):
        """Approve selected voter"""
        voter_id = self.get_selected_voter_id()
        if not voter_id:
            return

        success, response = self.api_request("POST", f"/voters/{voter_id}/approve")
        if success:
            messagebox.showinfo("Success", "Voter approved")
            self.refresh_voters()
        else:
            messagebox.showerror("Error", str(response))

    def block_voter(self):
        """Block selected voter"""
        voter_id = self.get_selected_voter_id()
        if not voter_id:
            return

        if not messagebox.askyesno("Confirm Block", 
            "This will prevent the voter from voting. Continue?"):
            return

        success, response = self.api_request("POST", f"/voters/{voter_id}/block")
        if success:
            messagebox.showinfo("Success", "Voter blocked")
            self.refresh_voters()
        else:
            messagebox.showerror("Error", str(response))

    # ===========================
    # TAB 4: LEDGER VERIFICATION
    # ===========================
    def create_ledger_verification_tab(self, notebook):
        frame = Frame(notebook)
        notebook.add(frame, text="🔍 Ledger Verification")

        top_frame = Frame(frame)
        top_frame.pack(fill="x", pady=10)

        Button(top_frame, text="🔄 Verify Ledger", command=self.verify_ledger).pack(side="left", padx=5)
        Button(top_frame, text="📜 Show Last Block", command=self.show_last_block).pack(side="left", padx=5)

        # Results text area
        self.verification_text = tk.Text(frame, width=100, height=20, font=("Consolas", 11))
        self.verification_text.pack(fill="both", expand=True, padx=20, pady=10)

    def verify_ledger(self):
        """Verify ledger integrity"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        success, response = self.api_request("GET", f"/ledger/verify?election_id={election_id}")
        if success:
            self.verification_text.delete(1.0, tk.END)
            self.verification_text.insert(tk.END, json.dumps(response, indent=2))
        else:
            messagebox.showerror("Error", str(response))

    def show_last_block(self):
        """Show last block details"""
        election_id = self.get_selected_election_id()
        if not election_id:
            return

        success, response = self.api_request("GET", f"/ledger/last?election_id={election_id}")
        if success:
            self.verification_text.delete(1.0, tk.END)
            self.verification_text.insert(tk.END, json.dumps(response, indent=2))
        else:
            messagebox.showerror("Error", str(response))
