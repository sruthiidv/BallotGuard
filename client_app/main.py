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
