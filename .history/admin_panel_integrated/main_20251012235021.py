import tkinter as tk
from tkinter import messagebox
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
        master.title("BallotGuard Admin Panel - Integrated")
        master.geometry("1000x700")

        # --- 1. Initialize Connectors and Manager ---
        self.database = DatabaseConnector()
        self.blockchain = BlockchainConnector()
        self.election_manager = ElectionManager(self.database, self.blockchain)

        # --- 2. Styling (Using the 'darkly' theme) ---
        style = ttk.Style(theme='darkly')

        # --- 3. Main UI Components ---
        self.header_frame = ttk.Frame(master, padding=10)
        self.header_frame.pack(fill="x")

        ttk.Label(self.header_frame, text="BallotGuard Admin Panel", font=("Arial", 20, "bold")).pack(side="left")

        db_status_text = "DATABASE CONNECTED" if self.database.db_available else "DATABASE MOCK MODE"
        db_status_style = "success" if self.database.db_available else "warning"
        ttk.Label(self.header_frame, text=db_status_text, bootstyle=db_status_style).pack(side="right", padx=15)

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- 4. Create Tabs ---
        self.create_dashboard_tab(self.notebook)
        self.create_election_management_tab(self.notebook)
        self.create_election_creation_tab(self.notebook)
        self.create_security_monitor_tab(self.notebook)

        # Initial data load
        self.refresh_elections()

    # =========================================================================
    # --- ELECTION MANAGEMENT TAB ---
    # =========================================================================
    def create_election_management_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=20)
        notebook.add(frame, text="🗳️ Election Management")

        ttk.Label(frame, text="Existing Elections:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill="both", expand=True)

        self.elections_listbox = tk.Listbox(listbox_frame, height=15, width=100, font=("Courier", 10))
        self.elections_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.elections_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.elections_listbox.config(yscrollcommand=scrollbar.set)

        # Control Buttons
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", pady=10)

        ttk.Button(controls_frame, text="🔄 Refresh List", command=self.refresh_elections, bootstyle="info").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="🗑️ Delete Selected Election", command=self.delete_election_ui, bootstyle="danger").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="➕ Add New Election", command=lambda: self.notebook.select(self.notebook.index("end") - 1), bootstyle="success").pack(side="left", padx=5)

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

            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete election '{title}' (ID: {election_id})?"):
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
                display_text = f"ID:{election.get('id', 'N/A'):<4} | {election.get('title', 'Untitled'):<40} | STATUS: {election.get('status', 'Unknown'):<10}"
                self.elections_listbox.insert(tk.END, display_text)
        elif success and not elections:
            self.elections_listbox.insert(tk.END, "No elections found.")
        else:
            self.elections_listbox.insert(tk.END, f"Error: {message}")

    # =========================================================================
    # --- DASHBOARD TAB ---
    # =========================================================================
    def create_dashboard_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=20)
        notebook.add(frame, text="📊 Dashboard & Results")
        ttk.Label(frame, text="Dashboard Content - Overall Stats, Results Summary", font=("Arial", 14)).pack()

    # =========================================================================
    # --- SECURITY TAB ---
    # =========================================================================
    def create_security_monitor_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=20)
        notebook.add(frame, text="🛡️ Security Monitor")
        ttk.Label(frame, text="Security Monitoring - Blockchain Integrity Checks", font=("Arial", 14)).pack()

    # =========================================================================
    # --- CREATE ELECTION TAB ---
    # =========================================================================
    def create_election_creation_tab(self, notebook):
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="➕ Create Election")

        form_frame = ttk.LabelFrame(frame, text="Create New Election", padding=30, bootstyle="primary")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(form_frame, text="(Form UI code omitted here for brevity, keep your working version)").pack()


if __name__ == "__main__":
    try:
        root = ttk.Window(themename="darkly")
    except:
        root = tk.Tk()

    app = AdminPanelApp(root)
    root.mainloop()
