import subprocess
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import threading

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
def clone_gerrit_repo(project, branch, commit_hash=None):
    current_dir = os.getcwd()
    server = 'buic-scm-ias.automotive-wan.com'
    port = '29418'
    ssh_url = f"ssh://{server}:{port}/{project}"
    local_path = os.path.join(current_dir, project.strip().split('/')[-1])

    if os.path.exists(local_path):
        logger.error(f"{local_path} already exists")
        return local_path

    scp_command = [
        "scp", "-p", "-O", "-P", port,
        f"{server}:hooks/commit-msg",
        f"{local_path}/.git/hooks"
    ]

    try:
        logger.info(f"Cloning project -> {project} with branch -> {branch}...")
        subprocess.run(["git", "clone", "-b", branch, ssh_url],
                       cwd=current_dir, check=True, capture_output=True, text=True)
        logger.info("Cloning succeeded.")

        logger.info("SCP for commit-msg hook...")
        subprocess.run(scp_command, cwd=current_dir, check=True, capture_output=True, text=True)
        logger.info("SCP succeeded.")

        if commit_hash:
            checkout_to_commit_hash(commit_hash, local_path)
        return local_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during clone or scp: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        return None


def checkout_to_commit_hash(commit, repo_path):
    try:
        subprocess.run(["git", "checkout", commit],
                       cwd=repo_path, check=True, capture_output=True, text=True)
        logger.info(f"Checked out to specific commit hash -> {commit}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking out commit {commit}: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")


def push_changes_to_github(github_repo, gerrit_repo_name, github_branch, commit_hash=None, gerrit_repo_branch=None):
    repo = gerrit_repo_name.strip().split('/')[-1]
    working_directory = os.path.join(os.getcwd(), repo)
    if not os.path.exists(working_directory):
        logger.error(f"Working directory {working_directory} does not exist")
        return
    remote_name = 'github'
    try:
        logger.info(f"Adding GitHub remote -> {github_repo}...")
        subprocess.run(["git", "remote", "add", remote_name, github_repo],
                       cwd=working_directory, check=False)

        logger.info("Fetching changes from GitHub...")
        subprocess.run(["git", "fetch", remote_name],
                       cwd=working_directory, check=True, capture_output=True, text=True)

        if commit_hash:
            temp_branch_name = f"temp-{commit_hash[:8]}"
            subprocess.run(["git", "checkout", "-b", temp_branch_name, commit_hash],
                           cwd=working_directory, check=True, capture_output=True, text=True)
            refspec = f"{temp_branch_name}:{github_branch}"
            logger.info(f"Commit hash present, refspec will be  -> {refspec}")
        else:
            refspec = f"{gerrit_repo_branch}:{github_branch}"
            logger.info(f"Commit hash not preset, refspec will be  -> {refspec}")

        logger.info(f"Pushing changes to GitHub as -> {refspec}")
        subprocess.run(["git", "push", remote_name, refspec, "--force-with-lease"],
                       cwd=working_directory, check=True, capture_output=True, text=True)
        logger.info("Github push was successfully performed!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")

def run_script(entry_gp, entry_gb, entry_gc, entry_ghb, entry_ghr):
    # read values from the GUI
    gerrit_project = entry_gp.get().strip()
    gerrit_branch = entry_gb.get().strip()
    gerrit_commit = entry_gc.get().strip()
    github_branch = entry_ghb.get().strip()
    github_repo = entry_ghr.get().strip()


    try:
        clone_gerrit_repo(gerrit_project, gerrit_branch,gerrit_commit)
        push_changes_to_github(github_repo, gerrit_project,github_branch, gerrit_commit,gerrit_branch)
        messagebox.showinfo("Success", "Operation completed successfully")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_thread(entry_gp, entry_gb, entry_gc, entry_ghb, entry_ghr):

    t = threading.Thread(target=run_script, args=(entry_gp, entry_gb, entry_gc, entry_ghb, entry_ghr))
    t.start()

# ---------------- GUI main ----------------
def main():
    root = tk.Tk()
    root.title("Gerrit → GitHub Sync Tool")
    root.geometry("500x320")

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    # Entry fields
    ttk.Label(frame, text="Gerrit Project").grid(row=0, column=0, sticky="w")
    entry_gp = ttk.Entry(frame, width=50)
    entry_gp.grid(row=0, column=1)

    ttk.Label(frame, text="Gerrit Branch").grid(row=1, column=0, sticky="w")
    entry_gb = ttk.Entry(frame, width=50)
    entry_gb.grid(row=1, column=1)

    ttk.Label(frame, text="Gerrit Commit (optional)").grid(row=2, column=0, sticky="w")
    entry_gc = ttk.Entry(frame, width=50)
    entry_gc.grid(row=2, column=1)

    ttk.Label(frame, text="GitHub Branch").grid(row=4, column=0, sticky="w")
    entry_ghr = ttk.Entry(frame, width=50)
    entry_ghr.grid(row=3, column=1)

    ttk.Label(frame, text="GitHub Repository").grid(row=3, column=0, sticky="w")
    entry_ghb = ttk.Entry(frame, width=50)
    entry_ghb.grid(row=4, column=1)

    # Run button
    run_button = ttk.Button(
        frame,
        text="Run Sync",
        command=lambda: start_thread(entry_gp, entry_gb, entry_gc, entry_ghb, entry_ghr)
    )
    run_button.grid(row=7, column=1, pady=20)

    root.mainloop()

# ---------------- Run Flask ----------------
if __name__ == "__main__":
    main()