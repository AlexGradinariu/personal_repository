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

def _repo_name(url):
    """Extract bare repo name from a URL or path (strips .git suffix)."""
    return url.rstrip("/").split("/")[-1].replace(".git", "")

# ---------------- Git Operations ----------------

def run_git(cmd, cwd):
    """Execute a git command; raises CalledProcessError on failure."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.debug(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {' '.join(cmd)}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        raise


def clone_target_github_repo(project, branch="main"):
    """Clone the target GitHub repo. If it already exists locally, reuse it."""
    current_dir = os.getcwd()
    repo_name = _repo_name(project)
    repo_path = os.path.join(current_dir, repo_name)

    if os.path.exists(repo_path):
        logger.warning(f"Repository already exists, reusing: {repo_path}")
        return repo_path

    logger.info(f"Cloning target repo {project} (branch: {branch})")
    run_git(["git", "clone", "-b", branch, project], cwd=current_dir)
    logger.info("Clone successful")
    return repo_path


def add_and_fetch_github_source_repo(target_repo_url, source_repo_url, commit_hash):
    """
    Inside the already-cloned TARGET repo, add the SOURCE repo as a remote,
    fetch it, cherry-pick the given commit, and push a new branch.
    """
    if len(commit_hash) < 7:
        raise ValueError(f"Commit hash '{commit_hash}' is too short (minimum 7 characters).")

    remote_name = 'github_remote'
    # The working directory is the TARGET repo, not the source
    repo_path = os.path.join(os.getcwd(), _repo_name(target_repo_url))

    if not os.path.isdir(repo_path):
        raise FileNotFoundError(
            f"Target repository path not found: {repo_path}. "
            "Make sure the clone step succeeded."
        )

    # Add remote if it doesn't already exist
    existing = subprocess.run(
        ["git", "remote"], cwd=repo_path,
        capture_output=True, text=True, check=True
    ).stdout.split()

    if remote_name not in existing:
        run_git(["git", "remote", "add", remote_name, source_repo_url], cwd=repo_path)
        logger.info(f"Remote added: {remote_name} -> {source_repo_url}")
    else:
        logger.info(f"Remote already exists: {remote_name}")

    run_git(["git", "fetch", remote_name], cwd=repo_path)
    logger.info("Remote fetch successful")

    cherry_pick_source_commit_hash(commit_hash, repo_path)
    push_change_to_github(remote_name, commit_hash, repo_path)


def cherry_pick_source_commit_hash(commit_hash, folder_path):
    """Cherry-pick a commit; aborts and raises on failure."""
    logger.info(f"Cherry-picking commit {commit_hash}")
    try:
        run_git(["git", "cherry-pick", commit_hash], cwd=folder_path)
        logger.info("Cherry-pick successful")
    except subprocess.CalledProcessError:
        logger.error("Cherry-pick failed, aborting.")
        subprocess.run(["git", "cherry-pick", "--abort"], cwd=folder_path, capture_output=True)
        raise


def push_change_to_github(remote_name, commit_hash, repo_path):
    """Create a new branch from HEAD and push it to origin."""
    short = commit_hash[:8]
    new_branch = f"{remote_name}_{short}"

    # Remove stale local branch if this is a re-run
    subprocess.run(
        ["git", "branch", "-D", new_branch],
        cwd=repo_path, capture_output=True
    )

    run_git(["git", "checkout", "-b", new_branch], cwd=repo_path)
    logger.info(f"Pushing branch {new_branch} to origin")
    run_git(["git", "push", "origin", f"HEAD:refs/heads/{new_branch}"], cwd=repo_path)
    logger.info("Push successful")


def run_script(entry_gtr, entry_gtb, entry_gsr, entry_gsc, run_button):
    github_target_repo = entry_gtr.get().strip()
    github_target_branch = entry_gtb.get().strip()
    github_source_repo = entry_gsr.get().strip()
    github_source_commit = entry_gsc.get().strip()

    try:
        _validate_inputs(**{
            "GitHub Target Repo": github_target_repo,
            "GitHub Target Branch": github_target_branch,
            "GitHub Source Repo": github_source_repo,
            "GitHub Source Commit Hash": github_source_commit,
        })

        if not _git_is_available():
            raise EnvironmentError("'git' executable not found on PATH.")

        clone_target_github_repo(github_target_repo, github_target_branch)
        add_and_fetch_github_source_repo(github_target_repo, github_source_repo, github_source_commit)
        messagebox.showinfo("Success", "Operation completed successfully.")
    except Exception as e:
        logger.error(f"run_script failed: {e}")
        messagebox.showerror("Error", str(e))
    finally:
        run_button.configure(state="normal", text="Run Sync")


def start_thread(entry_gtr, entry_gtb, entry_gsr, entry_gsc, run_button):
    run_button.configure(state="disabled", text="Running…")
    t = threading.Thread(
        target=run_script,
        args=(entry_gtr, entry_gtb, entry_gsr, entry_gsc, run_button),
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
    root.title("GitHub → GitHub Sync Tool")
    root.geometry("520x340")

    frame = ctk.CTkFrame(root)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    frame.grid_columnconfigure(1, weight=1)

    labels = [
        "GitHub Target Repo",
        "GitHub Target Branch",
        "GitHub Source Repo",
        "GitHub Source Commit Hash",
    ]

    entries = []
    for i, text in enumerate(labels):
        lbl = ctk.CTkLabel(frame, text=text)
        lbl.grid(row=i, column=0, padx=10, pady=10, sticky="w")

        entry = ctk.CTkEntry(frame, width=350)
        entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
        entries.append(entry)

    entry_gtr, entry_gtb, entry_gsr, entry_gsc = entries

    run_button = ctk.CTkButton(frame, text="Run Sync")
    run_button.configure(
        command=lambda: start_thread(entry_gtr, entry_gtb, entry_gsr, entry_gsc, run_button)
    )
    run_button.grid(row=5, column=1, pady=20)

    root.mainloop()


# ---------------- Entry point ----------------
if __name__ == "__main__":
    main()
