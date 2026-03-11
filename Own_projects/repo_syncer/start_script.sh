#!/bin/bash

echo "Prepare environment"
source "./.venv/Scripts/activate"

echo "Script starting"
python repo_syncer.py
REBUILD_EXIT_CODE=$?

echo "Script finished !"
exit $REBUILD_EXIT_CODE
