import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import cv2
import base64
import uuid
import time
from PIL import Image, ImageTk
import io
import numpy as np
import sys
import os
# Add the client_app directory to the Python path so package imports work when running this file directly
# When this file is executed directly, Python's import path (sys.path[0]) is the
# `client_app/voting` directory which prevents importing the top-level
# `client_app` package. Insert the repository's BallotGuard root so imports like
# `client_app.storage.localdb` resolve when running the script directly.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from client_app.storage.localdb import init, store_receipt

# Import client_app modules
try:
    # Prefer absolute package imports (works when running as module or via run_voter.ps1)
    from client_app.auth.face_verify import capture_face_photo, detect_faces, draw_face_rectangles, capture_face_encoding, bgr_to_jpeg_base64, check_liveness
    from client_app.crypto.vote_crypto import prepare_vote_data, generate_vote_id, verify_vote_receipt
    from client_app.api_client import BallotGuardAPI
    from client_app.client_config import SERVER_BASE
except Exception:
    # Fallback to relative imports (if executed in a different context)
    from auth.face_verify import capture_face_photo, detect_faces, draw_face_rectangles, capture_face_encoding, bgr_to_jpeg_base64
    from crypto.vote_crypto import prepare_vote_data, generate_vote_id, verify_vote_receipt
    from api_client import BallotGuardAPI
    from client_app.client_config import SERVER_BASE

# --- Initialize the database ---
init()

# Initialize API client
api_client = BallotGuardAPI()

class BallotGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("BallotGuard - Digital Voting System")
        self.geometry("900x650")
        self.minsize(800, 600)  # Set minimum window size
        self.resizable(True, True)  # Enable window resizing
        
        # Center window on screen
        self.center_window()
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize frames
        self.frames = {}
        self.current_frame = None
        
        # App state
        self.user_data = {
            "role": None,
            "voter_id": None,
            "name": None,
            "face_data": None,
            "selected_election": None,
            "registrations": {},  # Track registration status per election
            "voted_elections": set()  # Track elections user has voted in
        }
        
        self.create_frames()
        self.show_frame("MainMenu")
    
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_frames(self):
        """Create all application frames"""
        # Main menu frame
        self.frames["MainMenu"] = MainMenuFrame(self)
        
        # Voter frames
        self.frames["VoterMenu"] = VoterMenuFrame(self)
        self.frames["Registration"] = RegistrationFrame(self)
        self.frames["FaceVerification"] = FaceVerificationFrame(self)
        self.frames["VotingInterface"] = VotingInterfaceFrame(self)
        
        # Admin frames (placeholder for future)
        self.frames["AdminMenu"] = AdminMenuFrame(self)
        
        # Auditor frames (placeholder for future)
        self.frames["AuditorMenu"] = AuditorMenuFrame(self)
        
        # Place all frames
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def show_frame(self, frame_name):
        """Show the specified frame"""
        if self.current_frame:
            self.frames[self.current_frame].grid_remove()
        
        self.frames[frame_name].grid()
        self.current_frame = frame_name
        
        # Call frame's on_show method if it exists
        if hasattr(self.frames[frame_name], 'on_show'):
            self.frames[frame_name].on_show()

class MainMenuFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.configure(fg_color="transparent")
        self.create_widgets()
    
    def create_widgets(self):
        # Configure grid to make it responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main scrollable container
        scrollable = ctk.CTkScrollableFrame(self)
        scrollable.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        scrollable.grid_columnconfigure(0, weight=1)

        # Centered container for all content
        container = ctk.CTkFrame(scrollable, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)

        # Welcome message frame
        welcome_frame = ctk.CTkFrame(container, fg_color="transparent")
        welcome_frame.grid(row=0, column=0, sticky="n", pady=(40, 20))

        # Logo frame with PNG logo
        logo_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(30, 20))
        
        # Load and display PNG logo
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Untitled design.png')
        if os.path.exists(logo_path):
            try:
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(180, 180)  # Slightly larger logo
                )
                logo_label = ctk.CTkLabel(
                    logo_frame,
                    text="",  # No text, just image
                    image=logo_image
                )
                logo_label.image = logo_image  # Keep reference
            except Exception as e:
                # Fallback to emoji if image loading fails
                logo_label = ctk.CTkLabel(
                    logo_frame,
                    text="🗳️",  # Ballot box emoji
                    font=ctk.CTkFont(size=130)
                )
        else:
            # Fallback to emoji if file doesn't exist
            logo_label = ctk.CTkLabel(
                logo_frame,
                text="🗳️",  # Ballot box emoji
                font=ctk.CTkFont(size=130)
            )
        logo_label.grid(row=0, column=0)

        # App title
        title_label = ctk.CTkLabel(
            welcome_frame,
            text="BallotGuard",
            font=ctk.CTkFont(size=52, weight="bold")
        )
        title_label.grid(row=1, column=0, pady=(10, 5))

        # App subtitle
        subtitle_label = ctk.CTkLabel(
            welcome_frame,
            text="Secure Digital Voting System",
            font=ctk.CTkFont(size=22)
        )
        subtitle_label.grid(row=2, column=0, pady=(5, 30))

        # Enter button with clear call to action
        enter_btn = ctk.CTkButton(
            welcome_frame,
            text="Start Voting",
            font=ctk.CTkFont(size=20, weight="bold"),
            width=350,
            height=60,
            corner_radius=10,
            command=self.select_voter_role
        )
        enter_btn.grid(row=3, column=0, pady=(20, 40))

    
    def select_voter_role(self):
        self.parent.user_data["role"] = "voter"
        self.parent.show_frame("VoterMenu")
    
    def select_admin_role(self):
        self.parent.user_data["role"] = "admin"
        self.parent.show_frame("AdminMenu")
    
    def select_auditor_role(self):
        self.parent.user_data["role"] = "auditor"
        self.parent.show_frame("AuditorMenu")

class VoterMenuFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.configure(fg_color="transparent")
        self.create_widgets()
    
    def create_widgets(self):
        # Configure grid for responsive layout
        self.grid_rowconfigure(2, weight=1)  # Elections frame row
        self.grid_columnconfigure(0, weight=1)
        
        # Top Go Back button
        top_back_btn = ctk.CTkButton(
            self,
            text="← Go Back to Menu",
            font=ctk.CTkFont(size=14),
            width=160,
            height=36,
            command=lambda: self.parent.show_frame("MainMenu")
        )
        top_back_btn.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")

        # Header with Refresh button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=1, column=0, pady=(10, 15), padx=30, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Available Elections",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=15),
            width=140,
            height=42,
            corner_radius=8,
            command=self.load_elections
        )
        refresh_btn.grid(row=0, column=1, padx=(15, 0))

        # Elections list (scrollable)
        self.elections_frame = ctk.CTkScrollableFrame(self)
        self.elections_frame.grid(row=2, column=0, pady=(10, 15), padx=30, sticky="nsew")
        self.elections_frame.grid_columnconfigure(0, weight=1)

        # Bottom Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Main Menu",
            font=ctk.CTkFont(size=14),
            width=180,
            height=40,
            command=lambda: self.parent.show_frame("MainMenu")
        )
        back_btn.grid(row=3, column=0, pady=(10, 25))
    
    def on_show(self):
        """Load elections when frame is shown"""
        self.load_elections()
    
    def load_elections(self):
        """Fetch elections from server"""
        # Clear existing widgets
        for widget in self.elections_frame.winfo_children():
            widget.destroy()
        
        try:
            elections, error = api_client.get_elections()
            if error:
                self.show_error(error)
            else:
                self.display_elections(elections)
        except Exception as e:
            self.show_error(f"Failed to load elections: {str(e)}")
    
    def display_elections(self, elections):
        """Display elections in the scrollable frame"""
        if not elections:
            no_elections_label = ctk.CTkLabel(
                self.elections_frame,
                text="No elections available",
                font=ctk.CTkFont(size=18)
            )
            no_elections_label.grid(row=0, column=0, pady=40)
            return
        
        for idx, election in enumerate(elections):
            # Election card
            election_card = ctk.CTkFrame(self.elections_frame)
            election_card.grid(row=idx, column=0, pady=12, padx=15, sticky="ew")
            election_card.grid_columnconfigure(0, weight=1)
            
            # Election info container
            info_container = ctk.CTkFrame(election_card, fg_color="transparent")
            info_container.grid(row=0, column=0, sticky="ew", padx=15, pady=12)
            info_container.grid_columnconfigure(0, weight=1)
            
            # Election name
            name_label = ctk.CTkLabel(
                info_container,
                text=election.get("name", "Unknown Election"),
                font=ctk.CTkFont(size=20, weight="bold"),
                anchor="w"
            )
            name_label.grid(row=0, column=0, sticky="w", pady=(5, 8))
            
            # Election ID
            id_label = ctk.CTkLabel(
                info_container,
                text=f"ID: {election.get('election_id', 'Unknown')}",
                font=ctk.CTkFont(size=13)
            )
            id_label.grid(row=1, column=0, sticky="w", pady=2)
            
            # Status
            status_label = ctk.CTkLabel(
                info_container,
                text=f"Status: {election.get('status', 'Unknown')}",
                font=ctk.CTkFont(size=13)
            )
            status_label.grid(row=2, column=0, sticky="w", pady=(2, 5))
            
            # Check registration status
            voter_status = self.check_voter_status(election.get('election_id'))
            
            # Action buttons
            button_frame = ctk.CTkFrame(election_card, fg_color="transparent")
            button_frame.grid(row=1, column=0, pady=(5, 12), padx=15, sticky="w")
            
            # Handle different voter statuses for this election
            if voter_status == "voted":
                voted_btn = ctk.CTkButton(
                    button_frame,
                    text="✓ Already Voted",
                    width=150,
                    height=38,
                    state="disabled",
                    fg_color="green",
                    text_color="white",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                voted_btn.grid(row=0, column=0, padx=(0, 8))
                
            elif voter_status == "not_registered":
                register_btn = ctk.CTkButton(
                    button_frame,
                    text="Register",
                    width=130,
                    height=38,
                    font=ctk.CTkFont(size=14),
                    command=lambda e=election: self.register_for_election(e)
                )
                register_btn.grid(row=0, column=0, padx=(0, 8))
                
                vote_btn = ctk.CTkButton(
                    button_frame,
                    text="Vote",
                    width=130,
                    height=38,
                    state="disabled",
                    font=ctk.CTkFont(size=14)
                )
                vote_btn.grid(row=0, column=1)
                
            elif voter_status == "pending":
                status_btn = ctk.CTkButton(
                    button_frame,
                    text="⏳ Pending Approval",
                    width=170,
                    height=38,
                    state="disabled",
                    fg_color="orange",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                status_btn.grid(row=0, column=0)
                
            elif voter_status == "approved":
                vote_btn = ctk.CTkButton(
                    button_frame,
                    text="🗳️ Vote Now",
                    width=150,
                    height=38,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    command=lambda e=election: self.vote_in_election(e)
                )
                vote_btn.grid(row=0, column=0)
            
            elif voter_status == "blocked":
                blocked_btn = ctk.CTkButton(
                    button_frame,
                    text="🚫 Blocked",
                    width=130,
                    height=38,
                    state="disabled",
                    fg_color="red",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                blocked_btn.grid(row=0, column=0)
    
    def check_voter_status(self, election_id):
        """Check voter registration status for this specific election"""
        voter_id = self.parent.user_data.get("voter_id")
        if not voter_id:
            return "not_registered"

        try:
            # Check local registration cache first to see if user actually registered for THIS election
            key = f"{election_id}_{voter_id}"
            locally_registered = key in self.parent.user_data.get("registrations", {})
            
            # Use the new per-election status check endpoint
            result, err = api_client.get_voter_election_status(voter_id, election_id)
            if err:
                # Fall back to local cache if server is unreachable
                if locally_registered:
                    reg_data = self.parent.user_data["registrations"][key]
                    return reg_data.get("status", "not_registered")
                return "not_registered"

            # Check the election-specific approval
            if result.get("approved"):
                if result.get("already_voted"):
                    return "voted"  # Already voted in this election
                return "approved"
            else:
                reason = result.get("reason", "not_approved_for_election")
                if reason == "voter_not_found":
                    return "not_registered"
                elif reason == "not_approved_for_election":
                    # Only show "pending" if user actually registered for this election
                    if locally_registered:
                        return "pending"  # Registered for THIS election but not approved yet
                    else:
                        return "not_registered"  # Never registered for this election
                else:
                    return "blocked"
        except Exception:
            # On any error, fall back to local cache
            key = f"{election_id}_{voter_id}"
            if key in self.parent.user_data.get("registrations", {}):
                reg_data = self.parent.user_data["registrations"][key]
                return reg_data.get("status", "not_registered")
            return "not_registered"
    
    def check_if_already_voted(self, election_id):
        """Check if voter has already voted in this election"""
        voter_id = self.parent.user_data.get("voter_id")
        if not voter_id:
            return False
        
        # Check if we have voted locally (stored after successful vote)
        voted_elections = self.parent.user_data.get("voted_elections", set())
        election_voter_key = f"{election_id}_{voter_id}"
        
        return election_voter_key in voted_elections
    
    def register_for_election(self, election):
        """Register for specific election"""
        self.parent.user_data["selected_election"] = election
        self.parent.show_frame("Registration")
    
    def vote_in_election(self, election):
        """Vote in specific election"""
        self.parent.user_data["selected_election"] = election
        self.parent.show_frame("FaceVerification")
    
    def show_error(self, message):
        """Show error message"""
        error_label = ctk.CTkLabel(
            self.elections_frame,
            text=f"Error: {message}",
            text_color="red",
            font=ctk.CTkFont(size=14)
        )
        error_label.pack(pady=20)

class ElectionListFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.elections = []
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=20, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Available Elections",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Elections list (scrollable)
        self.elections_frame = ctk.CTkScrollableFrame(self, height=400)
        self.elections_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Voter Menu",
            command=lambda: self.parent.show_frame("VoterMenu")
        )
        back_btn.pack(pady=20)
    
    def on_show(self):
        """Load elections when frame is shown"""
        self.load_elections()
    
    def load_elections(self):
        """Fetch elections from server"""
        # Clear existing widgets
        for widget in self.elections_frame.winfo_children():
            widget.destroy()
        
        try:
            elections, error = api_client.get_elections()
            if error:
                self.show_error(error)
            else:
                self.elections = elections
                self.display_elections()
        except Exception as e:
            self.show_error(f"Failed to load elections: {str(e)}")
    
    def display_elections(self):
        """Display elections in the scrollable frame"""
        if not self.elections:
            no_elections_label = ctk.CTkLabel(
                self.elections_frame,
                text="No elections available",
                font=ctk.CTkFont(size=16)
            )
            no_elections_label.pack(pady=20)
            return
        
        for election in self.elections:
            # Election card
            election_card = ctk.CTkFrame(self.elections_frame)
            election_card.pack(pady=10, padx=10, fill="x")
            
            # Election info
            name_label = ctk.CTkLabel(
                election_card,
                text=election.get("name", "Unknown Election"),
                font=ctk.CTkFont(size=18, weight="bold")
            )
            name_label.pack(pady=10, anchor="w")
            
            id_label = ctk.CTkLabel(
                election_card,
                text=f"ID: {election.get('election_id', 'Unknown')}",
                font=ctk.CTkFont(size=12)
            )
            id_label.pack(anchor="w")
            
            status_label = ctk.CTkLabel(
                election_card,
                text=f"Status: {election.get('status', 'Unknown')}",
                font=ctk.CTkFont(size=12)
            )
            status_label.pack(anchor="w")
            
            # Action buttons
            button_frame = ctk.CTkFrame(election_card)
            button_frame.pack(pady=10, fill="x")
            
            register_btn = ctk.CTkButton(
                button_frame,
                text="Register",
                width=100,
                command=lambda e=election: self.register_for_election(e)
            )
            register_btn.pack(side="left", padx=5)
            
            vote_btn = ctk.CTkButton(
                button_frame,
                text="Vote",
                width=100,
                command=lambda e=election: self.vote_in_election(e)
            )
            vote_btn.pack(side="left", padx=5)
    
    def register_for_election(self, election):
        """Register for specific election"""
        self.parent.user_data["selected_election"] = election
        self.parent.show_frame("Registration")
    
    def vote_in_election(self, election):
        """Vote in specific election"""
        self.parent.user_data["selected_election"] = election
        self.parent.show_frame("FaceVerification")
    
    def show_error(self, message):
        """Show error message"""
        error_label = ctk.CTkLabel(
            self.elections_frame,
            text=f"Error: {message}",
            text_color="red",
            font=ctk.CTkFont(size=14)
        )
        error_label.pack(pady=20)

class RegistrationFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.photo_image = None
        self.captured_frame = None
        self.face_encoding = None
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=20, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Voter Registration",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        self.election_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.election_label.pack()
        
        # Registration form - MAKE IT SCROLLABLE
        form_scroll = ctk.CTkScrollableFrame(self, height=350)
        form_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Name input
        name_label = ctk.CTkLabel(
            form_scroll,
            text="Full Name:",
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(pady=(20, 5), anchor="w")
        
        self.name_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="Enter your full name",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.name_entry.pack(pady=(0, 20), fill="x")
        
        # Photo capture section
        photo_frame = ctk.CTkFrame(form_scroll)
        photo_frame.pack(pady=10, fill="x")
        
        photo_label = ctk.CTkLabel(
            photo_frame,
            text="Photo Capture:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        photo_label.pack(pady=(10, 5), anchor="w")
        
        # Instructions
        instructions_label = ctk.CTkLabel(
            photo_frame,
            text="Instructions: Camera will open. Position your face in the frame and press SPACE to capture, ESC to cancel.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        )
        instructions_label.pack(pady=(0, 10), anchor="w")
        
        # Photo display area using CTkImage
        self.photo_display = ctk.CTkLabel(
            photo_frame,
            text="📷\n\nNo photo captured\nClick button below to capture photo",
            font=ctk.CTkFont(size=14),
            height=200,
            width=300,
            fg_color="gray30",
            corner_radius=10
        )
        self.photo_display.pack(pady=10)
        
        # Capture button with fixed width
        self.capture_btn = ctk.CTkButton(
            photo_frame,
            text="📷 Capture Photo",
            font=ctk.CTkFont(size=14),
            height=45,
            width=200,
            command=self.capture_photo
        )
        self.capture_btn.pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            photo_frame,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        self.status_label.pack(pady=5)
        
        # Submit button section - IN THE SCROLLABLE AREA
        submit_frame = ctk.CTkFrame(form_scroll)
        submit_frame.pack(pady=20, fill="x")
        
        # Submit button
        self.submit_btn = ctk.CTkButton(
            submit_frame,
            text="Submit Registration",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=250,
            command=self.submit_registration,
            state="disabled"  # Initially disabled
        )
        self.submit_btn.pack(pady=15)
        
        # Submit status
        self.submit_status = ctk.CTkLabel(
            submit_frame,
            text="Please capture your photo first",
            font=ctk.CTkFont(size=12),
            text_color="orange"
        )
        self.submit_status.pack(pady=5)
        
        # Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Elections",
            command=lambda: self.parent.show_frame("VoterMenu")
        )
        back_btn.pack(pady=20)
    
    def on_show(self):
        """Update display when frame is shown"""
        election = self.parent.user_data.get("selected_election", {})
        if election:
            self.election_label.configure(text=f"Registering for: {election.get('name', 'Unknown Election')}")
    
    def capture_photo(self):
        """Capture face using updated face_verify.py logic (OpenCV live detection, rectangle drawing, and encoding)."""
        try:
            self.status_label.configure(text="📹 Opening camera. Position your face in the frame and press SPACE to capture, ESC to cancel", text_color="blue")
            messagebox.showinfo(
                "Camera Instructions",
                "Camera will open in a new window.\n\n"
                "Instructions:\n"
                "• Position your face clearly in the frame\n"
                "• Wait for green rectangle around your face\n"
                "• Press SPACE key to start capture\n"
                "• BLINK NATURALLY for liveness detection (2 seconds)\n"
                "• Photo will be captured after liveness check passes\n"
                "• Press ESC key to cancel\n\n"
                "Click OK to continue..."
            )
            # Use the updated face_verify.py capture_face_photo()
            result, error = capture_face_photo()
            if result:
                self.parent.user_data["face_data"] = result["face_data"]
                self.parent.user_data["face_encoding"] = result["face_encoding"]
                # Display the captured photo
                img_data = base64.b64decode(result["face_data"])
                pil_image = Image.open(io.BytesIO(img_data))
                display_size = (250, 188)
                pil_image = pil_image.resize(display_size, Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=display_size)
                self.photo_display.configure(image=ctk_image, text="")
                self.status_label.configure(text="✅ Photo captured successfully! Face encoding extracted.", text_color="green")
                self.capture_btn.configure(text="📷 Recapture Photo")
                self.submit_btn.configure(state="normal")
            else:
                self.status_label.configure(text=f"❌ {error}", text_color="red")
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {str(e)}")
            self.status_label.configure(text=f"❌ Camera error: {str(e)}", text_color="red")
    
    def submit_registration(self):
        """Submit registration to server"""
        name = self.name_entry.get().strip()
        election = self.parent.user_data.get("selected_election", {})
        
        if not name:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        if not self.parent.user_data.get("face_data"):
            messagebox.showerror("Error", "Please capture your photo first")
            return
        
        try:
            self.submit_btn.configure(state="disabled", text="Submitting...")
            
            # Prepare registration data for MVP Architecture
            face_encoding = self.parent.user_data.get("face_encoding")
            # Send to server using API client with name
            result, error = api_client.enroll_voter(face_encoding, name)
            
            if result:
                voter_id = result.get("voter_id")
                
                # Store registration info
                if "registrations" not in self.parent.user_data:
                    self.parent.user_data["registrations"] = {}
                
                reg_key = f"{election.get('election_id')}_{voter_id}"
                self.parent.user_data["registrations"][reg_key] = {
                    "status": result.get("status", "pending"),
                    "voter_id": voter_id,
                    "name": name,
                    "timestamp": time.time()
                }
                
                self.parent.user_data["voter_id"] = voter_id
                self.parent.user_data["name"] = name
                
                messagebox.showinfo(
                    "Registration Submitted", 
                    f"Registration submitted successfully!\n\nYour Voter ID: {voter_id}\n\nWaiting for approval..."
                )
                    # Do NOT auto-approve here; approval must be performed by an admin.
                    # The client will show "Pending Approval" until the server reports status 'active'.
                # Clear form and go back
                self.clear_form()
                self.parent.show_frame("VoterMenu")
            else:
                messagebox.showerror("Registration Failed", error)
                self.submit_btn.configure(state="normal", text="Submit Registration")
                
        except Exception as e:
            messagebox.showerror("Error", f"Registration error: {str(e)}")
            self.submit_btn.configure(state="normal", text="Submit Registration")
    
    def auto_approve(self, reg_key):
        """Deprecated demo auto-approve. Approval is now done by admin via server."""
        # This function previously simulated admin approval; it's intentionally left as a no-op.
        return
    
    def clear_form(self):
        """Clear the registration form"""
        self.name_entry.delete(0, 'end')
        self.parent.user_data["face_data"] = None
        self.parent.user_data["face_encoding"] = None
        self.captured_frame = None
        self.face_encoding = None
        self.photo_display.configure(
            image=None,
            text="📷\n\nNo photo captured\nClick button below to capture photo"
        )
        self.capture_btn.configure(text="📷 Capture Photo")
        self.submit_btn.configure(state="disabled", text="Submit Registration")
        self.submit_status.configure(text="Please capture your photo first", text_color="orange")
        self.status_label.configure(text="")

class FaceVerificationFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.verification_attempts = 0
        self.max_attempts = 3
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=20, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Face Verification",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        self.election_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.election_label.pack()
        
        # Verification form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Voter ID input (pre-fill if available)
        id_label = ctk.CTkLabel(
            form_frame,
            text="Voter ID:",
            font=ctk.CTkFont(size=14)
        )
        id_label.pack(pady=(20, 5), anchor="w")
        
        self.voter_id_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your Voter ID (or use saved ID)",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.voter_id_entry.pack(pady=(0, 10), fill="x")
        
        # Use saved ID button
        self.use_saved_btn = ctk.CTkButton(
            form_frame,
            text="Use My Saved ID",
            font=ctk.CTkFont(size=12),
            height=30,
            command=self.use_saved_id,
            state="disabled"
        )
        self.use_saved_btn.pack(pady=(0, 20))
        
        # Face verification
        verify_label = ctk.CTkLabel(
            form_frame,
            text="Face Verification:",
            font=ctk.CTkFont(size=14)
        )
        verify_label.pack(pady=(10, 5), anchor="w")
        
        # Instructions
        instructions = ctk.CTkLabel(
            form_frame,
            text="Position your face in the camera and press SPACE to capture for verification",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=400
        )
        instructions.pack(pady=(0, 10), anchor="w")
        
        self.verify_btn = ctk.CTkButton(
            form_frame,
            text="📷 Verify Face",
            font=ctk.CTkFont(size=14),
            height=40,
            command=self.verify_face
        )
        self.verify_btn.pack(pady=(0, 10), fill="x")
        
        self.verify_status = ctk.CTkLabel(
            form_frame,
            text="Enter Voter ID and verify your face to proceed",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.verify_status.pack(pady=(0, 20))
        
        # Proceed button
        self.proceed_btn = ctk.CTkButton(
            form_frame,
            text="Proceed to Vote",
            font=ctk.CTkFont(size=16),
            height=50,
            command=self.proceed_to_vote,
            state="disabled"
        )
        self.proceed_btn.pack(pady=20, fill="x")
        
        # Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Elections",
            command=lambda: self.parent.show_frame("VoterMenu")
        )
        back_btn.pack(pady=20)
    
    def on_show(self):
        """Update display when frame is shown"""
        # Reset verification attempts when frame is shown
        self.verification_attempts = 0
        self.verify_btn.configure(state="normal")
        self.proceed_btn.configure(state="disabled")
        
        election = self.parent.user_data.get("selected_election", {})
        if election:
            self.election_label.configure(text=f"Voting in: {election.get('name', 'Unknown Election')}")
        
        # Check if we have a saved voter ID
        saved_voter_id = self.parent.user_data.get("voter_id")
        if saved_voter_id:
            self.use_saved_btn.configure(state="normal")
            self.use_saved_btn.configure(text=f"Use Saved ID: {saved_voter_id}")
    
    def use_saved_id(self):
        """Use the saved voter ID"""
        saved_voter_id = self.parent.user_data.get("voter_id")
        if saved_voter_id:
            self.voter_id_entry.delete(0, 'end')
            self.voter_id_entry.insert(0, saved_voter_id)
    
    def verify_face(self):
        """Perform direct OpenCV verification with live detection, rectangle drawing, and camera capture loop."""
        voter_id = self.voter_id_entry.get().strip()
        if not voter_id:
            messagebox.showerror("Error", "Please enter your Voter ID")
            return
        self.verify_status.configure(text="Opening camera for verification...", text_color="blue")
        try:
            messagebox.showinfo("Camera", "Camera will open. Position your face and press SPACE to verify, ESC to cancel")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                self.verify_status.configure(text="❌ Camera error", text_color="red")
                return
            captured_frame = None
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                face_locations = detect_faces(frame)
                display_frame = draw_face_rectangles(frame, face_locations)
                cv2.imshow("Face Verification - Press SPACE to verify, ESC to cancel", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):
                    if len(face_locations) == 1:
                        captured_frame = frame.copy()
                        break
                    elif len(face_locations) == 0:
                        self.verify_status.configure(text="❌ No face detected. Please position your face in camera.", text_color="red")
                    else:
                        self.verify_status.configure(text="❌ Multiple faces detected. Please ensure only one person.", text_color="red")
                elif key == 27:
                    break
            cap.release()
            cv2.destroyAllWindows()
            if captured_frame is None:
                self.verify_status.configure(text="Verification cancelled", text_color="gray")
                return
            # Extract face encoding from captured frame
            encoding = capture_face_encoding(captured_frame)
            if encoding is None:
                self.verify_status.configure(text="❌ Could not extract face encoding.", text_color="red")
                return
            # Send verification request to server using API client
            election_id = self.parent.user_data.get("selected_election", {}).get("election_id")
            # Pass voter_id, election_id, and encoding as BallotGuardAPI.verify_face expects 3 args
            result, error = api_client.verify_face(voter_id, election_id, encoding)
            if result:
                if result.get("pass"):
                    self.verify_status.configure(text="✅ Face verified successfully! You can proceed to vote.", text_color="green")
                    self.proceed_btn.configure(state="normal")
                    self.parent.user_data["verified_voter_id"] = voter_id
                    self.parent.user_data["voter_id"] = voter_id
                    # Reset attempts on success
                    self.verification_attempts = 0
                else:
                    # Increment failed attempts
                    self.verification_attempts += 1
                    remaining_attempts = self.max_attempts - self.verification_attempts
                    
                    if self.verification_attempts >= self.max_attempts:
                        self.verify_status.configure(
                            text="❌ Face verification failed. Maximum attempts reached. Please contact support.", 
                            text_color="red"
                        )
                        self.verify_btn.configure(state="disabled")
                        messagebox.showerror(
                            "Verification Failed", 
                            "You have exceeded the maximum number of face verification attempts (3).\n\n"
                            "Please contact election support for assistance."
                        )
                    else:
                        self.verify_status.configure(
                            text=f"❌ Face verification failed. {remaining_attempts} attempt(s) remaining.", 
                            text_color="red"
                        )
                        messagebox.showwarning(
                            "Verification Failed",
                            f"Face verification failed.\n\nYou have {remaining_attempts} attempt(s) remaining."
                        )
            else:
                # Increment failed attempts for errors too
                self.verification_attempts += 1
                remaining_attempts = self.max_attempts - self.verification_attempts
                
                if self.verification_attempts >= self.max_attempts:
                    self.verify_status.configure(
                        text="❌ Maximum verification attempts reached. Please contact support.", 
                        text_color="red"
                    )
                    self.verify_btn.configure(state="disabled")
                    messagebox.showerror(
                        "Verification Failed", 
                        f"Maximum attempts reached.\n\nError: {error}\n\n"
                        "Please contact election support for assistance."
                    )
                else:
                    self.verify_status.configure(
                        text=f"❌ {error} - {remaining_attempts} attempt(s) remaining.", 
                        text_color="red"
                    )
        except Exception as e:
            # Increment failed attempts for exceptions
            self.verification_attempts += 1
            remaining_attempts = self.max_attempts - self.verification_attempts
            
            if self.verification_attempts >= self.max_attempts:
                self.verify_status.configure(
                    text="❌ Maximum verification attempts reached. Please contact support.", 
                    text_color="red"
                )
                self.verify_btn.configure(state="disabled")
                messagebox.showerror(
                    "Error", 
                    f"Verification error: {str(e)}\n\n"
                    "Maximum attempts reached. Please contact election support."
                )
            else:
                messagebox.showerror("Error", f"Verification error: {str(e)}\n\n{remaining_attempts} attempt(s) remaining.")
                self.verify_status.configure(
                    text=f"❌ Error: {str(e)} - {remaining_attempts} attempt(s) remaining.", 
                    text_color="red"
                )
    
    def proceed_to_vote(self):
        """Issue OVT and proceed to voting interface"""
        try:
            voter_id = self.parent.user_data.get("verified_voter_id")
            election_id = self.parent.user_data.get("selected_election", {}).get("election_id")
            
            if not voter_id or not election_id:
                messagebox.showerror("Error", "Missing voter or election information")
                return
            
            # Issue OVT token using API client
            result, error = api_client.issue_ovt(voter_id, election_id)
            
            if result:
                self.parent.user_data["ovt"] = result.get("ovt")
                self.parent.user_data["server_sig"] = result.get("server_sig")
                self.parent.show_frame("VotingInterface")
            else:
                messagebox.showerror("Error", error)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to issue voting token: {str(e)}")

class VotingInterfaceFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=20, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Cast Your Vote",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Election info
        self.election_info = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.election_info.pack()
        
        # Main scrollable container
        main_container = ctk.CTkScrollableFrame(self)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Voting form inside scrollable container
        voting_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        voting_frame.pack(fill="both", expand=True)
        
        candidates_label = ctk.CTkLabel(
            voting_frame,
            text="Select a candidate:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        candidates_label.pack(pady=20)
        
        # Candidates frame with better spacing
        self.candidates_frame = ctk.CTkFrame(voting_frame, fg_color="transparent")
        self.candidates_frame.pack(pady=10, fill="both", expand=True)
        
        # Bottom buttons container (outside scrollable area)
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.pack(side="bottom", fill="x", pady=20, padx=20)
        
        # Submit vote button
        self.vote_btn = ctk.CTkButton(
            button_container,
            text="Submit Vote",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.submit_vote,
            state="disabled"
        )
        self.vote_btn.pack(pady=(0, 10), fill="x")
        
        # Back button
        back_btn = ctk.CTkButton(
            button_container,
            text="← Back to Verification",
            command=lambda: self.parent.show_frame("FaceVerification")
        )
        back_btn.pack(fill="x")
        
        self.selected_candidate = None
    
    def on_show(self):
        """Update voting interface when shown"""
        election = self.parent.user_data.get("selected_election", {})
        if election:
            self.election_info.configure(text=f"Election: {election.get('name', 'Unknown')}")
            self.load_candidates(election)
    
    def load_candidates(self, election):
        """Load candidates for the election"""
        # Clear existing candidates
        for widget in self.candidates_frame.winfo_children():
            widget.destroy()
        
        candidates = election.get("candidates", [])
        if not candidates:
            no_candidates_label = ctk.CTkLabel(
                self.candidates_frame,
                text="No candidates available",
                font=ctk.CTkFont(size=14)
            )
            no_candidates_label.pack(pady=20)
            return
        
        # Create radio button variable
        self.candidate_var = tk.StringVar()
        self.candidate_id_map = {}  # index -> candidate_id
        # Create candidate options with index as value
        for idx, candidate in enumerate(candidates):
            candidate_frame = ctk.CTkFrame(self.candidates_frame)
            candidate_frame.pack(pady=5, padx=10, fill="x")
            self.candidate_id_map[str(idx)] = candidate.get('candidate_id', '')
            # Create candidate card with more details
            candidate_card = ctk.CTkFrame(candidate_frame)
            candidate_card.pack(pady=5, padx=10, fill="x")

            # Updated party symbols with Indian political parties
            party_symbols = {
                "BJP": "🌸",         # Lotus
                "INC": "✋",         # Hand
                "AAP": "🧹",         # Broom
                "CPI": "🌾",         # Ears of Corn
                "TMC": "🌿",         # Grass flower and leaves
                "Independent": "⭐",  # Star
                "": "🗳️"            # Default ballot box
            }

            # Get party and its symbol from candidate data
            party = candidate.get('party', 'Independent')
            # Look up symbol from party_symbols dictionary
            symbol = party_symbols.get(party, party_symbols.get('', '🗳️'))

            # Create grid layout for better alignment
            layout_frame = ctk.CTkFrame(candidate_card)
            layout_frame.pack(pady=10, padx=10, fill="x")
            layout_frame.grid_columnconfigure(2, weight=1)  # Make name column expandable

            # Party symbol on the left - centered vertically and horizontally
            symbol_frame = ctk.CTkFrame(layout_frame, fg_color="transparent", width=60, height=60)
            symbol_frame.grid(row=0, column=0, padx=(10, 15))
            symbol_frame.grid_propagate(False)  # Force fixed size
            
            symbol_label = ctk.CTkLabel(
                symbol_frame,
                text=symbol,
                font=ctk.CTkFont(size=32),
                width=60,
                height=60
            )
            symbol_label.place(relx=0.5, rely=0.5, anchor="center")  # Center in frame

            # Radio button - centered
            radio_btn = ctk.CTkRadioButton(
                layout_frame,
                text="",
                variable=self.candidate_var,
                value=str(idx),
                command=self.on_candidate_selected
            )
            radio_btn.grid(row=0, column=1, padx=(0, 15))

            # Candidate details frame
            details_frame = ctk.CTkFrame(layout_frame, fg_color="transparent")
            details_frame.grid(row=0, column=2, sticky="ew")

            # Candidate name
            name_label = ctk.CTkLabel(
                details_frame,
                text=candidate.get('name', 'Unknown'),
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w"
            )
            name_label.pack(fill="x")

            # Party name
            party_label = ctk.CTkLabel(
                details_frame,
                text=party,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                anchor="w"
            )
            party_label.pack(fill="x")

            # Optional: Add candidate info/platform
            if candidate.get('info'):
                info_label = ctk.CTkLabel(
                    candidate_card,
                    text=candidate.get('info', ''),
                    font=ctk.CTkFont(size=12),
                    justify="left",
                    wraplength=400
                )
                info_label.pack(pady=(0, 10), padx=40, anchor="w")
    
    def on_candidate_selected(self):
        """Enable vote button when candidate is selected"""
        self.selected_candidate_index = self.candidate_var.get()
        self.vote_btn.configure(state="normal")
    
    def submit_vote(self):
        """Submit the vote to server with Paillier encryption, server receipt, and RSA signature verification."""
        # Must allow index 0, so check for attribute existence and None/empty explicitly
        if not hasattr(self, 'selected_candidate_index') or self.selected_candidate_index in (None, ""):
            messagebox.showerror("Error", "Please select a candidate")
            return
        election = self.parent.user_data.get("selected_election", {})
        candidates = election.get("candidates", [])
        idx = int(self.selected_candidate_index)
        candidate_id = self.candidate_id_map[self.selected_candidate_index]
        candidate_name = candidates[idx].get("name", "Unknown")
        confirm = messagebox.askyesno(
            "Confirm Vote",
            f"Are you sure you want to vote for:\n\n{candidate_name}\n\nIn: {election.get('name', 'this election')}\n\nThis action cannot be undone."
        )
        if confirm:
            try:
                self.vote_btn.configure(state="disabled", text="Submitting Vote...")
                vote_id = generate_vote_id()
                election_id = election.get("election_id")
                ovt = self.parent.user_data.get("ovt", {})
                # --- Paillier vote encryption ---
                from client_app.crypto.paillier import paillier_encrypt
                from client_app.client_config import PAILLIER_N
                from phe import paillier
                paillier_pubkey = paillier.PaillierPublicKey(PAILLIER_N)
                # Encrypt a single vote (value 1), not the candidate index
                encrypted_vote_obj = paillier_encrypt(paillier_pubkey, 1)
                # Serialize EncryptedNumber for JSON
                encrypted_vote = {
                    "ciphertext": str(encrypted_vote_obj.ciphertext()),
                    "exponent": encrypted_vote_obj.exponent,
                }
                # --- Prepare vote data ---
                vote_data = {
                    "vote_id": vote_id,
                    "election_id": election_id,
                    "candidate_id": candidate_id,
                    "encrypted_vote": encrypted_vote,
                    "ovt": ovt,
                }
                # --- Send to server ---
                result, error = api_client.cast_vote(vote_data)
                if result:
                    # --- Server receipt and RSA signature verification ---
                    from client_app.crypto.signing import verify_rsa_signature
                    from client_app.client_config import RSA_PUB_PEM
                    import base64
                    server_sig = result.get("server_sig")
                    receipt = result.get("receipt")
                    
                    # Debug receipt data
                    print("Receipt:", receipt)
                    
                    # Verify receipt has required fields
                    required_fields = ["vote_id", "election_id", "ledger_index", "block_hash", "sig"]
                    if not all(field in receipt for field in required_fields):
                        messagebox.showerror("Vote Failed", "Invalid receipt format from server")
                        self.vote_btn.configure(state="normal", text="Submit Vote")
                        return
                        
                    # Only verify the canonical payload fields
                    payload = {
                        "vote_id": receipt["vote_id"],
                        "election_id": receipt["election_id"],
                        "ledger_index": receipt["ledger_index"],
                        "block_hash": receipt["block_hash"]
                    }
                    
                    try:
                        rsa_pub_pem_b64 = base64.b64encode(RSA_PUB_PEM.encode()).decode()
                        if not verify_rsa_signature(payload, receipt["sig"], rsa_pub_pem_b64):
                            messagebox.showerror("Vote Failed", "Server signature verification failed!")
                            self.vote_btn.configure(state="normal", text="Submit Vote")
                            return
                    except Exception as e:
                        messagebox.showerror("Vote Failed", f"Signature verification error: {str(e)}")
                        self.vote_btn.configure(state="normal", text="Submit Vote")
                        return
                        
                    ledger_index = result.get("ledger_index")
                    block_hash = result.get("block_hash")
                    
                    # Store receipt locally for voter verification
                    try:
                        store_receipt(
                            vote_id=receipt["vote_id"],
                            election_id=receipt["election_id"],
                            idx=receipt["ledger_index"],
                            bhash=receipt["block_hash"],
                            sig_b64=receipt["sig"]
                        )
                        print(f"[CLIENT] ✓ Receipt stored locally: vote_id={vote_id}, ledger_index={ledger_index}")
                    except Exception as e:
                        print(f"[CLIENT] ⚠ Warning: Could not store receipt locally: {e}")
                    
                    voter_id = self.parent.user_data.get("verified_voter_id")
                    if voter_id and election_id:
                        voted_key = f"{election_id}_{voter_id}"
                        self.parent.user_data["voted_elections"].add(voted_key)
                    messagebox.showinfo(
                        "Vote Submitted Successfully",
                        f"Your vote has been recorded!\n\nVote ID: {vote_id}\nCandidate: {candidate_name}\nLedger Index: {ledger_index}\nBlock Hash: {block_hash[:16]}...\n\nReceipt saved for verification.\n\nThank you for participating in the democratic process."
                    )
                    self.parent.user_data["verified_voter_id"] = None
                    self.parent.user_data["selected_election"] = None
                    self.parent.user_data["ovt"] = None
                    self.parent.show_frame("MainMenu")
                else:
                    messagebox.showerror("Vote Failed", error)
                    self.vote_btn.configure(state="normal", text="Submit Vote")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to submit vote: {str(e)}")
                self.vote_btn.configure(state="normal", text="Submit Vote")

# Placeholder frames for Admin and Auditor
class AdminMenuFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Top Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(pady=20, padx=20, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Admin Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)

        # Stats section
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        self.total_votes_label = ctk.CTkLabel(
            stats_frame,
            text="Total Votes: Loading...",
            font=ctk.CTkFont(size=16)
        )
        self.total_votes_label.pack(pady=5)
        
        self.active_elections_label = ctk.CTkLabel(
            stats_frame,
            text="Active Elections: Loading...",
            font=ctk.CTkFont(size=16)
        )
        self.active_elections_label.pack(pady=5)

        # Elections List
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        list_label = ctk.CTkLabel(
            list_frame,
            text="Current Elections",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        list_label.pack(pady=10)
        
        # Scrollable elections list
        self.elections_frame = ctk.CTkScrollableFrame(list_frame, height=300)
        self.elections_frame.pack(pady=10, fill="both", expand=True)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            self,
            text="🔄 Refresh Dashboard",
            command=self.refresh_dashboard
        )
        refresh_btn.pack(pady=10)
        
        # Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Main Menu",
            command=lambda: self.parent.show_frame("MainMenu")
        )
        back_btn.pack(pady=10)

        # Initial load
        self.refresh_dashboard()
    
    def refresh_dashboard(self):
        """Refresh the admin dashboard data"""
        try:
            # Clear existing election widgets
            for widget in self.elections_frame.winfo_children():
                widget.destroy()
            
            # Fetch elections from server
            elections, error = api_client.get_elections()
            if error:
                messagebox.showerror("Error", f"Failed to load elections: {error}")
                return
            
            # Update stats
            active_elections = sum(1 for e in elections if e.get("status") == "open")
            self.active_elections_label.configure(text=f"Active Elections: {active_elections}")

            # Get vote counts from server (this would be a separate API call in production)
            total_votes = 0  # In real system, get from server

            self.total_votes_label.configure(text=f"Total Votes: {total_votes}")
            
            # Display elections
            for election in elections:
                election_frame = ctk.CTkFrame(self.elections_frame)
                election_frame.pack(pady=5, padx=5, fill="x")
                
                name_label = ctk.CTkLabel(
                    election_frame,
                    text=election.get("name", "Unknown Election"),
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                name_label.pack(pady=5, anchor="w", padx=10)
                
                status_label = ctk.CTkLabel(
                    election_frame,
                    text=f"Status: {election.get('status', 'Unknown')}",
                    font=ctk.CTkFont(size=12)
                )
                status_label.pack(pady=2, anchor="w", padx=10)
                
                dates_label = ctk.CTkLabel(
                    election_frame,
                    text=f"Dates: {election.get('start_date', 'TBD')} to {election.get('end_date', 'TBD')}",
                    font=ctk.CTkFont(size=12)
                )
                dates_label.pack(pady=2, anchor="w", padx=10)
                
                # Action buttons based on status
                button_frame = ctk.CTkFrame(election_frame)
                button_frame.pack(pady=5, padx=10, fill="x")
                
                if election.get("status") == "open":
                    close_btn = ctk.CTkButton(
                        button_frame,
                        text="Close Election",
                        width=100,
                        height=30,
                        font=ctk.CTkFont(size=12),
                        command=lambda e=election: self.close_election(e)
                    )
                    close_btn.pack(side="left", padx=5)
                    
                elif election.get("status") == "draft":
                    open_btn = ctk.CTkButton(
                        button_frame,
                        text="Open Election",
                        width=100,
                        height=30,
                        font=ctk.CTkFont(size=12),
                        command=lambda e=election: self.open_election(e)
                    )
                    open_btn.pack(side="left", padx=5)
                
                elif election.get("status") == "closed":
                    tally_btn = ctk.CTkButton(
                        button_frame,
                        text="View Results",
                        width=100,
                        height=30,
                        font=ctk.CTkFont(size=12),
                        command=lambda e=election: self.view_results(e)
                    )
                    tally_btn.pack(side="left", padx=5)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh dashboard: {str(e)}")
    
    def close_election(self, election):
        """Close an open election"""
        try:
            result, error = api_client.update_election_status(election["election_id"], "close")
            if error:
                messagebox.showerror("Error", f"Failed to close election: {error}")
            else:
                messagebox.showinfo("Success", "Election closed successfully")
                self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close election: {str(e)}")
    
    def open_election(self, election):
        """Open a draft election"""
        try:
            result, error = api_client.update_election_status(election["election_id"], "open")
            if error:
                messagebox.showerror("Error", f"Failed to open election: {error}")
            else:
                messagebox.showinfo("Success", "Election opened successfully")
                self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open election: {str(e)}")
    
    def view_results(self, election):
        """View results for a closed election"""
        try:
            result, error = api_client.get_election_results(election["election_id"])
            if error:
                messagebox.showerror("Error", f"Failed to get results: {error}")
            else:
                # Simple results display for now
                results_str = f"Results for {election['name']}:\n\n"
                for candidate, votes in result.get("results", {}).items():
                    results_str += f"{candidate}: {votes} votes\n"
                messagebox.showinfo("Election Results", results_str)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view results: {str(e)}")
    
    def on_show(self):
        """Refresh dashboard when frame is shown"""
        self.refresh_dashboard()

class AuditorMenuFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        title_label = ctk.CTkLabel(
            self,
            text="Auditor Portal",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=50)
        
        info_label = ctk.CTkLabel(
            self,
            text="Auditor functionality coming soon...",
            font=ctk.CTkFont(size=16)
        )
        info_label.pack(pady=20)
        
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Main Menu",
            command=lambda: self.parent.show_frame("MainMenu")
        )
        back_btn.pack(pady=20)

def main():
    """Main application entry point"""
    app = BallotGuardApp()
    app.mainloop()

if __name__ == "__main__":
    main()

# Backwards-compatible alias: some launchers/importers expect `run_ui()`.
def run_ui():
    """Alias for launching the UI programmatically.

    Use this if another module imports `run_ui` (older code). It simply
    forwards to `main()`.
    """
    return main()
