import json
import sys

def validate_json(file_path):
    try:
        with open(file_path, "r") as f:
            json.load(f)
        print("✅ JSON is valid")
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_json.py <file.json>")
    else:
        validate_json(sys.argv[1])