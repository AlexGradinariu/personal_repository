import subprocess
import os
import logging
import customtkinter as ctk
import threading
from tkinter import messagebox

# ---------------- Logging ----------------
log_file = os.path.join(os.getcwd(), "gerrit_sync.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(log_file, mode='a')  # append mode
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ---------------- Git Operations ----------------

def run_git(cmd, cwd):
    """Execute a git command with logging."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {' '.join(cmd)}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def clone_target_github_repo(project, branch="main"):
    current_dir = os.getcwd()
    repo_name = project.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(current_dir, repo_name)
    if os.path.exists(repo_path):
        logger.warning(f"Repository already exists: {repo_path}")
        return repo_path
    logger.info(f"Cloning project {project} (branch: {branch})")
    if not run_git(["git", "clone", "-b", branch, project], cwd=current_dir):
        return None

    logger.info("Clone successful")
    return repo_path

def add_and_fetch_github_source_repo(project,commit_hash):
    remote_name = 'REMOTE'
    repo_name  = project.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(os.getcwd(), repo_name )
    if not os.path.isdir(repo_path):
        logger.error(f"Repository path not found: {repo_path}")
        return False
    remotes = subprocess.run(
        ["git", "remote"],cwd=repo_path,capture_output=True,text=True).stdout.split()

    if remote_name not in remotes:
        if not run_git(["git", "remote", "add", remote_name, project], cwd=repo_path):
            return False
        logger.info(f"Remote added: {remote_name}")
    else:
        logger.info(f"Remote already exists: {remote_name}")

    if not run_git(["git", "fetch", remote_name], cwd=repo_path):
        return False

    logger.info("Remote fetch successful")

    if not cherry_pick_source_commit_hash(commit_hash, repo_path):
        return False

    if not push_change_to_github(remote_name, commit_hash, repo_path):
        return False

    return True

def cherry_pick_source_commit_hash(commit_hash, folder_path):

    logger.info(f"Cherry-picking commit {commit_hash}")
    try:
        subprocess.run(
            ["git", "cherry-pick", commit_hash],
            cwd=folder_path,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Cherry-pick successful")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Cherry-pick failed")
        logger.error(e.stderr)
        subprocess.run(["git", "cherry-pick", "--abort"], cwd=folder_path)
        return False

def push_change_to_github(remote, commit_hash, repo_path):

    test_branch = f"{remote}_{commit_hash[:6]}"
    if not run_git(["git", "checkout", "-b", test_branch], cwd=repo_path):
        return False
    logger.info(f"Pushing branch {test_branch}")
    if not run_git(["git", "push", "origin",f"HEAD:refs/heads/{test_branch}"], cwd=repo_path):
        return False
    logger.info("Push successful")
    return True

def run_script(entry_gtr, entry_gtb, entry_gsr, entry_gsc):
    github_target_repo = entry_gtr.get().strip()
    github_target_branch = entry_gtb.get().strip()
    github_source_repo = entry_gsr.get().strip()
    github_source_commit = entry_gsc.get().strip()

    try:
        print(github_target_repo,github_target_branch,github_source_repo,github_source_commit)
        clone_target_github_repo(github_target_repo, github_target_branch)
        add_and_fetch_github_source_repo(github_source_repo, github_source_commit)
        messagebox.showinfo("Success", "Operation completed successfully")
    except Exception as e:
        messagebox.showerror("Error", str(e))
#
def start_thread(entry_gtr, entry_gtb, entry_gsr, entry_gsc):
    t = threading.Thread(
        target=run_script,
        args=(entry_gtr, entry_gtb, entry_gsr, entry_gsc),
        daemon=True
    )
    t.start()
#
# # ---------------- GUI main ----------------
def main():
    ctk.set_appearance_mode("dark")  # "light" / "dark"
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Gerrit → GitHub Sync Tool")
    root.geometry("520x340")

    frame = ctk.CTkFrame(root)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Configure grid
    frame.grid_columnconfigure(1, weight=1)

    # Labels + Entries
    labels = [
        "GitHub Target Repo",
        "GitHub Target Branch",
        "GitHub Source Repo",
        "GitHub Source Commit Hash"
    ]

    entries = []

    for i, text in enumerate(labels):
        lbl = ctk.CTkLabel(frame, text=text)
        lbl.grid(row=i, column=0, padx=10, pady=10, sticky="w")

        entry = ctk.CTkEntry(frame, width=350)
        entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")

        entries.append(entry)

    entry_gtr, entry_gtb, entry_gsr, entry_gsc = entries

    # Run button
    run_button = ctk.CTkButton(
        frame,
        text="Run Sync",
        command=lambda: start_thread(entry_gtr, entry_gtb, entry_gsr, entry_gsc)
    )
    run_button.grid(row=5, column=1, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
