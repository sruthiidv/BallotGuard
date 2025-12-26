import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import json
import os

# Local modules (must be in same directory)
from database_connector import DatabaseConnector
from blockchain_connector import BlockchainConnector
from election_manager import ElectionManager


class AdminPanelApp:
    def __init__(self, master):
        self.master = master
        master.title("BallotGuard Admin Panel - Integrated")
        master.geometry("1100x720")

        # --- Connectors & Manager ---
        self.database = DatabaseConnector()
        self.blockchain = BlockchainConnector()
        self.election_manager = ElectionManager(self.database, self.blockchain)

        # --- Style & theme ---
        style = ttk.Style(theme='darkly')

        # --- Header ---
        self.header_frame = ttk.Frame(master, padding=10)
        self.header_frame.pack(fill="x")

        ttk.Label(self.header_frame, text="BallotGuard Admin Panel", font=("Arial", 20, "bold")).pack(side="left")

        db_status_text = "DATABASE CONNECTED"
        db_status_style = "success"
        ttk.Label(self.header_frame, text=db_status_text, bootstyle=db_status_style).pack(side="right", padx=15)

        # --- Notebook (tabs) ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Create tabs
        self.create_dashboard_tab(self.notebook)
        self.create_election_management_tab(self.notebook)
        self.create_election_creation_tab(self.notebook)
        self.create_security_monitor_tab(self.notebook)

        # Load initial data
        self.refresh_elections()
        self.update_dashboard_selection_ui()

    # -------------------------
    # Tab 1: Dashboard & Results
    # -------------------------
    def create_dashboard_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="📊 Dashboard & Results")

        # Top: Current Election selection and status
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(top_frame, text="Current Election:", font=("Arial", 12)).pack(side="left")
        self.current_election_var = tk.StringVar()
        self.current_election_dropdown = ttk.Combobox(top_frame, textvariable=self.current_election_var, state="readonly", width=60)
        self.current_election_dropdown.pack(side="left", padx=10)
        self.current_election_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_dashboard_selection_ui())

        ttk.Label(top_frame, text="Status:", font=("Arial", 12)).pack(side="left", padx=(20, 5))
        self.current_status_label = ttk.Label(top_frame, text="N/A", font=("Arial", 12, "bold"))
        self.current_status_label.pack(side="left")

        # Middle: Results display area
        results_frame = ttk.LabelFrame(frame, text="Election Results", padding=10, bootstyle="secondary")
        results_frame.pack(fill="both", expand=True)

        self.result_text = tk.Text(results_frame, height=15, wrap="none", font=("Courier", 10))
        self.result_text.pack(fill="both", expand=True, side="left", padx=(0, 5))
        self.result_text.config(state="disabled")

        scrollbar_v = ttk.Scrollbar(results_frame, orient="vertical", command=self.result_text.yview)
        scrollbar_v.pack(side="right", fill="y")
        self.result_text['yscrollcommand'] = scrollbar_v.set

        # Bottom: Result controls
        controls_frame = ttk.Frame(frame, padding=6)
        controls_frame.pack(fill="x", pady=(10, 0))

        self.view_results_btn = ttk.Button(controls_frame, text="View Results", command=self.view_results, bootstyle="info")
        self.view_results_btn.pack(side="left", padx=5)

        self.export_results_btn = ttk.Button(controls_frame, text="Export Results", command=self.export_results, bootstyle="success")
        self.export_results_btn.pack(side="left", padx=5)

        self.finalize_results_btn = ttk.Button(controls_frame, text="Finalize Results", command=self.finalize_results, bootstyle="warning")
        self.finalize_results_btn.pack(side="left", padx=5)

        # Blockchain state indicator in dashboard
        self.chain_status_label = ttk.Label(controls_frame, text="Chain: OK", bootstyle="success")
        self.chain_status_label.pack(side="right", padx=10)

    def update_dashboard_selection_ui(self):
        """Refresh dropdown options and show selected election details & chain status"""
        success, message, elections = self.database.get_elections()
        elections = elections if success and elections else []

        # Build dropdown options"
        options = [f"ID:{e['id']} - {e.get('title', 'Untitled')}" for e in elections]
        self.election_map = {f"ID:{e['id']} - {e.get('title', 'Untitled')}": e for e in elections}

        self.current_election_dropdown['values'] = options
        if options and not self.current_election_var.get():
            # default select first
            self.current_election_var.set(options[0])

        # Update status and results area
        sel = self.current_election_var.get()
        election = self.election_map.get(sel)
        if election:
            self.current_status_label.config(text=election.get('status', 'Unknown'))
            self.populate_results_text(election)
        else:
            self.current_status_label.config(text="N/A")
            self.clear_results_text()

        # Update chain label from blockchain connector
        status = self.blockchain.get_chain_status()
        if status.get("broken"):
            self.chain_status_label.config(text="Chain: BROKEN", bootstyle="danger")
            self.set_result_controls_state(enabled=False)
        else:
            self.chain_status_label.config(text="Chain: SECURE", bootstyle="success")
            self.set_result_controls_state(enabled=True)

    def populate_results_text(self, election):
        """Show real aggregated results in the text widget"""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        
        self.result_text.insert(tk.END, f"Election: {election.get('title')}\n")
        self.result_text.insert(tk.END, f"Status : {election.get('status')}\n\n")
        
        # Fetch real tallied results from database
        try:
            eid = election.get('id')
            ok, res = self.database.get_election_results(eid)
            
            if ok and res:
                self.result_text.insert(tk.END, "Candidate                         | Votes      | Percentage\n")
                self.result_text.insert(tk.END, "-"*65 + "\n")
                
                results_list = res.get('results', []) or []
                for r in results_list:
                    name = r.get('name', 'Unknown')
                    votes = r.get('votes', 0)
                    percentage = r.get('percentage', 0.0)
                    self.result_text.insert(tk.END, f"{name:<33} | {votes:<10} | {percentage:.1f}%\n")
                
                if not results_list:
                    self.result_text.insert(tk.END, "No results available yet.\n")
            else:
                # Fallback: show candidates without vote counts if results not available
                candidates = election.get('candidates', [])
                self.result_text.insert(tk.END, "Candidate                         | Votes\n")
                self.result_text.insert(tk.END, "-"*50 + "\n")
                if candidates:
                    for c in candidates:
                        name = c.get('name', 'Unnamed')
                        self.result_text.insert(tk.END, f"{name:<33} | --\n")
                else:
                    self.result_text.insert(tk.END, "No candidates found.\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"Error fetching results: {e}\n")
        
        self.result_text.config(state="disabled")

    def clear_results_text(self):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state="disabled")

    def set_result_controls_state(self, enabled=True):
        """Enable/disable result control buttons based on blockchain integrity"""
        state = "normal" if enabled else "disabled"
        for btn in (self.view_results_btn, self.export_results_btn, self.finalize_results_btn):
            btn.config(state=state)

    def view_results(self):
        # Just make sure chain is OK
        if self.blockchain.get_chain_status().get("broken"):
            messagebox.showerror("Security", "Cannot view results: blockchain compromised.")
            return
        sel = self.current_election_var.get()
        election = self.election_map.get(sel)
        if not election:
            messagebox.showwarning("No election", "Please select an election.")
            return
        # Try to get tallied results from the database connector
        try:
            eid = election.get('id')
            ok, res = self.database.get_election_results(eid)
            if not ok:
                messagebox.showerror("Error", f"Failed to fetch results: {res}")
                return

            # Build a readable summary
            total_votes = res.get('total_votes', 0)
            eligible = res.get('eligible_voters', 0)
            turnout = res.get('turnout_percentage', 0.0)
            results_list = res.get('results', []) or []

            summary = f"Results for '{election.get('title')}'\n\n"
            summary += f"Total votes: {total_votes}\nEligible voters: {eligible}\nTurnout: {turnout:.1f}%\n\n"
            for r in results_list:
                summary += f"{r.get('name', 'Unknown')} (id:{r.get('candidate_id')}): {r.get('votes',0)} votes ({r.get('percentage',0.0):.1f}%)\n"

            winner = res.get('winner')
            if winner:
                if isinstance(winner, dict) and winner.get('tie'):
                    winners = winner.get('winners', [])
                    win_names = ', '.join([w.get('name', w.get('candidate_id')) for w in winners])
                    summary += f"\nResult: TIE between: {win_names}\n"
                else:
                    summary += f"\nWinner: {winner.get('name', winner.get('candidate_id'))} with {winner.get('votes',0)} votes\n"

            # Show in a modal and also populate the results text
            messagebox.showinfo("Election Results", summary)
            # Also update the results pane
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, summary)
            self.result_text.config(state="disabled")

            # Refresh UI state (in case status changed)
            self.refresh_elections()
            self.update_dashboard_selection_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve results: {e}")

    def export_results(self):
        if self.blockchain.get_chain_status().get("broken"):
            messagebox.showerror("Security", "Cannot export results: blockchain compromised.")
            return
        sel = self.current_election_var.get()
        election = self.election_map.get(sel)
        if not election:
            messagebox.showwarning("No election", "Please select an election.")
            return

        # Fetch real tallied results from server
        try:
            eid = election.get('id')
            ok, res = self.database.get_election_results(eid)
            if not ok:
                messagebox.showerror("Error", f"Failed to fetch results: {res}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve results: {e}")
            return

        default_name = f"results_election_{election.get('id')}.json"
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=default_name,
                                            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            # Export complete results with tallies
            results = {
                "election_id": election.get('id'),
                "title": election.get('title'),
                "status": election.get('status'),
                "total_votes": res.get('total_votes', 0),
                "eligible_voters": res.get('eligible_voters', 0),
                "turnout_percentage": res.get('turnout_percentage', 0.0),
                "candidates": res.get('results', []),
                "winner": res.get('winner')
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            messagebox.showinfo("Exported", f"Results exported to {path}")

    def finalize_results(self):
        if self.blockchain.get_chain_status().get("broken"):
            messagebox.showerror("Security", "Cannot finalize: blockchain compromised.")
            return
        sel = self.current_election_var.get()
        election = self.election_map.get(sel)
        if not election:
            messagebox.showwarning("No election", "Please select an election.")
            return

        # Call manager to finalize election
        try:
            fn = getattr(self.election_manager, "finalize_election", None)
            if callable(fn):
                ok, msg = fn(election.get('id'))
            else:
                ok, msg = False, "Finalize not implemented in manager"
            
            if ok:
                messagebox.showinfo("Finalized", msg)
                self.refresh_elections()
                self.update_dashboard_selection_ui()
                # After finalizing, show final tallied results to admin
                try:
                    self.view_results()
                except Exception:
                    pass
            else:
                messagebox.showerror("Error", msg)
        except Exception as ex:
            messagebox.showerror("Error", f"Could not finalize: {ex}")

    # -------------------------
    # Tab 2: Election Management
    # -------------------------
    def create_election_management_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="🗳️ Election Management")

        ttk.Label(frame, text="Existing Elections:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill="both", expand=True)

        self.elections_listbox = tk.Listbox(listbox_frame, height=15, width=100, font=("Courier", 10))
        self.elections_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.elections_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.elections_listbox.config(yscrollcommand=scrollbar.set)

        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", pady=10)

        ttk.Button(controls_frame, text="🔄 Refresh List", command=self.refresh_elections, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="🗑️ Delete Selected Election", command=self.delete_election_ui, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="➕ Add New Election", command=lambda: self.notebook.select(2), bootstyle="success").pack(side="left", padx=5)

    def delete_election_ui(self):
        try:
            selected_index = self.elections_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("Selection Required", "Please select an election to delete.")
                return

            list_text = self.elections_listbox.get(selected_index[0])
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
        self.elections_listbox.delete(0, tk.END)
        success, message, elections = self.database.get_elections()
        if success and elections:
            for election in elections:
                display_text = f"ID:{election.get('id', 'N/A'):<4} | {election.get('title', 'Untitled'):<50} | STATUS: {election.get('status', 'Unknown'):<10}"
                self.elections_listbox.insert(tk.END, display_text)
        elif success and not elections:
            self.elections_listbox.insert(tk.END, "No elections found.")
        else:
            self.elections_listbox.insert(tk.END, f"Error: {message}")

        # Also refresh dashboard dropdown
        self.update_dashboard_selection_ui()

    # -------------------------
    # Tab 3: Create Election
    # -------------------------
    def create_election_creation_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="➕ Create Election")

        form_frame = ttk.LabelFrame(frame, text="Create New Election", padding=20, bootstyle="primary")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ttk.Label(form_frame, text="Election Title:", font=("Arial", 12)).pack(anchor="w", pady=(5, 0))
        self.election_title_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.election_title_var, width=80, bootstyle="primary").pack(fill="x", pady=5)

        # Description
        ttk.Label(form_frame, text="Description:", font=("Arial", 12)).pack(anchor="w", pady=(10, 0))
        self.election_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.election_desc_var, width=80, bootstyle="primary").pack(fill="x", pady=5)

        # Dates & voters
        dates_frame = ttk.Frame(form_frame)
        dates_frame.pack(fill="x", pady=10)
        ttk.Label(dates_frame, text="Start Date (YYYY-MM-DD):").pack(side="left")
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(dates_frame, textvariable=self.start_date_var, width=15).pack(side="left", padx=8)
        ttk.Label(dates_frame, text="End Date (YYYY-MM-DD):").pack(side="left", padx=(20, 5))
        self.end_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        ttk.Entry(dates_frame, textvariable=self.end_date_var, width=15).pack(side="left", padx=8)
        ttk.Label(dates_frame, text="Eligible Voters:").pack(side="left", padx=(20, 5))
        self.eligible_voters_var = tk.StringVar(value="1000")
        ttk.Entry(dates_frame, textvariable=self.eligible_voters_var, width=10).pack(side="left")

        # Candidates area
        candidates_frame = ttk.LabelFrame(form_frame, text="Candidates (min 2)", padding=10, bootstyle="info")
        candidates_frame.pack(fill="x", pady=10)
        self.candidates_container = ttk.Frame(candidates_frame)
        self.candidates_container.pack(fill="x")
        self.candidate_entries = []
        # initialize two candidate inputs
        self.add_candidate_row()
        self.add_candidate_row()
        ttk.Button(candidates_frame, text="➕ Add Candidate", command=self.add_candidate_row, bootstyle="info-outline").pack(pady=8)

        # Controls
        controls_frame = ttk.Frame(form_frame)
        controls_frame.pack(fill="x", pady=12)
        ttk.Button(controls_frame, text="✅ Create Election", command=self.create_election_handler, bootstyle="success").pack(side="left", padx=6)
        ttk.Button(controls_frame, text="🔄 Clear", command=self.clear_create_form, bootstyle="secondary").pack(side="left", padx=6)

    def add_candidate_row(self):
        frame = ttk.Frame(self.candidates_container)
        frame.pack(fill="x", pady=4)
        idx = len(self.candidate_entries) + 1
        ttk.Label(frame, text=f"Candidate {idx}:", width=12).pack(side="left")
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).pack(side="left", padx=5)
        ttk.Label(frame, text="Party:", width=8).pack(side="left")
        party_var = tk.StringVar()
        ttk.Entry(frame, textvariable=party_var, width=25).pack(side="left", padx=5)
        # allow removing additional candidates (not first two)
        if idx > 2:
            remove_btn = ttk.Button(frame, text="X", width=3, bootstyle="danger-outline", command=lambda f=frame: self.remove_candidate_row(f))
            remove_btn.pack(side="left", padx=6)
        self.candidate_entries.append({"frame": frame, "name_var": name_var, "party_var": party_var})

    def remove_candidate_row(self, frame):
        if len(self.candidate_entries) <= 2:
            return
        # remove from list and UI
        self.candidate_entries = [c for c in self.candidate_entries if c['frame'] is not frame]
        frame.destroy()
        # relabel
        for i, e in enumerate(self.candidate_entries):
            e['frame'].winfo_children()[0].config(text=f"Candidate {i+1}:")

    def create_election_handler(self):
        title = self.election_title_var.get().strip()
        desc = self.election_desc_var.get().strip()
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        try:
            voters = int(self.eligible_voters_var.get())
            if voters <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Validation", "Eligible voters must be a positive integer")
            return
        if not title or not desc:
            messagebox.showerror("Validation", "Title and description required")
            return

        candidates = []
        for entry in self.candidate_entries:
            name = entry['name_var'].get().strip()
            if name:
                party = entry['party_var'].get().strip() or "Independent"
                candidates.append({"name": name, "party": party})

        if len(candidates) < 2:
            messagebox.showerror("Validation", "At least 2 candidates required with names")
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

        # Try manager.create_new_election first, else fallback to database.create_election
        try:
            fn = getattr(self.election_manager, "create_new_election", None)
            if callable(fn):
                ok, msg, eid = fn(data)
            else:
                ok, msg, eid = self.database.create_election(data)
        except Exception as e:
            ok, msg, eid = False, f"Error: {e}", None

        if ok:
            messagebox.showinfo("Success", f"{msg} (ID {eid})")
            self.clear_create_form()
            self.refresh_elections()
            # switch to management tab
            self.notebook.select(1)
        else:
            messagebox.showerror("Error", msg)

    def clear_create_form(self):
        self.election_title_var.set("")
        self.election_desc_var.set("")
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var.set((datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.eligible_voters_var.set("1000")
        # clear candidate rows and create two empty
        for e in self.candidate_entries:
            e['frame'].destroy()
        self.candidate_entries = []
        self.add_candidate_row()
        self.add_candidate_row()

    # -------------------------
    # Tab 4: Security Monitor
    # -------------------------
    def create_security_monitor_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="🛡️ Security Monitor")

        ttk.Label(frame, text="Security Monitoring - Blockchain Integrity Checks", font=("Arial", 14)).pack(pady=(6, 12))

        info_frame = ttk.Frame(frame)
        info_frame.pack(fill="x", pady=6)

        self.chain_info_text = tk.Text(info_frame, height=8, wrap="word", font=("Arial", 10))
        self.chain_info_text.pack(fill="both", expand=False)
        self.chain_info_text.config(state="disabled")

        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", pady=10)

        ttk.Button(controls_frame, text="🔒 Verify Chain", command=self.verify_chain, bootstyle="info").pack(side="left", padx=6)
        ttk.Button(controls_frame, text="⚠️ Simulate Admin Modify Votes", command=self.simulate_admin_modification, bootstyle="danger").pack(side="left", padx=6)

        # Show current chain status on load
        self.verify_chain()

    def verify_chain(self):
        status = self.blockchain.get_chain_status()
        info = self.blockchain.get_vote_verification_info()
        self.chain_info_text.config(state="normal")
        self.chain_info_text.delete("1.0", tk.END)
        self.chain_info_text.insert(tk.END, f"Chain status: {status.get('status')} (broken={status.get('broken')})\n")
        self.chain_info_text.insert(tk.END, f"Total blocks: {status.get('total_blocks')}\n\n")
        self.chain_info_text.insert(tk.END, f"Verification:\n")
        for k, v in info.items():
            self.chain_info_text.insert(tk.END, f"{k}: {v}\n")
        self.chain_info_text.config(state="disabled")

        # update dashboard chain label & controls
        self.update_dashboard_selection_ui()

    def simulate_admin_modification(self):
        # Ask for confirmation
        if not messagebox.askyesno("Simulate", "This will simulate an admin attempting to modify votes and will BREAK the blockchain. Proceed?"):
            return

        # Call blockchain method to break the chain
        res = self.blockchain.break_chain_on_admin_modification("MANUAL_VOTE_MODIFICATION")
        # Update UI
        self.verify_chain()
        messagebox.showwarning("Security Breach", "Blockchain integrity violated! Chain marked as BROKEN.\n" + str(res))

    # -------------------------
    # App Run
    # -------------------------
def main():
    try:
        root = ttk.Window(themename="darkly")
    except Exception:
        root = tk.Tk()

    app = AdminPanelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
