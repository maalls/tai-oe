#!/usr/bin/env python3
"""
Test script for action CLI - lists actions for opportunity c32c94d9-66ea-427b-8ba0-4946191f4c31
"""

import subprocess
import sys
import json
from pathlib import Path

BACK_DIR = Path(__file__).resolve().parents[3]

def run_command(cmd):
    """Run a command and return output."""
    print(f"\n{'='*100}")
    print(f"Running: {cmd}")
    print(f"{'='*100}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)
    
    return result.returncode


def main():
    """Run test queries."""
    
    opportunity_id = "c32c94d9-66ea-427b-8ba0-4946191f4c31"
    
    # List actions for the opportunity
    run_command(f"cd {BACK_DIR} && {sys.executable} -m src.command.action_cli list-actions {opportunity_id}")


if __name__ == '__main__':
    main()
