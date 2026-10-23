"""기사 상세 투명성 UI의 안전한 기본 안내와 출처 링크를 검사합니다."""
import unittest
from pathlib import Path

NEWS_HTML = (Path(__file__).resolve().parent.parent / "static" / "news.html")


class ArticleTransparencyTests(unittest.TestCase):
    def test_transparency_fields_exist(self):
        page = NEWS_HTML.read_text(encoding="utf-8")
        for field in ("articleAuthor", "articleCreatedAt", "articleAiDisclosure",
                      "articleParagraphSources", "articleCorrections"):
            with self.subTest(field=field):
                self.assertIn('id="' + field + '"', page)

    def test_no_invented_article_author_or_correction(self):
        page = NEWS_HTML.read_text(encoding="utf-8")
        self.assertIn("개별 작성자 기록 없음", page)
        self.assertIn("개별 AI 사용 여부는 DB에 별도로 기록되지 않았습니다", page)
        self.assertIn("정정 이력 기록 기능은 연결되지 않음", page)
        self.assertIn("developers.kakaomobility.com/guide/navi-api/start", page)
        self.assertIn('link.rel = "noopener noreferrer"', page)
        self.assertIn("displayArticleTransparency(article)", page)
