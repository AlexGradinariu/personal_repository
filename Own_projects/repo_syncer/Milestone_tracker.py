import os
import json
import pandas as pd
import logging
import subprocess

# ---------------- Logging ----------------
log_file = os.path.join(os.getcwd(), "Milestone_tracker.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ── Constants ──────────────────────────────────────────────────────────────────
COMMIT_LOOKBACK = input("Enter number of commits to look back: ")        # how many commits to inspect for milestone changes
EXCEL_FILE      = "Milestone_changes.xlsx"

def get_repo_root(project_name):
    local_path = os.path.join(os.getcwd(), project_name.strip().split('/')[-1])
    return local_path


def clone_gerrit_repo(project_name, branch_name):
    current_dir = os.getcwd()
    server      = 'buic-scm'
    port        = '29418'
    ssh_url     = f"ssh://{server}:{port}/{project_name}"
    local_path  = os.path.join(current_dir, project_name.strip().split('/')[-1])

    if os.path.exists(local_path):
        logger.warning(f"Repository already exists at '{local_path}' — pulling latest changes...")
        try:
            run_git(["git", "fetch", "--all"], cwd=local_path)
            run_git(["git", "reset", "--hard", f"origin/{branch_name}"], cwd=local_path)
            logger.info("Pull succeeded — repo is up to date.")
        except subprocess.CalledProcessError:
            logger.warning("Could not update existing repo — proceeding with cached state.")
        return local_path

    scp_command = [
        "scp", "-p", "-O", "-P", port,
        f"{server}:hooks/commit-msg",
        f"{local_path}/.git/hooks"
    ]

    try:
        # FIX: was referencing undefined `project` — corrected to `project_name`
        logger.info(f"Cloning project -> {project_name} with branch -> {branch_name}...")
        run_git(["git", "clone", "-b", branch_name, ssh_url, local_path],
                cwd=current_dir)
        logger.info("Cloning succeeded.")

        logger.info("SCP for commit-msg hook...")
        run_git(scp_command, cwd=current_dir)
        logger.info("SCP succeeded.")

        return local_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during clone or scp: {e}")
        logger.error(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        raise


def run_git(cmd, cwd):
    """Execute a git/shell command; raises CalledProcessError on failure."""
    cmd_str = " ".join(str(c) for c in cmd)   # safe join even if ints sneak in
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"   # don't crash on exotic author names / paths
        )
        if result.stdout:
            logger.debug(result.stdout.strip())
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {cmd_str}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        raise


def get_commits_for_json_file(json_file, root_repo_path, count=COMMIT_LOOKBACK):
    """Return the last *count* commit SHAs that touched *json_file*."""
    commits = run_git(
        ["git", "log", "-n", str(count), "--pretty=format:%H", "--", json_file],
        cwd=root_repo_path
    )
    logger.info(f"Last {count} commits for '{json_file}':")
    logger.info(commits)
    return [c for c in commits.splitlines() if c.strip()]   # filter blank lines


def get_commit_info(commit, root_repo_path):
    """Return (author, date) for a commit; returns (None, None) on failure."""
    try:
        info = run_git(
            ["git", "log", "-1", "--format=%an|%ad", commit],
            cwd=root_repo_path
        ).strip()
    except subprocess.CalledProcessError:
        logger.warning(f"Could not retrieve info for commit {commit[:10]}.")
        return None, None

    if "|" in info:
        author, date = info.split("|", 1)
        return author.strip(), date.strip()
    return None, None


def check_milestone_changes(json_file, root_repo_path):
    """
    Walk commits oldest→newest and record every commit where the mainline
    MILESTONE value changed.

    Returns:
        dict { "Milestone changed from X → Y": [[author, date, commit], ...] }
    """
    dictionary_of_changes = {}
    commits = get_commits_for_json_file(json_file, root_repo_path)

    if not commits:
        logger.warning("No commits found for the given file — nothing to analyse.")
        return dictionary_of_changes

    last_milestone = None

    for commit in reversed(commits):   # oldest first
        try:
            json_file_content = run_git(
                ["git", "show", f"{commit}:{json_file}"],
                cwd=root_repo_path
            )
            data = json.loads(json_file_content)   # may raise json.JSONDecodeError
        except subprocess.CalledProcessError as e:
            logger.error(f"git show failed for commit {commit[:10]}: {e}")
            continue
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in commit {commit[:10]}: {e}")
            continue

        for version in data.get("versions", []):
            if version.get("LINE") == "mainline":
                current_milestone = version.get("MILESTONE")
                if current_milestone is None:
                    logger.warning(f"MILESTONE key missing in commit {commit[:10]} — skipping.")
                    continue
                if last_milestone is not None and current_milestone != last_milestone:
                    author, date = get_commit_info(commit, root_repo_path)
                    text_content = f"Milestone changed from {last_milestone} → {current_milestone}"
                    dictionary_of_changes.setdefault(text_content, []).append(
                        [author or "unknown", date or "unknown", commit]
                    )
                last_milestone = current_milestone
                break   # only one "mainline" entry per JSON — no need to keep iterating

    logger.info(f"Found {len(dictionary_of_changes)} milestone transition(s).")
    return dictionary_of_changes


def write_excel_file(dictionary_with_changes, output_path=None):
    """Write milestone changes to an Excel file with auto-fitted column widths."""
    if not dictionary_with_changes:
        logger.warning("No milestone changes to write — Excel file will not be created.")
        return

    if output_path is None:
        output_path = os.path.join(os.getcwd(), EXCEL_FILE)

    rows = []
    for milestone_change, entries in dictionary_with_changes.items():
        for entry in entries:   # each entry is [author, date, commit]
            rows.append([milestone_change] + entry)

    df = pd.DataFrame(
        rows,
        columns=["Milestone change (Mainline)", "Author", "Date of change", "Commit Hash"]
    )

    # Parse with UTC for correct cross-timezone sorting, then strip tz for Excel
    df["Date of change"] = pd.to_datetime(df["Date of change"], utc=True, errors="coerce")
    df.sort_values("Date of change", ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["Date of change"] = df["Date of change"].dt.tz_localize(None)  # Excel requires tz-naive

    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Milestone Changes")

            ws = writer.sheets["Milestone Changes"]
            for col in ws.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col if cell.value is not None),
                    default=10
                )
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 80)

        logger.info(f"Excel report saved to: {output_path}")
    except OSError as e:
        logger.error(f"Failed to write Excel file '{output_path}': {e}")
        raise


if __name__ == "__main__":
    project        = 'devops/platform/core'
    branch         = 'master'
    json_proj_file = "projects/DRT16/TOOLS/Publish/project_versions.json"

    repo_root = clone_gerrit_repo(project, branch)   # use returned path directly
    if not os.path.exists(repo_root):
        logger.error(f"Repo root not found: {repo_root}")
        raise SystemExit(1)

    changes = check_milestone_changes(json_proj_file, repo_root)
    write_excel_file(changes)

