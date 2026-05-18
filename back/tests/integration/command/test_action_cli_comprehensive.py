#!/usr/bin/env python3
"""
Comprehensive test file for action CLI

This file demonstrates:
1. Listing actions for an opportunity
2. Creating actions with different schedules
3. Getting action details
4. Pausing/resuming actions
5. Manual execution
6. Viewing execution logs

Opportunity ID: c32c94d9-66ea-427b-8ba0-4946191f4c31
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import pytest

BACK_DIR = Path(__file__).resolve().parents[3]

OPPORTUNITY_ID = "c32c94d9-66ea-427b-8ba0-4946191f4c31"
USER_ID = "393be11f-807f-4f0d-bfbe-5aa93f409b48"
RUN_MANUAL_SMOKE_TESTS = os.getenv("RUN_MANUAL_SMOKE_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MANUAL_SMOKE_TESTS,
    reason="Manual smoke script; set RUN_MANUAL_SMOKE_TESTS=1 to execute against a live backend.",
)

@pytest.fixture
def action_id():
    action_id = _create_follow_up_email()
    if not action_id:
        pytest.skip("Could not create a live action for CLI smoke tests")
    return action_id

def run_cli(command: str) -> tuple[int, str]:
    """Run an action CLI command and return exit code and output."""
    full_cmd = f"cd {BACK_DIR} && {sys.executable} -m src.command.action_cli {command}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + (result.stderr if result.returncode != 0 else "")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*100}")
    print(f"TEST: {title}")
    print(f"{'='*100}\n")

def _list_actions() -> bool:
    code, output = run_cli(f"list-actions {OPPORTUNITY_ID}")
    print(output)
    return code == 0


def _create_recurring_quote() -> bool:
    code, output = run_cli(
        f"""create-action {OPPORTUNITY_ID} {USER_ID} recurring_quote monthly '{{\"day_of_month\": 1, \"time\": \"09:00\", \"timezone\": \"UTC\"}}' '{{\"template_id\": \"default\", \"days_valid\": 30}}'"""
    )
    print(output)
    return code == 0


def _create_follow_up_email() -> str | None:
    code, output = run_cli(
        f"""create-action {OPPORTUNITY_ID} {USER_ID} follow_up_email weekly '{{\"day_of_week\": 2, \"time\": \"10:00\", \"timezone\": \"UTC\"}}' '{{\"subject\": \"Follow up\", \"email_template_id\": \"follow_up_001\"}}' 12"""
    )
    print(output)
    if code != 0:
        return None
    if "Action ID:" in output:
        for line in output.split('\n'):
            if "Action ID:" in line:
                return line.split(":")[-1].strip()
    return None


def _create_recurring_invoice() -> bool:
    code, output = run_cli(
        f"""create-action {OPPORTUNITY_ID} {USER_ID} recurring_invoice daily '{{\"time\": \"08:00\", \"timezone\": \"UTC\"}}' '{{\"invoice_type\": \"standard\"}}'"""
    )
    print(output)
    return code == 0


def _get_action_details(action_id: str) -> bool:
    code, output = run_cli(f"get-action {action_id}")
    print(output)
    return code == 0


def _pause_action(action_id: str) -> bool:
    code, output = run_cli(f"pause-action {action_id}")
    print(output)
    return code == 0


def _resume_action(action_id: str) -> bool:
    code, output = run_cli(f"resume-action {action_id}")
    print(output)
    return code == 0


def _execute_action_manually(action_id: str) -> bool:
    code, output = run_cli(f"execute-action {action_id}")
    print(output)
    return code == 0


def _get_execution_logs(action_id: str) -> bool:
    code, output = run_cli(f"get-logs {action_id} 5")
    print(output)
    return code == 0


def _delete_action(action_id: str) -> bool:
    code, output = run_cli(f"delete-action {action_id}")
    print(output)
    return code == 0


def test_list_actions():
    """Test listing all actions for an opportunity."""
    print_section("List Actions for Opportunity")
    assert _list_actions()

def test_create_recurring_quote():
    """Test creating a recurring quote action."""
    print_section("Create Recurring Quote Action (Monthly on 1st at 09:00)")
    assert _create_recurring_quote()

def test_create_follow_up_email():
    """Test creating a follow-up email action."""
    print_section("Create Follow-up Email Action (Weekly on Tuesday at 10:00)")
    assert _create_follow_up_email() is not None

def test_create_recurring_invoice():
    """Test creating a recurring invoice action."""
    print_section("Create Recurring Invoice Action (Daily at 08:00)")
    assert _create_recurring_invoice()

def test_get_action_details(action_id: str):
    """Test getting details of a specific action."""
    print_section(f"Get Action Details: {action_id}")
    assert _get_action_details(action_id)

def test_pause_action(action_id: str):
    """Test pausing an action."""
    print_section(f"Pause Action: {action_id}")
    assert _pause_action(action_id)

def test_resume_action(action_id: str):
    """Test resuming a paused action."""
    print_section(f"Resume Action: {action_id}")
    assert _resume_action(action_id)

def test_execute_action_manually(action_id: str):
    """Test manually executing an action."""
    print_section(f"Manually Execute Action: {action_id}")
    assert _execute_action_manually(action_id)

def test_get_execution_logs(action_id: str):
    """Test getting execution logs for an action."""
    print_section(f"Get Execution Logs: {action_id}")
    assert _get_execution_logs(action_id)

def test_delete_action(action_id: str):
    """Test deleting an action."""
    print_section(f"Delete Action: {action_id}")
    assert _delete_action(action_id)

def main():
    """Run all tests."""
    print("\n" + "="*100)
    print("ACTION CLI COMPREHENSIVE TEST SUITE")
    print("="*100)
    print(f"Opportunity ID: {OPPORTUNITY_ID}")
    print(f"User ID: {USER_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: List existing actions
    tests_total += 1
    if _list_actions():
        tests_passed += 1
    
    # Test 2: Create recurring quote
    tests_total += 1
    if _create_recurring_quote():
        tests_passed += 1
    
    # Test 3: Create follow-up email (extract ID for later use)
    tests_total += 1
    follow_up_id = _create_follow_up_email()
    if follow_up_id:
        tests_passed += 1
    
    # Test 4: Create recurring invoice
    tests_total += 1
    if _create_recurring_invoice():
        tests_passed += 1
    
    # Test 5: List again to see all actions
    tests_total += 1
    if _list_actions():
        tests_passed += 1
    
    # If we have an action ID, test other operations
    if follow_up_id:
        # Test 6: Get action details
        tests_total += 1
        if _get_action_details(follow_up_id):
            tests_passed += 1
        
        # Test 7: Pause action
        tests_total += 1
        if _pause_action(follow_up_id):
            tests_passed += 1
        
        # Test 8: Resume action
        tests_total += 1
        if _resume_action(follow_up_id):
            tests_passed += 1
        
        # Test 9: Get execution logs (should be empty)
        tests_total += 1
        if _get_execution_logs(follow_up_id):
            tests_passed += 1
    
    # Final: List all actions one more time
    tests_total += 1
    if _list_actions():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total*100):.1f}%")
    print("="*100 + "\n")
    
    return 0 if tests_passed == tests_total else 1


if __name__ == '__main__':
    sys.exit(main())
