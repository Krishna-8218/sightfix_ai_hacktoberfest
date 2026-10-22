"""
SightFix AI — Demo Script

A standalone script that exercises the demo mode programmatically.
Useful for verifying the pipeline without launching the full GUI.

Usage:
    python demo_script.py
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.diagnosis_service import DiagnosisService


def main():
    print("=" * 60)
    print("  🔍 SightFix AI — Demo Pipeline")
    print("=" * 60)
    print()

    svc = DiagnosisService()

    # ── Step 1: Simulated diagnosis ───────────────────────────────
    print("📸 Step 1: Screen Capture")
    print("   (In the real app, this captures your desktop with mss)")
    print("   Using simulated screenshot of a Python ModuleNotFoundError")
    print()

    diag = svc.get_demo_diagnosis()

    print("🤖 Step 2: AI Analysis")
    print(f"   Issues found: {diag.has_issue}")
    print(f"   Number of problems: {len(diag.problems)}")
    print()

    print("📋 Step 3: Diagnosis")
    for i, p in enumerate(diag.problems, 1):
        print(f"   Problem {i}: {p.title}")
        print(f"   Evidence: {p.evidence[:80]}...")
        print(f"   Cause: {p.cause[:80]}...")
        print(f"   Confidence: {p.confidence.upper()}")
        print()
        print("   Recommended Fix:")
        for j, step in enumerate(p.solution_steps, 1):
            print(f"     {j}. {step}")
        print()
        if p.commands:
            print("   Commands:")
            for cmd in p.commands:
                print(f"     $ {cmd}")
        print()
        print(f"   Verification: {p.verification}")
    print()

    print(f"   Summary: {diag.summary}")
    print()

    # ── Step 2: Simulated verification ────────────────────────────
    print("✅ Step 4: Verification")
    ver = svc.get_demo_verification()
    print(f"   Resolved: {ver.resolved}")
    print(f"   Evidence: {ver.evidence}")
    print(f"   Explanation: {ver.explanation}")
    print()

    print("=" * 60)
    print("  ✨ Demo complete!")
    print("  Run 'python main.py' to launch the full GUI application.")
    print("=" * 60)


if __name__ == "__main__":
    main()
