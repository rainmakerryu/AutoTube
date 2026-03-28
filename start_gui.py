#!/usr/bin/env python3
"""
AutoTube Launcher - GUI wrapper for start.sh
Double-click to run, terminal window stays open.
"""

import subprocess
import os
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    start_script = os.path.join(root_dir, "start.sh")

    if not os.path.exists(start_script):
        print(f"❌ start.sh not found at {start_script}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Run start.sh in a new terminal window
    subprocess.run([
        "open",
        "-a",
        "Terminal",
        start_script
    ])

if __name__ == "__main__":
    main()
