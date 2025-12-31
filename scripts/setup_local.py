#!/usr/bin/env python3
"""
Local setup script for Job Finder.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, check=True)
        return result.returncode == 0
    except:
        return False

def main():
    print("=" * 70)
    print("Job Finder - Local Setup")
    print("=" * 70)

    # Check Python
    v = sys.version_info
    if v.major != 3 or v.minor < 11:
        print(f"Python 3.11+ required, found {v.major}.{v.minor}")
        return 1
    print(f"Python {v.major}.{v.minor} OK")

    # Check Node
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        print("Node.js OK")
    except:
        print("Node.js not found")
        return 1

    # Check .env
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print("Creating .env file...")
        app_id = input("ADZUNA_APP_ID: ").strip()
        app_key = input("ADZUNA_APP_KEY: ").strip()
        with open(env_file, "w") as f:
            f.write(f"ADZUNA_APP_ID={app_id}\nADZUNA_APP_KEY={app_key}\n")

    # Install Python deps
    print("Installing Python dependencies...")
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Install frontend deps
    print("Installing frontend dependencies...")
    run_cmd(["npm", "install"], cwd=PROJECT_ROOT / "jobhunt")

    # Create frontend .env
    with open(PROJECT_ROOT / "jobhunt" / ".env.local", "w") as f:
        f.write("VITE_API_URL=http://localhost:8000\n")

    # Collect jobs
    print("Collecting jobs (this takes several minutes)...")
    run_cmd([sys.executable, "scripts/collect_all_jobs.py", "--target", "1000"])

    # Build index
    print("Building vector index...")
    run_cmd([sys.executable, "scripts/build_vector_index.py"])

    print("\n" + "=" * 70)
    print("SETUP COMPLETE!")
    print("=" * 70)
    print("\nTo run:")
    print("  Terminal 1: uvicorn api.main:app --reload --port 8000")
    print("  Terminal 2: cd jobhunt && npm run dev")
    print("\nOpen: http://localhost:5173")
    print("\nFor public access, use ngrok:")
    print("  ngrok http 8000")
    return 0

if __name__ == "__main__":
    sys.exit(main())
