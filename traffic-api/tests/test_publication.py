"""F20 publication privacy and admin authorization contracts (no live database)."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main, news_database
from app.admin_auth import require_admin


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.pop(require_admin, None)
        self.client.close()

    def test_admin_publication_endpoints_require_login(self):
        self.assertIn(
            self.client.get("/api/admin/news/publications").status_code, (401, 403)
        )
        self.assertIn(
            self.client.patch(
                "/api/admin/news/publications/1", json={"status": "published"}
            ).status_code, (401, 403)
        )

    def test_admin_publication_list_and_transition(self):
        main.app.dependency_overrides[require_admin] = lambda: {"id": "test-admin"}
        with patch.object(news_database, "get_admin_publication_articles",
                          return_value=[{"id": 1, "status": "review"}]):
            result = self.client.get("/api/admin/news/publications")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["articles"][0]["status"], "review")

        with patch.object(news_database, "change_article_publication_status",
                          return_value={"article_id": 1, "old_status": "review",
                                        "status": "published"}) as changed:
            result = self.client.patch(
                "/api/admin/news/publications/1", json={"status": "published"}
            )
        self.assertEqual(result.status_code, 200)
        changed.assert_called_once_with(1, "published", "test-admin")

    def test_admin_publication_invalid_status_is_rejected(self):
        main.app.dependency_overrides[require_admin] = lambda: {"id": "test-admin"}
        result = self.client.patch(
            "/api/admin/news/publications/1", json={"status": "unknown"}
        )
        self.assertEqual(result.status_code, 422)

    def test_database_queries_hide_review_and_held(self):
        import inspect
        list_source = inspect.getsource(news_database.get_saved_news_articles)
        search_source = inspect.getsource(news_database.search_saved_news_articles)
        detail_source = inspect.getsource(news_database.get_saved_news_article)
        for source in (list_source, search_source, detail_source):
            self.assertIn("public.traffic_article_publication", source)
            self.assertIn("pub.status <> 'published'", source)

    def test_article_and_review_status_in_same_transaction(self):
        import inspect
        source = inspect.getsource(news_database.save_news_article)
        self.assertIn("INSERT INTO public.traffic_article_publication", source)
        self.assertIn("INSERT INTO public.traffic_article_publication_events", source)
        self.assertIn("ON CONFLICT (generation_id) DO NOTHING", source)
        self.assertIn("with get_database_connection() as connection:", source)
