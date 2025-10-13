import ttkbootstrap as ttkb
from components.dashboard import Dashboard
import sys
from tkinter import messagebox

def main():
    try:
        app = ttkb.Window(themename="darkly")
        app.title("BallotGuard Admin Panel - Demo Mode")
        app.geometry("1000x700")
        app.minsize(800, 600)
        
        # Create dashboard
        dashboard = Dashboard(app)
        
        # Handle window close
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit the Admin Panel?"):
                app.destroy()
        
        app.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("🚀 BallotGuard Admin Panel starting...")
        print("📊 Dashboard loaded successfully")
        print("💡 Demo mode active - shows mock voting data")
        
        app.mainloop()
        
    except Exception as e:
        print(f"Error starting Admin Panel: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
