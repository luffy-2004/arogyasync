# Deployment Instructions - Offline-First PHC Management System

This document outlines deployment configurations for running the application in a production primary health centre (PHC) environment.

---

## 1. Prerequisites

* **Python**: Python 3.13 (recommended for this project)
* **Local OS**: Windows / Linux / macOS (deployed locally on clinic desktops/laptops)
* **Local Database**: SQLite (installed natively with Python, no separate service required)
* **Cloud Database**: PostgreSQL 15+ (hosted in the central cloud/state data center)

---

## 2. Installation Steps

### Step 1: Clone and Set Up Environment
Open a terminal in the project directory:
```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY="replace-with-a-secure-random-string-for-production"
LOCAL_DATABASE_URL="sqlite:///./local_phc.db"
CLOUD_DATABASE_URL="postgresql://username:password@cloud-host:5432/arogyasync_cloud"
```
> [!NOTE]
> If there is no cloud database configured yet, you can leave `CLOUD_DATABASE_URL` empty or omit it. The application will continue functioning as a standalone offline local database.

---

## 3. Database Migrations (Alembic)

The application automatically creates database tables in SQLite on startup. However, for schema updates and central PostgreSQL deployments, Alembic migrations are standard.

### Initialize Migrations (if customizing schema)
```bash
alembic init migrations
```
Configure `migrations/env.py` to point to our models metadata:
* Set `target_metadata = Base.metadata` from `app.db.base`.
* Read database URLs from `app.config.settings`.

To generate and apply a migration:
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## 4. Running the Application

### Running Local API Server
Start the FastAPI server via Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
* **Interactive Documentation (Swagger)**: Access [http://localhost:8000/docs](http://localhost:8000/docs)
* **Local SQLite Store**: A file `local_phc.db` will be created in the current working directory.

---

## 5. Synchronization Worker Scheduling

To push records from local SQLite to cloud PostgreSQL automatically, you should schedule a task that regularly invokes the sync engine.

### Option A: Background Cron Job / Task Scheduler (Recommended)
You can schedule a script to run every 5 minutes.

Create a script `run_sync.py`:
```python
import os
import sys
from dotenv import load_dotenv

# Ensure the root path is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.services.sync_engine import sync_engine

if __name__ == "__main__":
    print("Checking database sync status...")
    stats = sync_engine.sync_local_to_cloud()
    print(f"Sync complete. Stats: {stats}")
```

#### On Windows (Task Scheduler):
Configure a task via command line to execute the sync script every 5 minutes:
```cmd
schtasks /create /tn "PHC_Data_Sync" /tr "C:\Users\anant\Desktop\arogyasync\venv\Scripts\python.exe C:\Users\anant\Desktop\arogyasync\run_sync.py" /sc minute /mo 5
```

#### On Linux (Cron Job):
Add the following line to `crontab -e`:
```text
*/5 * * * * /path/to/arogyasync/venv/bin/python /path/to/arogyasync/run_sync.py >> /var/log/arogyasync_sync.log 2>&1
```

### Option B: HTTP Triggered Sync
If you prefer triggering synchronization directly from a client application (e.g. clicking a "Go Online & Sync" button in a UI dashboard), simply make a `POST` request to:
`http://localhost:8000/api/v1/sync/trigger`
Protected by JWT authentication.
