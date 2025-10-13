from ttkbootstrap import Frame, Label, Button
from utils.api_client import APIClient

class Dashboard(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.api = APIClient()
        self.label = Label(self, text="Total Votes: fetching...", font=("Arial", 16))
        self.label.pack(pady=40)
        Button(self, text="Refresh Tally", command=self.update_tally).pack(pady=10)
        self.update_tally()

    def update_tally(self):
        data = self.api.get_tally()
        if "total_votes" in data:
            self.label.configure(text=f"Total Votes: {data['total_votes']}")
        else:
            self.label.configure(text="Error fetching tally")
