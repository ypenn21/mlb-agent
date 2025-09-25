#!/usr/bin/env python3
"""
MLB Agent Lab - Task File Loader
Downloads lab files from GCS bucket with backup and confirmation features.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import shutil

# Configuration
BUCKET_NAME = "adk-mlb-lab-files"
BUCKET_PREFIX = f"gs://{BUCKET_NAME}"

# Always work from this folder
ROOT_DIR = os.path.expanduser("~/mlb-agent-lab")

# File mappings for each task
TASK_FILES = {
    "setup": {
        "files": {
            "requirements.txt": "setup/requirements.txt",
            "config.env": "setup/config.env",
            "activate.sh": "setup/activate.sh"
        },
        "description": "Initial setup files (requirements, config, activation script)"
    },
    "2": {
        "files": {
            "workspace/mlb_scout/agent_instructions.py": "task2/agent_instructions.py"
        },
        "description": "Agent instruction template for Task 2"
    },
    "2-solution": {
        "files": {
            "workspace/mlb_scout/__init__.py": "task2-solution/workspace/mlb_scout/__init__.py",
            "workspace/mlb_scout/agent_instructions.py": "task2-solution/workspace/mlb_scout/agent_instructions.py",
            "workspace/mlb_scout/agent.py": "task2-solution/workspace/mlb_scout/agent.py",
            "config.env": "task2-solution/config.env",
            "activate.sh": "task2-solution/activate.sh",
            "requirements.txt": "task2-solution/requirements.txt"
        },
        "description": "Full solution state for Task 2"
    },
    "4": {
        "files": {
            "workspace/mlb_scout/tools.yaml": "task4/tools.yaml",
        },
        "description": "MCP tools configuration starter"
    },
    "4-solution": {
        "files": {
            "workspace/mlb_scout/__init__.py": "task4-solution/workspace/mlb_scout/__init__.py",
            "workspace/mlb_scout/agent_instructions.py": "task4-solution/workspace/mlb_scout/agent_instructions.py",
            "workspace/mlb_scout/agent.py": "task4-solution/workspace/mlb_scout/agent.py",
            "workspace/mlb_scout/tools.yaml": "task4-solution/workspace/mlb_scout/tools.yaml",
            "workspace/mlb_scout/.env": "task4-solution/workspace/mlb_scout/.env",
            "config.env": "task4-solution/config.env",
            "activate.sh": "task4-solution/activate.sh",
            "requirements.txt": "task4-solution/requirements.txt"
        },
        "description": "Full solution state for Task 4"
    },
    "6": {
        "files": {
            "mlb_scout_ui/app.py": "task6/app.py",
        },
        "description": "Load the Streamlit starter app"
    },
    "6-solution": {
        "files": {
            "mlb_scout_ui/app.py": "task6-solution/mlb_scout_ui/app.py",
            "mlb_scout_ui/Procfile": "task6-solution/mlb_scout_ui/Procfile",
            "mlb_scout_ui/requirements.txt": "task6-solution/mlb_scout_ui/requirements.txt",
            "workspace/mlb_scout/__init__.py": "task6-solution/workspace/mlb_scout/__init__.py",
            "workspace/mlb_scout/agent_instructions.py": "task6-solution/workspace/mlb_scout/agent_instructions.py",
            "workspace/mlb_scout/agent.py": "task6-solution/workspace/mlb_scout/agent.py",
            "workspace/mlb_scout/.env": "task6-solution/workspace/mlb_scout/.env",
            "workspace/mlb_scout/tools.yaml": "task6-solution/workspace/mlb_scout/tools.yaml",
            "workspace/mlb_scout/requirements.txt": "task6-solution/workspace/mlb_scout/requirements.txt",
            "config.env": "task6-solution/config.env",
            "activate.sh": "task6-solution/activate.sh",
            "requirements.txt": "task6-solution/requirements.txt"
        },
        "description": "Full solution state for Task 6 with new UI"
    },
    "7": {
        "files": {
            "workspace/mlb_scout/mlb_tools.py": "task7/mlb_tools.py",
            "workspace/mlb_scout/agent_instructions.py": "task7/agent_instructions.py",
        },
        "description": "Load the MLB API tools and updated instructions"
    },
    "7-solution": {
        "files": {
            "mlb_scout_ui/app.py": "task7-solution/mlb_scout_ui/app.py",
            "mlb_scout_ui/Procfile": "task7-solution/mlb_scout_ui/Procfile",
            "mlb_scout_ui/requirements.txt": "task7-solution/mlb_scout_ui/requirements.txt",
            "workspace/mlb_scout/__init__.py": "task7-solution/workspace/mlb_scout/__init__.py",
            "workspace/mlb_scout/agent_instructions.py": "task7-solution/workspace/mlb_scout/agent_instructions.py",
            "workspace/mlb_scout/agent.py": "task7-solution/workspace/mlb_scout/agent.py",
            "workspace/mlb_scout/.env": "task7-solution/workspace/mlb_scout/.env",
            "workspace/mlb_scout/mlb_tools.py": "task7-solution/workspace/mlb_scout/mlb_tools.py",
            "workspace/mlb_scout/tools.yaml": "task7-solution/workspace/mlb_scout/tools.yaml",
            "workspace/mlb_scout/requirements.txt": "task7-solution/workspace/mlb_scout/requirements.txt",
            "config.env": "task7-solution/config.env",
            "activate.sh": "task7-solution/activate.sh",
            "requirements.txt": "task7-solution/requirements.txt"
        },
        "description": "Full solution state for Task 7 with UI and tools"
    }
}


# Special handling for notebook
NOTEBOOK_INFO = {
    "url": f"https://storage.googleapis.com/{BUCKET_NAME}/notebooks/mlb_data_analytics.ipynb",
    "local_path": "mlb_data_analytics.ipynb"
}


def create_backup(filepath):
    """Create a backup of existing file"""
    full_path = os.path.join(ROOT_DIR, filepath)
    if os.path.exists(full_path):
        backup_dir = os.path.join(ROOT_DIR, ".backup")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(filepath)
        backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}")

        shutil.copy2(full_path, backup_path)
        return backup_path
    return None


def download_file(gcs_path, local_path):
    """Download a file from GCS"""
    try:
        full_path = os.path.join(ROOT_DIR, local_path)
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Download using gsutil
        cmd = ["gsutil", "cp", f"{BUCKET_PREFIX}/{gcs_path}", full_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Error downloading {gcs_path}: {result.stderr}")
            return False

        print(f"   ✅ Downloaded to: {full_path}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def load_task(task_id, force=False):
    """Load files for a specific task"""
    if task_id not in TASK_FILES:
        print(f"❌ Unknown task: {task_id}")
        print(f"Available tasks: {', '.join(TASK_FILES.keys())}")
        return False

    task_info = TASK_FILES[task_id]
    print(f"\n📋 Task: {task_info['description']}")

    # If it's a solution task and no files listed, do a full overwrite
    if "-solution" in task_id and not task_info["files"]:
        print("🛠️  Solution task detected. Preparing full folder restore.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(ROOT_DIR, ".backup", f"full_{timestamp}")
        print(f"\n📦 Backing up current folder to: {backup_dir}")
        os.makedirs(backup_dir, exist_ok=True)

        # Directories to exclude from backup
        EXCLUDE_DIRS = {".backup", "__pycache__", "venv"}

        for item in os.listdir(ROOT_DIR):
            if item in EXCLUDE_DIRS:
                continue
            src = os.path.join(ROOT_DIR, item)
            dst = os.path.join(backup_dir, item)
            shutil.move(src, dst)

        print("✅ Backup complete.")

        print(f"\n📥 Downloading solution from GCS: gs://{BUCKET_NAME}/{task_id}/")
        cmd = [
            "gsutil", "-m", "cp", "-r",
            f"{BUCKET_PREFIX}/{task_id}/*",
            ROOT_DIR
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Error downloading solution folder:\n{result.stderr}")
            return False

        print(f"\n✅ Solution files restored to: {ROOT_DIR}")
        return True



    # Check for existing files
    existing_files = []
    for local_path in task_info["files"].keys():
        full_path = os.path.join(ROOT_DIR, local_path)
        if os.path.exists(full_path):
            existing_files.append(full_path)

    if existing_files and not force:
        print("\n⚠️  The following files already exist:")
        for f in existing_files:
            print(f"   - {f}")

        response = input("\nFiles will be backed up before overwriting. Continue? (y/n): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled.")
            return False

    # Process each file
    success_count = 0
    for local_path, gcs_path in task_info["files"].items():
        print(f"\n📥 Downloading: {os.path.basename(local_path)}")

        # Backup existing file
        backup_path = create_backup(local_path)
        if backup_path:
            print(f"   📁 Backed up to: {backup_path}")

        # Download new file
        if download_file(gcs_path, local_path):
            success_count += 1
        else:
            print(f"   ❌ Failed to download")

    print(f"\n✅ Successfully loaded {success_count}/{len(task_info['files'])} files")
    return success_count == len(task_info["files"])


def handle_notebook():
    """Special handling for the notebook"""
    print("\n📓 MLB Data Analytics Notebook")
    print("-" * 40)
    print("The notebook for Tasks 3 & 4 contains:")
    print("  • Data loading from MLB Stats API")
    print("  • BigQuery table creation")
    print("  • Performance metrics calculations")
    print("  • BQML model training")

    print(f"\n📥 Download the notebook from:")
    print(f"   {NOTEBOOK_INFO['url']}")

    print("\n📝 Instructions:")
    print("1. Click the link above to download the notebook")
    print("2. In Cloud Console, navigate to Vertex AI > Colab Enterprise")
    print("3. Click 'Upload notebook' and select the downloaded file")
    print("4. Follow the instructions in the notebook")

    response = input("\nWould you like to download the notebook locally as backup? (y/n): ")
    if response.lower() == 'y':
        notebook_path = os.path.join(ROOT_DIR, NOTEBOOK_INFO['local_path'])
        if download_file("notebooks/mlb_data_analytics.ipynb", NOTEBOOK_INFO['local_path']):
            print(f"✅ Notebook saved to: {notebook_path}")
        else:
            print("❌ Failed to download notebook")


def main():
    print(f"📁 Working from lab root: {ROOT_DIR}")
    parser = argparse.ArgumentParser(description="Load files for MLB Agent Lab tasks")
    parser.add_argument("task", help="Task identifier (setup, 2, 3-4, 5, 8, notebook)")
    parser.add_argument("--solution", action="store_true", help="Load solution files")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    # Handle special cases
    if args.task == "notebook":
        handle_notebook()
        return

    # Construct task ID
    task_id = args.task
    if args.solution and f"{task_id}-solution" in TASK_FILES:
        task_id = f"{task_id}-solution"

    # Special handling for task 3-4
    if task_id == "3-4":
        print("\n📓 Tasks 3 & 4 use a Colab Enterprise notebook")
        print("Run: python load_task.py notebook")
        return

    # Load the task files
    load_task(task_id, args.force)


if __name__ == "__main__":
    main()