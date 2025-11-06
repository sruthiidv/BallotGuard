from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
# Add the client_app directory to the Python path so package imports work when running this file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from client_app.storage.localdb import init

# Import client_app modules
from auth.face_verify import capture_face_photo, detect_faces, draw_face_rectangles, capture_face_encoding
from auth.encode import bgr_to_jpeg_base64
from crypto.vote_crypto import prepare_vote_data, generate_vote_id, verify_vote_receipt
from api_client import BallotGuardAPI
from config import SERVER_BASE

# Initialize API client
api_client = BallotGuardAPI()

class BallotGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("BallotGuard - Digital Voting System")
        self.geometry("800x600")
        self.resizable(False, False)
        
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
        self.create_widgets()
    
    def create_widgets(self):
        # Make the main menu scrollable
        scrollable = ctk.CTkScrollableFrame(self, width=760, height=560)
        scrollable.pack(expand=True, fill="both", padx=20, pady=20)

        # Centered container for all content
        container = ctk.CTkFrame(scrollable)
        container.pack(expand=True)

        # Title with icon placeholder, centered
        title_frame = ctk.CTkFrame(container)
        title_frame.pack(pady=40, padx=40)

        # App icon placeholder (centered)
        icon_label = ctk.CTkLabel(
            title_frame,
            text="🗳️",
            font=ctk.CTkFont(size=60)
        )
        icon_label.pack(pady=10)

        # App title (centered)
        title_label = ctk.CTkLabel(
            title_frame,
            text="BallotGuard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=10)

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Secure Digital Voting System",
            font=ctk.CTkFont(size=16)
        )
        subtitle_label.pack()

        # Role selection
        role_frame = ctk.CTkFrame(container)
        role_frame.pack(pady=40, padx=40)

        role_title = ctk.CTkLabel(
            role_frame,
            text="Select Your Role",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        role_title.pack(pady=20)

        # Centered button frame
        button_frame = ctk.CTkFrame(role_frame)
        button_frame.pack(pady=10, padx=10)
        button_width = 320
        button_height = 56

        # All buttons same width/height, centered
        voter_btn = ctk.CTkButton(
            button_frame,
            text="👤 Voter",
            font=ctk.CTkFont(size=16),
            width=button_width,
            height=button_height,
            command=self.select_voter_role
        )
        voter_btn.pack(pady=8)

        admin_btn = ctk.CTkButton(
            button_frame,
            text="👨‍💼 Admin",
            font=ctk.CTkFont(size=16),
            width=button_width,
            height=button_height,
            command=self.select_admin_role
        )
        admin_btn.pack(pady=8)

        auditor_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Auditor",
            font=ctk.CTkFont(size=16),
            width=button_width,
            height=button_height,
            command=self.select_auditor_role
        )
        auditor_btn.pack(pady=8)
    
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
        self.create_widgets()
    
    def create_widgets(self):
        # Top Go Back button
        top_back_btn = ctk.CTkButton(
            self,
            text="← Go Back to Menu",
            command=lambda: self.parent.show_frame("MainMenu")
        )
        top_back_btn.pack(pady=(20, 0), anchor="w", padx=20)

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

        # Bottom Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Main Menu",
            command=lambda: self.parent.show_frame("MainMenu")
        )
        back_btn.pack(pady=20)
    
    def on_show(self):
        """Load elections when frame is shown"""
        self.load_elections()
    
    def to_dict(self):
        vote_count = Vote.query.filter_by(candidate_id=self.id).count()
        total_votes = Vote.query.filter_by(election_id=self.election_id).count()
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        
        return {
            'id': self.id,
            'name': self.name,
            'party': self.party,
            'description': self.description,
            'election_id': self.election_id,
            'votes': vote_count,
            'percentage': round(percentage, 2)
        }

class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(64))
    
    __table_args__ = (db.UniqueConstraint('voter_id', 'election_id', name='unique_voter_election'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'voter_id': self.voter_id,
            'candidate_id': self.candidate_id,
            'election_id': self.election_id,
            'timestamp': self.timestamp.isoformat(),
            'blockchain_hash': self.blockchain_hash
        }

class Voter(db.Model):
    __tablename__ = 'voters'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    vote_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'voter_id': self.voter_id,
            'name': self.name,
            'email': self.email,
            'has_voted': self.has_voted,
            'vote_timestamp': self.vote_timestamp.isoformat() if self.vote_timestamp else None,
            'created_at': self.created_at.isoformat()
        }

class BlockchainRecord(db.Model):
    __tablename__ = 'blockchain_records'
    
    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, nullable=False)
    block_hash = db.Column(db.String(64), nullable=False)
    previous_hash = db.Column(db.String(64))
    vote_hash = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'block_index': self.block_index,
            'block_hash': self.block_hash,
            'previous_hash': self.previous_hash,
            'vote_hash': self.vote_hash,
            'timestamp': self.timestamp.isoformat()
        }

