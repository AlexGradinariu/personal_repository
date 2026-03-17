# AGENTS.md - repo_syncer Guidance

## Project Overview

**repo_syncer** is a GUI-based repository synchronization tool that automates cherry-picking commits from a source GitHub repository to a target GitHub repository. The application bridges Gerrit-style workflow patterns with GitHub by providing a user-friendly interface for cross-repository commit synchronization.

## Architecture & Core Workflows

### Main Components

1. **Git Operations Layer** (`main.py` lines 24-182)
   - Isolated git command execution through `run_git()` wrapper
   - All git commands capture stdout/stderr and log them
   - Git operations return boolean success/failure for orchestration

2. **Workflow Orchestration** (`main.py` lines 68-120)
   - `clone_target_github_repo()`: Clones or verifies target repo locally
   - `add_and_fetch_github_source_repo()`: Adds source as remote and performs cherry-pick
   - `cherry_pick_source_commit_hash()`: Executes cherry-pick with automatic abort on failure
   - `push_change_to_github()`: Creates ephemeral test branch and pushes to origin

3. **GUI Layer** (`main.py` lines 123-190)
   - CustomTkinter dark-mode interface with 4 input fields
   - Threading prevents UI blocking during long-running git operations
   - Modal dialogs report success/error states

### Data Flow

```
User Input (4 fields)
  ↓
start_thread() [spawn daemon thread]
  ↓
run_script() [reads entry widgets]
  ↓
clone_target_github_repo()
  ↓
add_and_fetch_github_source_repo()
  ├→ cherry_pick_source_commit_hash()
  └→ push_change_to_github()
  ↓
messagebox (success/error)
```

## Key Patterns & Conventions

### Logging Strategy
- Dual output: console (INFO level) + append-mode file (`gerrit_sync.log` in cwd)
- All git commands logged at DEBUG level; failures at ERROR level
- Use `logger.error()` + manual `logger.error()` for subprocess exceptions (see line 55-56)

### Git Command Execution
- All git operations use `subprocess.run()` with `check=True` and `capture_output=True`
- Error handling: log stdout/stderr separately, then return `False`
- Cherry-pick failures trigger automatic `git cherry-pick --abort` (line 108)

### Thread Safety
- GUI updates happen on main thread only (entry widgets read in `run_script()`)
- Worker thread is daemon-threaded; blocks are acceptable
- No shared state between threads except entry widget reads

### Branch Naming Convention
- Test branches created as: `{remote_name}_{commit_hash_first_6_chars}` (line 114)
- Remote name is hardcoded as `'REMOTE'` (line 70)

## Critical Developer Workflows

### Running the Application
```powershell
python main.py
```
- Launches CustomTkinter GUI window (520x340px)
- Fill 4 fields: target repo URL, target branch, source repo URL, source commit hash
- Click "Run Sync" to execute (threaded)

### Testing Git Operations Directly
Uncomment lines 196-197 to test functions standalone:
```python
clone_target_github_repo("git@github-ix.int.automotive-wan.com:an-mb-athos/proj.nad.swl.app.git", "main")
add_and_fetch_github_source_repo("git@...", "f7708b73f1d9a8266b825e720b4cfe8536f24b27")
```

### Monitoring Execution
- Console output: real-time operation logs
- `gerrit_sync.log`: persistent operation history (append mode)
- Errors trigger messagebox popup AND log file entry

## Integration Points & External Dependencies

### External Packages
- **customtkinter** (3.x): Modern GUI library with dark mode support
- **subprocess** (stdlib): Git command execution
- **threading** (stdlib): Non-blocking UI operations
- **logging** (stdlib): Dual console/file logging

### Git Assumptions
- Local git CLI available in PATH
- SSH key authentication configured (URLs use `git@` format in examples)
- Repositories support SSH-style clone URLs
- Target repo must be cloneable; cherry-pick may have conflicts (triggers abort)

### Environment Assumptions
- Working directory is the project root (repos cloned relative to cwd)
- `gerrit_sync.log` written to cwd (not configurable)
- OS: Windows (implied by .idea/.venv structure), but code should work cross-platform

## Project-Specific Quirks

1. **Entry Widget Parsing** (line 130-133): `.get().strip()` removes whitespace; validate URLs before passing
2. **Currently Commented Out** (lines 138-139): The actual workflow is commented; only messagebox shows
3. **Hardcoded Remote Name**: `'REMOTE'` is not configurable; affects branch naming
4. **No Input Validation**: Empty fields or malformed URLs will fail silently in subprocess
5. **Daemon Threads**: Threads don't prevent process exit; graceful shutdown not implemented

## Code Health Notes

- **TODO**: Uncomment lines 138-139 to activate actual sync logic
- **TODO**: Add input validation for repository URLs and commit hashes
- **TODO**: Implement conflict resolution dialog for cherry-pick failures
- **Missing**: Exception handling in `run_script()` catches all exceptions but doesn't retry

