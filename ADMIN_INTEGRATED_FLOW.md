# BallotGuard Admin Panel - Integrated Flow

## Changes Made

### 1. Updated PowerShell Launcher
**File**: `run_admin.ps1`
- **Before**: Ran `admin/admin_panel_ui/main.py` (API-based client)
- **After**: Runs `admin/admin_panel_integrated/main.py` (Fully integrated)

### 2. Unified Server Endpoints
**File**: `admin/admin_panel_integrated/blockchain_connector.py`
- **Before**: `http://localhost:5000` (incorrect port)
- **After**: `http://127.0.0.1:8443` (same as database connector)

---

## System Architecture After Changes

```
┌─────────────────────────────────────────────────────────┐
│         run_admin.ps1 (PowerShell Launcher)              │
│  Activates .venv and runs integrated admin panel        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│    admin/admin_panel_integrated/main.py                  │
│           AdminPanelApp (Tkinter GUI)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 4 Tabs:                                          │  │
│  │ 1. 📊 Dashboard & Results                        │  │
│  │ 2. 🗳️  Election Management                       │  │
│  │ 3. ➕ Create Election                            │  │
│  │ 4. 🛡️  Security Monitor                          │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬──────────────────┐
        │                     │                  │
        ▼                     ▼                  ▼
   ┌─────────────┐     ┌──────────────┐   ┌────────────────┐
   │ Database    │     │ Blockchain   │   │ Election       │
   │ Connector   │     │ Connector    │   │ Manager        │
   │             │     │              │   │                │
   │ Manages:    │     │ Manages:     │   │ Orchestrates:  │
   │ - Elections │     │ - Chain      │   │ - Creation     │
   │ - Candidates│     │   Status     │   │ - Finalization │
   │ - Votes     │     │ - Integrity  │   │ - Deletion     │
   │ - Results   │     │   Checks     │   │ - Tallying     │
   └─────────────┘     └──────────────┘   └────────────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────────┐
        │  Flask Server            │
        │  (server/server.py)      │
        │  Port: 8443              │
        │  ┌─────────────────────┐ │
        │  │ Endpoints:          │ │
        │  │ /elections          │ │
        │  │ /blockchain/info    │ │
        │  │ /blockchain/blocks  │ │
        │  │ /votes              │ │
        │  │ /test-db            │ │
        │  └─────────────────────┘ │
        └────────────┬─────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
   ┌─────────────┐         ┌──────────────┐
   │ SQLite DB   │         │ Blockchain   │
   │ (votes,     │         │ (chain of    │
   │  elections, │         │  blocks with │
   │  voters)    │         │  hashes)     │
   └─────────────┘         └──────────────┘
```

---

## Data Flow by Tab

### Tab 1: Dashboard & Results
```
User selects election → 
  ├─ DatabaseConnector.get_elections()
  ├─ BlockchainConnector.get_chain_status()
  ├─ DatabaseConnector.get_election_results(eid)
  └─ Display: Results + Chain Status

Actions:
  ├─ View Results → Fetch + Display detailed tally
  ├─ Export Results → Save JSON with winner info
  └─ Finalize Results → ElectionManager.finalize_election()
```

### Tab 2: Election Management
```
Load elections →
  ├─ DatabaseConnector.get_elections()
  └─ Display: List of all elections

Actions:
  ├─ Refresh List
  ├─ Delete Selected → ElectionManager.delete_election()
  └─ Add New Election → Switch to Tab 3
```

### Tab 3: Create Election
```
Fill form (title, dates, candidates) →
  ├─ Validate inputs
  ├─ ElectionManager.create_new_election(data)
  │   └─ DatabaseConnector.create_election(data)
  └─ Success → Refresh + Switch to Tab 2
```

### Tab 4: Security Monitor
```
Load chain status →
  ├─ BlockchainConnector.get_chain_status()
  ├─ BlockchainConnector.get_vote_verification_info()
  └─ Display: Chain integrity + block count

Actions:
  ├─ Verify Chain → Refresh chain status
  └─ Simulate Admin Modify → Break chain for testing
```

---

## Connection Details

### All Components → Single Flask Server
```
Host: 127.0.0.1
Port: 8443
Protocol: HTTP

DatabaseConnector: http://127.0.0.1:8443
BlockchainConnector: http://127.0.0.1:8443 ✅ (Fixed)
```

### Server Endpoints Used
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/test-db` | GET | Test database connection |
| `/elections` | GET/POST | List/Create elections |
| `/elections/{id}` | GET | Get specific election |
| `/elections/{id}/results` | GET | Get election results |
| `/elections/{id}/delete` | POST | Delete election |
| `/blockchain/info` | GET | Get blockchain info |
| `/blockchain/blocks` | GET | Get blocks (with limit) |

---

## Startup Sequence

1. **PowerShell**: `.\run_admin.ps1` executed
2. **Activate venv** (if `.venv/Scripts/Activate.ps1` exists)
3. **Launch Python**: `admin/admin_panel_integrated/main.py`
4. **Initialize AdminPanelApp**:
   - Create `DatabaseConnector()` → Test connection to server:8443
   - Create `BlockchainConnector()` → Test blockchain endpoints
   - Create `ElectionManager(db, blockchain)`
   - Build 4-tab GUI
5. **Load Initial Data**:
   - `refresh_elections()` → Fetch all elections
   - `update_dashboard_selection_ui()` → Update chain status
6. **GUI Ready** → User can interact with all tabs

---

## Security Features

✅ **Blockchain Integrity Monitoring**
- Auto-detect chain breaks
- Disable result operations if chain is broken
- Visual indicators (Chain: OK vs Chain: BROKEN)

✅ **Admin Action Logging**
- Election creation logged
- Election deletion logged
- Modifications tracked in system

✅ **Direct Database Access**
- No API authentication layers (trusted admin environment)
- Direct SQLite queries through Flask endpoints
- Real-time vote tally aggregation

---

## Requirements

### Python Packages
```
tkinter (built-in)
ttkbootstrap
requests
datetime
json
os
```

### External Services
- **Flask Server**: Must be running on `http://127.0.0.1:8443`
  - Start with: `python server/server.py`

### Directory Structure
```
admin/admin_panel_integrated/
├── main.py                    ← Entry point
├── database_connector.py       ← DB operations
├── blockchain_connector.py     ← Blockchain operations
└── election_manager.py         ← Business logic
```

---

## How to Run

```powershell
# Navigate to repository root
cd C:\Users\sruth\Documents\GitHub\BallotGuard

# Option 1: Use PowerShell launcher
.\run_admin.ps1

# Option 2: Manual (for debugging)
python .\admin\admin_panel_integrated\main.py
```

### Prerequisites
1. Flask server must be running:
   ```powershell
   python server/server.py
   ```
2. Ensure virtual environment is activated:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

---

## Key Advantages of This Setup

| Aspect | Integrated | API-Based |
|--------|-----------|----------|
| **Dependencies** | Only Tkinter + requests | Flask client + API server |
| **Latency** | Direct DB access | Network requests |
| **Reliability** | Single point of failure | Two failure points |
| **Security Monitoring** | Real-time blockchain checks | Delayed checks |
| **Testing** | Self-contained | Needs external server |
| **Maintenance** | Fewer files | More moving parts |

