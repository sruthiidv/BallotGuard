import ttkbootstrap as ttkb
from components.dashboard import Dashboard

def main():
    app = ttkb.Window(themename="darkly")
    app.title("BallotGuard Admin Panel")
    app.geometry("800x600")
    Dashboard(app)
    app.mainloop()

if __name__ == "__main__":
    main()
