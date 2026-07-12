import unittest
from pathlib import Path

from rag_query import query_knowledge_base


class RagQueryTests(unittest.TestCase):
    def test_sql_injection_query_returns_relevant_chunk(self) -> None:
        results = query_knowledge_base("SQL injection")
        self.assertTrue(results)
        text = " ".join(result["content"] for result in results)
        self.assertIn("SQL", text.upper())

    def test_secrets_query_returns_relevant_chunk(self) -> None:
        results = query_knowledge_base("hardcoded secrets")
        self.assertTrue(results)
        text = " ".join(result["content"] for result in results)
        self.assertIn("SECRET", text.upper())


if __name__ == "__main__":
    unittest.main()