def create_sample_data():
    """Create sample election data"""
    try:
        print("🔄 Creating sample data...")
        
        # Create sample election
        election = Election(
            title="Student Council Election 2024",
            description="Annual student council election",
            start_date=datetime.now(),
            end_date=datetime.now(),
            status="active",
            eligible_voters=1000
        )
        db.session.add(election)
        db.session.flush()
        
        print(f"📊 Created election: {election.title} (ID: {election.id})")
        
        # Create candidates
        candidates_data = [
            {"name": "Alice Johnson", "party": "Progressive Party"},
            {"name": "Bob Smith", "party": "Conservative Party"},
            {"name": "Carol Davis", "party": "Independent"}
        ]
        
        candidates = []
        for cand_data in candidates_data:
            candidate = Candidate(
                name=cand_data["name"],
                party=cand_data["party"],
                election_id=election.id
            )
            candidates.append(candidate)
            db.session.add(candidate)
        
        db.session.flush()
        print(f"👥 Created {len(candidates)} candidates")
        
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
        """Capture photo using auth module"""
        try:
            self.status_label.configure(text="📹 Opening camera. Position your face in the frame and press SPACE to capture, ESC to cancel", text_color="blue")
            
            # Show instructions popup
            messagebox.showinfo("Camera Instructions", 
                              "Camera will open in a new window.\n\n" +
                              "Instructions:\n" +
                              "• Position your face clearly in the frame\n" +
                              "• Wait for green rectangle around your face\n" +
                              "• Press SPACE key to capture photo\n" +
                              "• Press ESC key to cancel\n\n" +
                              "Click OK to continue...")
            
            # Use the auth module for face capture
            result, error = capture_face_photo()
            
            if result:
                self.parent.user_data["face_data"] = result["face_data"]
                self.parent.user_data["face_encoding"] = result["face_encoding"]
                
                # Convert base64 back to display in UI
                img_data = base64.b64decode(result["face_data"])
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Resize for display
                display_size = (250, 188)
                pil_image = pil_image.resize(display_size, Image.Resampling.LANCZOS)
                
                # Create CTkImage for proper scaling
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=display_size)
                
                self.photo_display.configure(
                    image=ctk_image,
                    text=""
                )
                
                self.status_label.configure(text="✅ Photo captured successfully! Face encoding extracted.", text_color="green")
                self.capture_btn.configure(text="📷 Recapture Photo")  # Allow user to recapture
                self.submit_btn.configure(state="normal")
            
            else:
                election_count = Election.query.count()
                vote_count = Vote.query.count()
                voter_count = Voter.query.count()
                print(f"📊 Database already contains:")
                print(f"   • {election_count} elections")
                print(f"   • {vote_count} votes") 
                print(f"   • {voter_count} voters")
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
            face_template = self.parent.user_data.get("face_encoding")
            
            # Send to server using API client
            result, error = api_client.enroll_voter(face_template)
            
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
                
                # Auto-approve after 3 seconds (for demo)
                self.parent.after(3000, lambda: self.auto_approve(reg_key))
                
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
        """Auto-approve registration after delay"""
        if reg_key in self.parent.user_data.get("registrations", {}):
            self.parent.user_data["registrations"][reg_key]["status"] = "approved"
            messagebox.showinfo("Approved", "Your registration has been approved! You can now vote.")
            
            # Refresh the voter menu to update button states
            if hasattr(self.parent.frames.get("VoterMenu"), 'load_elections'):
                self.parent.frames["VoterMenu"].load_elections()
    
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
        """Verify face against stored template"""
        voter_id = self.voter_id_entry.get().strip()
        
        if not voter_id:
            messagebox.showerror("Error", "Please enter your Voter ID")
            return
        
        self.verify_status.configure(text="Opening camera for verification...", text_color="blue")
        
        try:
            # Use auth module for face detection and capture
            messagebox.showinfo("Camera", "Camera will open. Position your face and press SPACE to verify, ESC to cancel")
            
            # For verification, we can use the simple camera capture from auth module
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
                
                # Use auth module functions for face detection
                face_locations = detect_faces(frame)
                display_frame = draw_face_rectangles(frame, face_locations)
                
                cv2.imshow("Face Verification - Press SPACE to verify, ESC to cancel", display_frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):  # Space to capture
                    if len(face_locations) == 1:
                        captured_frame = frame.copy()
                        break
                    elif len(face_locations) == 0:
                        self.verify_status.configure(text="❌ No face detected. Please position your face in camera.", text_color="red")
                    else:
                        self.verify_status.configure(text="❌ Multiple faces detected. Please ensure only one person.", text_color="red")
                elif key == 27:  # ESC to cancel
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if captured_frame is None:
                self.verify_status.configure(text="Verification cancelled", text_color="gray")
                return
            
            # Send verification request to server using API client
            election_id = self.parent.user_data.get("selected_election", {}).get("election_id")
            
            result, error = api_client.verify_face(voter_id, election_id)
            
            if result:
                if result.get("pass"):
                    self.verify_status.configure(text="✅ Face verified successfully! You can proceed to vote.", text_color="green")
                    self.proceed_btn.configure(state="normal")
                    self.parent.user_data["verified_voter_id"] = voter_id
                    
                    # Save voter ID for future use
                    self.parent.user_data["voter_id"] = voter_id
                else:
                    self.verify_status.configure(text="❌ Face verification failed", text_color="red")
            else:
                self.verify_status.configure(text=f"❌ {error}", text_color="red")
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @api_bp.route('/elections/<int:election_id>', methods=['PATCH'])
    def update_election(election_id):
        """Update election"""
        try:
            election = Election.query.get_or_404(election_id)
            data = request.get_json()
            
            if 'status' in data:
                election.status = data['status']
            if 'title' in data:
                election.title = data['title']
            if 'description' in data:
                election.description = data['description']
            
            db.session.commit()
            return jsonify(election.to_dict())
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    @api_bp.route('/voters', methods=['GET'])
    def get_voters():
        """Get voters"""
        try:
            voters = Voter.query.all()
            return jsonify([voter.to_dict() for voter in voters])
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
        
        # Voting form
        voting_frame = ctk.CTkFrame(self)
        voting_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        candidates_label = ctk.CTkLabel(
            voting_frame,
            text="Select a candidate:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        candidates_label.pack(pady=20)
        
        # Candidate selection will be populated dynamically
        self.candidates_frame = ctk.CTkFrame(voting_frame)
        self.candidates_frame.pack(pady=10, fill="both", expand=True)
        
        # Submit vote button
        self.vote_btn = ctk.CTkButton(
            voting_frame,
            text="Submit Vote",
            font=ctk.CTkFont(size=16),
            height=50,
            command=self.submit_vote,
            state="disabled"
        )
        self.vote_btn.pack(pady=20, fill="x")
        
        # Back button
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Verification",
            command=lambda: self.parent.show_frame("FaceVerification")
        )
        back_btn.pack(pady=20)
        
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
        
        # Create candidate options
        for candidate in candidates:
            candidate_frame = ctk.CTkFrame(self.candidates_frame)
            candidate_frame.pack(pady=5, padx=10, fill="x")
            
            radio_btn = ctk.CTkRadioButton(
                candidate_frame,
                text=f"{candidate.get('name', 'Unknown')} ({candidate.get('party', 'Independent')})",
                variable=self.candidate_var,
                value=candidate.get('candidate_id', ''),
                command=self.on_candidate_selected
            )
            radio_btn.pack(pady=10, anchor="w")
    
    def on_candidate_selected(self):
        """Enable vote button when candidate is selected"""
        self.selected_candidate = self.candidate_var.get()
        self.vote_btn.configure(state="normal")
    
    def submit_vote(self):
        """Submit the vote to server"""
        if not self.selected_candidate:
            messagebox.showerror("Error", "Please select a candidate")
            return
        
        # Get candidate name for confirmation
        election = self.parent.user_data.get("selected_election", {})
        candidates = election.get("candidates", [])
        candidate_name = "Unknown"
        for candidate in candidates:
            if candidate.get("candidate_id") == self.selected_candidate:
                candidate_name = candidate.get("name", "Unknown")
                break
        
        # Confirm vote
        confirm = messagebox.askyesno(
            "Confirm Vote",
            f"Are you sure you want to vote for:\n\n{candidate_name}\n\nIn: {election.get('name', 'this election')}\n\nThis action cannot be undone."
        )
        
        if confirm:
            try:
                self.vote_btn.configure(state="disabled", text="Submitting Vote...")
                
                # Generate unique vote ID and prepare encrypted vote data using crypto module
                vote_id = generate_vote_id()
                election_id = election.get("election_id")
                ovt = self.parent.user_data.get("ovt", {})
                
                # Prepare vote data using crypto module
                vote_data = prepare_vote_data(
                    vote_id=vote_id,
                    election_id=election_id,
                    candidate_id=self.selected_candidate,
                    ovt=ovt
                )
                
                # Send to server using API client
                result, error = api_client.cast_vote(vote_data)
                
                if result:
                    ledger_index = result.get("ledger_index")
                    block_hash = result.get("block_hash")
                    
                    # Mark this election as voted
                    voter_id = self.parent.user_data.get("verified_voter_id")
                    if voter_id and election_id:
                        voted_key = f"{election_id}_{voter_id}"
                        self.parent.user_data["voted_elections"].add(voted_key)
                    
                    messagebox.showinfo(
                        "Vote Submitted Successfully",
                        f"Your vote has been recorded!\n\nVote ID: {vote_id}\nCandidate: {candidate_name}\nLedger Index: {ledger_index}\nBlock Hash: {block_hash[:16]}...\n\nThank you for participating in the democratic process."
                    )
                    
                    # Clear user data and return to main menu
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
        
        title_label = ctk.CTkLabel(
            self,
            text="Admin Portal",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=50)
        
        info_label = ctk.CTkLabel(
            self,
            text="Admin functionality coming soon...",
            font=ctk.CTkFont(size=16)
        )
        info_label.pack(pady=20)
        
        back_btn = ctk.CTkButton(
            self,
            text="← Back to Main Menu",
            command=lambda: self.parent.show_frame("MainMenu")
        )
        back_btn.pack(pady=20)

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
