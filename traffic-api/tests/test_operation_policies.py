"""Pure contract tests: no external requests and no Supabase mutations."""
import unittest
from datetime import date, datetime, timezone
from app.operation_policies import (
    scheduled_slot_utc, publication_transition_allowed,
    visible_to_anonymous, safe_error_code,
)


class OperationPolicyTests(unittest.TestCase):
    def test_daily_0900_kst_converts_to_midnight_utc(self):
        self.assertEqual(
            scheduled_slot_utc(date(2026, 10, 20)),
            datetime(2026, 10, 20, tzinfo=timezone.utc),
        )

    def test_article_transitions_are_restricted(self):
        self.assertTrue(publication_transition_allowed("review", "published"))
        self.assertTrue(publication_transition_allowed("published", "held"))
        self.assertTrue(publication_transition_allowed("held", "review"))
        self.assertFalse(publication_transition_allowed("published", "review"))
        self.assertFalse(publication_transition_allowed("review", "review"))

    def test_legacy_articles_stay_public_new_reviews_private(self):
        self.assertTrue(visible_to_anonymous(None))
        self.assertTrue(visible_to_anonymous("published"))
        self.assertFalse(visible_to_anonymous("review"))
        self.assertFalse(visible_to_anonymous("held"))

    def test_untrusted_error_text_is_not_persistable(self):
        self.assertEqual(safe_error_code("timeout"), "timeout")
        self.assertEqual(safe_error_code("token=secret"), "unexpected_error")
