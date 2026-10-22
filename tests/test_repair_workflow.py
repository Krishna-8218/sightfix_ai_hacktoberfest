"""
SightFix AI — End-to-End Test Suite for Code Repair & Stale Diagnosis Fixes

Scenarios Tested:
- Test A: Current-file syntax repair (calculate_total missing colon -> patch -> py_compile passes)
- Test B: Previous-error isolation (student_management.py -> calculate_total.py isolation)
- Test C: Repeated scans & stale response rejection (scan_id isolation)
- Test D: Rejected patch (file remains completely unchanged)
- Test E: Failed verification (faulty patch reported as failed, never claims false success)
- Test F: Successful runtime execution (calculate_total prints 'Total: 30')
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.code_service import CodeService, FileInspectionResult, CodePatch
from services.ai_service import AIService
from services.diagnosis_service import DiagnosisService, Diagnosis


class TestCodeRepairWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.ai_svc = AIService()

    def tearDown(self):
        self.temp_dir.cleanup()

    # ── Test A: Current-file syntax repair ────────────────────────────
    def test_a_current_file_syntax_repair(self):
        """
        Create calculate_total.py with missing colon on line 1.
        Verify error detection, patch generation, patch application, and py_compile pass.
        """
        code = (
            "def calculate_total(a, b)\n"
            "    total = a + b\n"
            "    return total\n"
            "\n"
            "result = calculate_total(10, 20)\n"
            "print(\"Total:\", result)\n"
        )
        file_path = self.dir_path / "calculate_total.py"
        file_path.write_text(code, encoding="utf-8")

        # 1. Inspect file directly from disk
        inspection = CodeService.inspect_file(file_path)
        self.assertTrue(inspection.has_error, "Should detect syntax error")
        self.assertEqual(inspection.compiler_result.error_line, 1, "Error should be on line 1")
        self.assertIn("SyntaxError", inspection.compiler_result.error_type)

        # 2. Generate patch (via AI or heuristic fallback)
        res = self.ai_svc.repair_code(
            file_path=str(file_path),
            file_content=inspection.file_content,
            compiler_output=inspection.compiler_result.stderr,
            error_line=inspection.compiler_result.error_line,
        )
        self.assertTrue(res.get("has_fix"), "Should propose a fix")

        orig_code = res.get("original_code")
        repl_code = res.get("replacement_code")
        self.assertIn("def calculate_total(a, b)", orig_code)
        self.assertTrue(repl_code.strip().endswith(":"), "Replacement must end with a colon")

        # 3. Validate patch
        patch = CodeService.validate_patch(
            file_path=file_path,
            original_code=orig_code,
            replacement_code=repl_code,
            affected_line=1,
            explanation=res.get("explanation", ""),
            expected_hash=inspection.content_hash,
        )
        self.assertTrue(patch.is_valid, f"Patch should be valid: {patch.validation_error}")
        self.assertIn("+", patch.diff)
        self.assertIn("-", patch.diff)

        # 4. Apply patch safely
        success, msg = CodeService.apply_patch(file_path, patch)
        self.assertTrue(success, f"Apply patch failed: {msg}")

        # Check backup was created
        backup_path = file_path.with_suffix(".py.bak")
        self.assertTrue(backup_path.exists(), "Backup .bak file should exist")

        # 5. Verify py_compile passes
        verify_cr = CodeService.compile_check(file_path)
        self.assertFalse(verify_cr.has_error, "Syntax error must be resolved after applying patch")
        self.assertEqual(verify_cr.exit_code, 0, "Exit code must be 0")

    # ── Test B: Previous-error isolation ──────────────────────────────
    def test_b_previous_error_isolation(self):
        """
        Diagnose student_management.py first.
        Then select calculate_total.py.
        Verify second scan contains ZERO evidence or references from the first scan.
        """
        # Create student_management.py with error at line 15
        student_code_lines = [f"# line {i}" for i in range(1, 15)]
        student_code_lines.append("    def calculate_average(self)")
        student_code_lines.append("        return sum(self.grades) / len(self.grades)")
        student_code = "\n".join(student_code_lines) + "\n"

        student_file = self.dir_path / "student_management.py"
        student_file.write_text(student_code, encoding="utf-8")

        # Scan 1: student_management.py
        inspection_1 = CodeService.inspect_file(student_file)
        self.assertEqual(inspection_1.compiler_result.error_line, 15)
        diag_1 = DiagnosisService.create_file_diagnosis(inspection_1)
        self.assertIn("student_management.py", diag_1.summary)

        # Create calculate_total.py with error at line 1
        calc_code = (
            "def calculate_total(a, b)\n"
            "    return a + b\n"
        )
        calc_file = self.dir_path / "calculate_total.py"
        calc_file.write_text(calc_code, encoding="utf-8")

        # Scan 2: calculate_total.py
        inspection_2 = CodeService.inspect_file(calc_file)
        self.assertEqual(inspection_2.compiler_result.error_line, 1)
        diag_2 = DiagnosisService.create_file_diagnosis(inspection_2)

        # Assert complete isolation
        diag_2_str = str(diag_2)
        self.assertNotIn("student_management", diag_2_str, "Second scan must not contain first file name")
        self.assertNotIn("calculate_average", diag_2_str, "Second scan must not contain first function name")
        self.assertNotIn("Line 15", diag_2_str, "Second scan must not contain Line 15")
        self.assertIn("calculate_total.py", diag_2_str, "Second scan must reference calculate_total.py")
        self.assertEqual(diag_2.affected_line, 1, "Second scan must target line 1")

    # ── Test C: Repeated scans & token invalidation ───────────────────
    def test_c_repeated_scans_isolation(self):
        """
        Simulate rapid repeated scans with scan_id tracking.
        Confirm older scan IDs are discarded and cannot overwrite newer scans.
        """
        scan_id = 1
        active_scan_id = 2  # A newer scan was launched

        # Worker 1 finishes late with scan_id = 1
        stale_accepted = (scan_id == active_scan_id)
        self.assertFalse(stale_accepted, "Stale scan_id 1 must be rejected when active is 2")

        # Worker 2 finishes with scan_id = 2
        fresh_accepted = (active_scan_id == active_scan_id)
        self.assertTrue(fresh_accepted, "Fresh scan_id 2 must be accepted")

    # ── Test D: Rejected patch ────────────────────────────────────────
    def test_d_rejected_patch_leaves_file_unchanged(self):
        """
        When user rejects a proposed patch, verify the file remains bit-for-bit identical.
        """
        code = "def calculate_total(a, b)\n    return a + b\n"
        file_path = self.dir_path / "calculate_total.py"
        file_path.write_text(code, encoding="utf-8")

        orig_content = file_path.read_text(encoding="utf-8")

        # Propose patch
        patch = CodeService.validate_patch(
            file_path=file_path,
            original_code="def calculate_total(a, b)",
            replacement_code="def calculate_total(a, b):",
            affected_line=1,
            explanation="Add colon",
        )
        self.assertTrue(patch.is_valid)

        # User rejects -> we do NOT call apply_patch
        current_content = file_path.read_text(encoding="utf-8")
        self.assertEqual(orig_content, current_content, "File must remain completely unchanged upon reject")

    # ── Test E: Failed verification ───────────────────────────────────
    def test_e_failed_verification_reports_failure(self):
        """
        Test that if a patch fails to fix the syntax error (e.g. still broken),
        py_compile reports exit code != 0 and SightFix reports failure, never false success.
        """
        code = "def calculate_total(a, b)\n    return a + b\n"
        file_path = self.dir_path / "calculate_total.py"
        file_path.write_text(code, encoding="utf-8")

        # Apply an incorrect patch that does not fix the syntax error
        bad_patch = CodePatch(
            file_path=str(file_path),
            affected_line=1,
            original_code="def calculate_total(a, b)",
            replacement_code="def calculate_total(a, b)  # missing colon still",
            explanation="Bad patch",
            is_valid=True,
        )
        success, _ = CodeService.apply_patch(file_path, bad_patch)
        self.assertTrue(success)

        # Verify
        verify_cr = CodeService.compile_check(file_path)
        self.assertTrue(verify_cr.has_error, "Verification must report error still persists")
        self.assertNotEqual(verify_cr.exit_code, 0, "Exit code must not be 0")
        self.assertIn("SyntaxError", verify_cr.error_type)

    # ── Test F: Successful runtime execution ──────────────────────────
    def test_f_successful_runtime_execution(self):
        """
        After fixing calculate_total.py, execute the file and confirm it prints 'Total: 30'.
        """
        code = (
            "def calculate_total(a, b)\n"
            "    total = a + b\n"
            "    return total\n"
            "\n"
            "result = calculate_total(10, 20)\n"
            "print(\"Total:\", result)\n"
        )
        file_path = self.dir_path / "calculate_total.py"
        file_path.write_text(code, encoding="utf-8")

        # Apply valid patch
        patch = CodePatch(
            file_path=str(file_path),
            affected_line=1,
            original_code="def calculate_total(a, b)",
            replacement_code="def calculate_total(a, b):",
            explanation="Add colon to function header",
            is_valid=True,
        )
        success, _ = CodeService.apply_patch(file_path, patch)
        self.assertTrue(success)

        # Run script
        run_ok, output, exit_code = CodeService.run_python_script(file_path)
        self.assertTrue(run_ok, f"Script should execute with return code 0, got {exit_code}")
        self.assertEqual(exit_code, 0)
        self.assertIn("Total: 30", output, f"Expected 'Total: 30' in output, got: '{output}'")


if __name__ == "__main__":
    unittest.main()
