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

# ---------------- Helpers ----------------

def _validate_inputs(**fields):
    """Raise ValueError if any required field is empty."""
    for name, value in fields.items():
        if not value:
            raise ValueError(f"Field '{name}' must not be empty.")

def _git_is_available():
    """Return True if git is on PATH."""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# ---------------- Git Operations ----------------

def clone_gerrit_repo(project, branch, commit_hash=None):
    current_dir = os.getcwd()
    server = 'buic-scm-ias.automotive-wan.com'
    port = '29418'
    ssh_url = f"ssh://{server}:{port}/{project}"
    local_path = os.path.join(current_dir, project.strip().split('/')[-1])

    if os.path.exists(local_path):
        logger.warning(f"Repository already exists, reusing: {local_path}")
        if commit_hash:
            checkout_to_commit_hash(commit_hash, local_path)
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
        raise


def checkout_to_commit_hash(commit, repo_path):
    """Checkout a specific commit; raises on failure so callers are aware."""
    try:
        subprocess.run(["git", "checkout", commit],
                       cwd=repo_path, check=True, capture_output=True, text=True)
        logger.info(f"Checked out to specific commit hash -> {commit}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking out commit {commit}: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        raise


def push_changes_to_github(github_repo, gerrit_repo_name, github_branch,
                            commit_hash=None, gerrit_repo_branch=None):
    repo = gerrit_repo_name.strip().split('/')[-1]
    working_directory = os.path.join(os.getcwd(), repo)
    if not os.path.exists(working_directory):
        raise FileNotFoundError(
            f"Working directory '{working_directory}' does not exist. "
            "Make sure the Gerrit clone step succeeded."
        )

    remote_name = 'github'
    try:
        # Add remote only if it doesn't already exist
        existing = subprocess.run(
            ["git", "remote"], cwd=working_directory,
            capture_output=True, text=True, check=True
        ).stdout.split()

        if remote_name not in existing:
            logger.info(f"Adding GitHub remote -> {github_repo}...")
            subprocess.run(
                ["git", "remote", "add", remote_name, github_repo],
                cwd=working_directory, check=True, capture_output=True, text=True
            )
        else:
            logger.info(f"Remote '{remote_name}' already exists, skipping add.")

        logger.info("Fetching changes from GitHub...")
        subprocess.run(["git", "fetch", remote_name],
                       cwd=working_directory, check=True, capture_output=True, text=True)

        if commit_hash:
            temp_branch_name = f"temp-{commit_hash[:8]}"
            # Delete local branch first if it already exists (re-run scenario)
            subprocess.run(
                ["git", "branch", "-D", temp_branch_name],
                cwd=working_directory, capture_output=True
            )
            subprocess.run(["git", "checkout", "-b", temp_branch_name, commit_hash],
                           cwd=working_directory, check=True, capture_output=True, text=True)
            refspec = f"{temp_branch_name}:{github_branch}"
            logger.info(f"Commit hash present, refspec -> {refspec}")
        else:
            if not gerrit_repo_branch:
                raise ValueError("Either commit_hash or gerrit_repo_branch must be provided.")
            refspec = f"{gerrit_repo_branch}:{github_branch}"
            logger.info(f"Commit hash not present, refspec -> {refspec}")

        logger.info(f"Pushing changes to GitHub as -> {refspec}")
        subprocess.run(["git", "push", remote_name, refspec, "--force-with-lease"],
                       cwd=working_directory, check=True, capture_output=True, text=True)
        logger.info("GitHub push was successfully performed!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        raise


def run_script(entry_gp, entry_gb, entry_gc, entry_ghr, entry_ghb, run_button):
    # Read values from the GUI
    gerrit_project = entry_gp.get().strip()
    gerrit_branch = entry_gb.get().strip()
    gerrit_commit = entry_gc.get().strip()
    github_repo = entry_ghr.get().strip()
    github_branch = entry_ghb.get().strip()

    try:
        _validate_inputs(**{
            "Gerrit Project": gerrit_project,
            "Gerrit Branch": gerrit_branch,
            "GitHub Repository": github_repo,
            "GitHub Branch": github_branch,
        })

        if not _git_is_available():
            raise EnvironmentError("'git' executable not found on PATH.")

        clone_gerrit_repo(gerrit_project, gerrit_branch, gerrit_commit or None)
        push_changes_to_github(github_repo, gerrit_project, github_branch,
                               gerrit_commit or None, gerrit_branch)
        messagebox.showinfo("Success", "Operation completed successfully.")
    except Exception as e:
        logger.error(f"run_script failed: {e}")
        messagebox.showerror("Error", str(e))
    finally:
        # Re-enable the button regardless of outcome
        run_button.configure(state="normal", text="Run Sync")


def start_thread(entry_gp, entry_gb, entry_gc, entry_ghr, entry_ghb, run_button):
    run_button.configure(state="disabled", text="Running…")
    t = threading.Thread(
        target=run_script,
        args=(entry_gp, entry_gb, entry_gc, entry_ghr, entry_ghb, run_button),
        daemon=True
    )
    t.start()


# ---------------- GUI main ----------------
def main():
    if not _git_is_available():
        messagebox.showerror("Startup Error", "'git' is not available on PATH. Aborting.")
        return

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Gerrit → GitHub Sync Tool")
    root.geometry("520x340")

    frame = ctk.CTkFrame(root)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    frame.grid_columnconfigure(1, weight=1)

    labels = [
        "Gerrit Project",
        "Gerrit Branch",
        "Gerrit Commit (optional)",
        "GitHub Repository",
        "GitHub Branch",
    ]

    entries = []
    for i, text in enumerate(labels):
        lbl = ctk.CTkLabel(frame, text=text)
        lbl.grid(row=i, column=0, padx=10, pady=10, sticky="w")

        entry = ctk.CTkEntry(frame, width=350)
        entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
        entries.append(entry)

    entry_gp, entry_gb, entry_gc, entry_ghr, entry_ghb = entries

    run_button = ctk.CTkButton(frame, text="Run Sync")
    # Pass run_button into the callback so it can be disabled/re-enabled
    run_button.configure(
        command=lambda: start_thread(entry_gp, entry_gb, entry_gc, entry_ghr, entry_ghb, run_button)
    )
    run_button.grid(row=5, column=1, pady=20)

    root.mainloop()


# ---------------- Entry point ----------------
if __name__ == "__main__":
    main()

