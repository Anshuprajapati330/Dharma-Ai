# -*- coding: utf-8 -*-
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import dharma_ai


class TranslationTests(unittest.TestCase):
    def setUp(self):
        dharma_ai.clear_translation_cache()

    def tearDown(self):
        dharma_ai.clear_translation_cache()

    @patch("dharma_ai.load_groq")
    def test_hindi_translation_does_not_switch_models_after_invalid_output(self, load_groq):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="Keep doing your duty.")
                                )
                            ]
                        )
                    )
                )
            )
        )
        load_groq.return_value = client

        with self.assertRaisesRegex(RuntimeError, "(?i)translation failed"):
            dharma_ai.translate_text("Keep doing your duty.", "hi")

        client.chat.completions.create.assert_called_once()
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["model"],
            dharma_ai.GROQ_MODEL,
        )
        self.assertIn(
            "Devanagari",
            client.chat.completions.create.call_args.kwargs["messages"][1]["content"],
        )

    @patch("dharma_ai.load_groq")
    def test_hindi_translation_reports_failure_instead_of_returning_english(self, load_groq):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="Keep doing your duty.")
                                )
                            ]
                        )
                    )
                )
            )
        )
        load_groq.return_value = client

        with self.assertRaisesRegex(RuntimeError, "(?i)translation failed"):
            dharma_ai.translate_text("Keep doing your duty.", "hi")

    @patch("dharma_ai.load_groq")
    def test_english_translation_does_not_switch_models_after_invalid_output(self, load_groq):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="अपने कर्तव्य का पालन करते रहें।")
                                )
                            ]
                        )
                    )
                )
            )
        )
        load_groq.return_value = client

        with self.assertRaisesRegex(RuntimeError, "(?i)translation failed"):
            dharma_ai.translate_text("अपने कर्तव्य का पालन करते रहें।", "en")

        client.chat.completions.create.assert_called_once()
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["model"],
            dharma_ai.GROQ_MODEL,
        )
        self.assertIn(
            "English prose",
            client.chat.completions.create.call_args.kwargs["messages"][1]["content"],
        )

    @patch("dharma_ai.load_groq")
    def test_english_translation_reports_failure_instead_of_returning_hindi(self, load_groq):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="अपने कर्तव्य का पालन करते रहें।")
                                )
                            ]
                        )
                    )
                )
            )
        )
        load_groq.return_value = client

        with self.assertRaisesRegex(RuntimeError, "(?i)translation failed"):
            dharma_ai.translate_text("अपने कर्तव्य का पालन करते रहें।", "en")

    def test_translation_rejects_unsupported_target_language(self):
        with self.assertRaisesRegex(ValueError, "Target language"):
            dharma_ai.translate_text("Keep doing your duty.", "fr")

    @patch("dharma_ai.load_groq")
    def test_translation_uses_cache_on_subsequent_calls(self, load_groq):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="अपना कर्तव्य करते रहें।")
                                )
                            ]
                        )
                    )
                )
            )
        )
        load_groq.return_value = client

        first = dharma_ai.translate_text("Keep doing your duty.", "hi")
        second = dharma_ai.translate_text("Keep doing your duty.", "hi")

        self.assertEqual(first, "अपना कर्तव्य करते रहें।")
        self.assertEqual(second, "अपना कर्तव्य करते रहें।")
        self.assertEqual(client.chat.completions.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
