"""Pytest integration for harness invariants I1 through I8."""
from harness.run import verify_all_invariants, run_golden_suite, run_adversarial_suite

def test_harness_invariants_pass():
    """Verify that all safety invariants I1 to I8 hold."""
    invariants, all_passed = verify_all_invariants()
    assert all_passed, f"One or more invariants failed: {[i for i in invariants if not i['passed']]}"

def test_harness_golden_benchmarks():
    """Verify golden benchmarks meet challenge thresholds."""
    metrics = run_golden_suite()
    assert metrics["catch_rate"] >= 90.0
    assert metrics["false_positive_rate"] <= 5.0

def test_harness_adversarial_defenses():
    """Verify that adversarial attacks are systematically defended."""
    adv = run_adversarial_suite()
    assert adv["defense_rate"] >= 90.0
