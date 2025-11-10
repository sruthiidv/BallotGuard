from setuptools import setup, find_packages
import os

# Read install requirements from requirements.txt
here = os.path.abspath(os.path.dirname(__file__))
req_file = os.path.join(here, 'requirements.txt')
install_requires = []
if os.path.exists(req_file):
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            install_requires.append(line)

setup(
    name="ballotguard",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            # Run the admin UI: this dispatches to the admin module's main()
            'run-admin=admin.admin_panel_ui.main:main',
            # Run the voter UI: dispatch to the client_app voting app
            'run-voter=client_app.voting.app:main',
        ]
    },
    long_description='''
BallotGuard
-------------

This package contains the BallotGuard voter and admin UIs and the supporting modules.

Running the UIs
---------------
- From PowerShell helper scripts (recommended):
  - `./run_admin.ps1` — starts the Admin UI (activates .venv if present)
  - `./run_voter.ps1` — starts the Voter UI

- After installing the package (editable install during development):
  - `pip install -e .`
  - Then you can launch the apps via console scripts:
    - `run-admin`
    - `run-voter`

These console scripts call the package entry points and are cross-platform.
'''
)