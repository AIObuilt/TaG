import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.delivery.hosted.enrollment import create_enrollment_session


class TagHostedEnrollmentTests(unittest.TestCase):
    def test_managed_requires_billing_before_bootstrap(self) -> None:
        with self.assertRaisesRegex(ValueError, "billing"):
            create_enrollment_session(
                account_id="acct-1",
                mode="managed",
                billing_active=False,
                machine_label="jason-mac",
            )

    def test_self_managed_allows_bootstrap_without_billing(self) -> None:
        session = create_enrollment_session(
            account_id="acct-1",
            mode="self-managed",
            billing_active=False,
            machine_label="jason-mac",
        )
        self.assertEqual(session["mode"], "self-managed")
        self.assertEqual(session["machine_label"], "jason-mac")
        self.assertIn("bootstrap_token", session)


if __name__ == "__main__":
    unittest.main()
