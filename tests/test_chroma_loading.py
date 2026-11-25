import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import dharma_ai


class ChromaLoadingTests(unittest.TestCase):
    def tearDown(self):
        dharma_ai._load_chroma.cache_clear()

    @patch("dharma_ai.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("dharma_ai.chromadb.PersistentClient")
    def test_concurrent_calls_initialize_chroma_once(self, client_factory, embedding_factory):
        dharma_ai._load_chroma.cache_clear()
        collection = Mock()
        client_factory.return_value.get_or_create_collection.return_value = collection

        with ThreadPoolExecutor(max_workers=4) as executor:
            collections = list(executor.map(lambda _: dharma_ai.load_chroma(), range(4)))

        self.assertTrue(all(result is collection for result in collections))
        client_factory.assert_called_once_with(
            path=str(Path(dharma_ai.__file__).resolve().parent / "chroma_db")
        )
        embedding_factory.assert_called_once_with(model_name="all-MiniLM-L6-v2")


if __name__ == "__main__":
    unittest.main()