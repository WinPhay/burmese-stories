#!/usr/bin/env python3
"""
Master Publication Builder for Burmese Stories
Compiles:
1. Web Reader (dist/site/)
2. PDF Storybooks (dist/pdf/ and dist/site/pdf/)
3. Social Cards & Telegram Posts (dist/social/)
"""

import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

def run_script(name):
    script_path = SCRIPTS_DIR / name
    print(f"\n==========================================")
    print(f"▶ Executing: {name}")
    print(f"==========================================")
    res = subprocess.run([sys.executable, str(script_path)], check=True)
    if res.returncode != 0:
        print(f"Failed to execute {name}")
        sys.exit(res.returncode)

def main():
    print("Starting Full Burmese Stories Publication Build...")
    run_script("build_site.py")
    run_script("build_pdf.py")
    run_script("build_social.py")
    print("\n==========================================")
    print("✅ Full Publication Suite Build Succeeded!")
    print("==========================================")

if __name__ == "__main__":
    main()
