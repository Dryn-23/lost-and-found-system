"""Headless tests for the SQLite workflows and privacy boundary."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from controllers.claim_controller import ClaimController
from database.database import DatabaseManager, DuplicateClaimError
from models.claim import Claim
from models.person import Student


class LostFoundWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(Path(self.temp_dir.name) / "test.db")
        self.claims = ClaimController(self.db)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_claim(self, item_id: int, school_id: str = "STU-TEST-100") -> Claim:
        person = Student(
            full_name="Demo Claimant",
            school_id=school_id,
            contact_number="+63 912 345 6789",
            grade_course="Grade 10",
            section="A",
        )
        return Claim(
            item_id=item_id,
            claimant=person,
            last_seen_location="Library",
            last_seen_date=date.today().isoformat(),
            item_description="A fictional sample claim description.",
            identifying_features="A private characteristic known to the claimant.",
        )

    def test_demo_catalog_and_admin_authentication(self) -> None:
        items = self.db.list_public_items()
        self.assertEqual(len(items), 10)
        self.assertIsNotNone(self.db.authenticate_admin("admin", "admin123"))
        self.assertIsNone(self.db.authenticate_admin("admin", "wrong"))

    def test_public_projection_does_not_contain_private_finder_fields(self) -> None:
        public_item = self.db.list_public_items()[0]
        self.assertNotIn("finder_name", public_item)
        self.assertNotIn("finder_id", public_item)
        self.assertNotIn("storage_location", public_item)
        self.assertNotIn("private_notes", public_item)
        self.assertIn("public_description", public_item)

    def test_claim_is_pending_and_duplicate_active_claim_is_blocked(self) -> None:
        item = self.db.list_public_items()[0]
        claim_code = self.claims.submit_claim(self.make_claim(item["id"]))
        self.assertTrue(claim_code.startswith(f"CLAIM-{date.today().year}-"))
        self.assertEqual(self.db.get_public_item(item["id"])["status"], "Pending Claim")
        with self.assertRaises(DuplicateClaimError):
            self.claims.submit_claim(self.make_claim(item["id"]))

    def test_approval_and_physical_return_are_separate_transitions(self) -> None:
        item = self.db.list_public_items()[0]
        code = self.claims.submit_claim(self.make_claim(item["id"]))
        claim_row = self.db.list_claims()[0]
        self.claims.review(claim_row["id"], "Approved", "admin", "Verified in person.")
        self.assertEqual(self.db.get_admin_item(item["id"])["status"], "Claim Approved")
        self.assertIsNone(self.db.get_public_item(item["id"]))
        self.assertEqual(self.db.get_claim(claim_row["id"])["status"], "Approved")

        self.claims.mark_returned(
            claim_row["id"],
            {
                "returned_date": date.today().isoformat(),
                "returned_time": "14:20",
                "released_by": "admin",
                "claimant_name": "Demo Claimant",
                "notes": "Fictional test handover.",
            },
            "admin",
        )
        self.assertEqual(self.db.get_admin_item(item["id"])["status"], "Returned")
        self.assertEqual(self.db.get_claim(claim_row["id"])["status"], "Completed")
        self.assertEqual(self.db.list_returns()[0]["claim_code"], code)

    def test_rejection_restores_item_when_no_other_claims_are_pending(self) -> None:
        item = self.db.list_public_items()[0]
        self.claims.submit_claim(self.make_claim(item["id"]))
        claim_row = self.db.list_claims()[0]
        self.claims.review(claim_row["id"], "Rejected", "admin", "Answers did not match the item.")
        self.assertEqual(self.db.get_admin_item(item["id"])["status"], "Available")


if __name__ == "__main__":
    unittest.main()
