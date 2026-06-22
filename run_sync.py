import os
import sys
from dotenv import load_dotenv

# Add current folder to PYTHONPATH to resolve app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.services.sync_engine import sync_engine

if __name__ == "__main__":
    print("Initializing synchronization task...")
    stats = sync_engine.sync_local_to_cloud()
    print(f"Sync execution finished. Statistics: {stats}")
