import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import dharma_ai


class GenerationTests(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_default_fast_model_streams_response(self, load_chroma, load_groq):
        load_chroma.return_value.query.return_value = {
            "documents": [["A teaching about acting with compassion."]],
            "metadatas": [[{"source": "Bhagavad Gita", "chapter": 2, "verse": 47}]],
            "distances": [[0.2]],
        }
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="Choose compassion."))]
        )
        completions = SimpleNamespace(create=Mock(return_value=[chunk]))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        streamed = []

        with patch.object(dharma_ai, "GROQ_MODEL", "openai/gpt-oss-20b"):
            response = dharma_ai.generate_response(
                "How should I handle a disagreement?",
                on_token=streamed.append,
            )

        self.assertEqual(response, "Choose compassion.")
        self.assertEqual(streamed, ["Choose compassion."])
        self.assertEqual(
            completions.create.call_args.kwargs["model"],
            "openai/gpt-oss-20b",
        )
        self.assertEqual(
            completions.create.call_args.kwargs["max_tokens"],
            1000,
        )
        messages = completions.create.call_args.kwargs["messages"]
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertEqual(messages[-1]["content"], "How should I handle a disagreement?")
        self.assertIn("BHAGAVAD GITA WISDOM", messages[0]["content"])
        self.assertNotIn("Understanding Your Situation", messages[0]["content"])
        self.assertIn("Use Dharma and the project's knowledge base", messages[0]["content"])
        self.assertIn("do not call fear imaginary", messages[0]["content"])

    def test_configured_groq_model_is_selected(self):
        self.assertEqual(dharma_ai.GROQ_MODEL, os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))

    def test_system_prompt_applies_grounded_personal_guidance_and_safety_rules(self):
        prompt = dharma_ai._build_system_prompt(
            mode_instruction="Use a calm tone.",
            context="Sanskrit Verse: Example verse\nChapter: 2\nVerse: 47",
            is_hindi=False,
            is_follow_up=False,
            is_language_request=False,
        )

        self.assertIn("begin\nwith ONE such verse", prompt)
        self.assertIn("chapter/verse reference exactly", prompt)
        self.assertIn("simple Hindi meaning", prompt)
        self.assertIn("WHAT YOU CAN DO", prompt)
        self.assertIn("2–3 specific, actionable suggestions", prompt)
        self.assertIn("Ask no more than one focused question", prompt)
        self.assertIn("prioritize\nimmediate safety", prompt)
        self.assertIn("Never invent a source", prompt)

    def test_follow_up_prompt_does_not_repeat_the_personal_problem_template(self):
        prompt = dharma_ai._build_system_prompt(
            mode_instruction="Use a calm tone.",
            context="",
            is_hindi=False,
            is_follow_up=True,
            is_language_request=False,
        )

        self.assertIn("Do not restart the full format", prompt)
        self.assertIn("Answer only the user's latest question", prompt)

    def test_retrieval_context_deduplicates_exact_text_and_keeps_first_match(self):
        items = [
            {"doc": "A teaching about compassion.", "meta": {"source": "Gita"}, "dist": 0.1},
            {"doc": " A teaching   about compassion. ", "meta": {"source": "Other"}, "dist": 0.2},
            {"doc": "A different teaching.", "meta": {"source": "Ramayana"}, "dist": 0.3},
        ]

        unique_items = dharma_ai._deduplicate_retrieval_items(items)

        self.assertEqual(len(unique_items), 2)
        self.assertEqual(unique_items[0]["meta"]["source"], "Gita")
        self.assertEqual(unique_items[1]["doc"], "A different teaching.")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_generation_does_not_switch_models_after_configured_model_fails(
        self, load_chroma, load_groq
    ):
        load_chroma.return_value.query.return_value = {
            "documents": [["A teaching about acting with compassion."]],
            "metadatas": [[{"source": "Bhagavad Gita", "chapter": 2, "verse": 47}]],
            "distances": [[0.2]],
        }
        create = Mock(side_effect=RuntimeError("simulated provider error"))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )

        with patch.object(dharma_ai, "GROQ_MODEL", "configured/test-model"):
            with self.assertRaisesRegex(RuntimeError, "could not complete"):
                dharma_ai.generate_response("How should I act?")

        create.assert_called_once()
        self.assertEqual(
            create.call_args.kwargs["model"],
            "configured/test-model",
        )

    def test_conversation_history_is_bounded_and_excludes_duplicated_current_query(self):
        history = [
            {"role": "user", "content": "Earlier question."},
            {"role": "assistant", "content": "Earlier answer."},
            {"role": "user", "content": "Current question."},
        ]

        context = dharma_ai._prepare_conversation_history(history, "Current question.")

        self.assertEqual(
            context,
            [
                {"role": "user", "content": "Earlier question."},
                {"role": "assistant", "content": "Earlier answer."},
            ],
        )

    def test_follow_up_patterns_cover_requested_english_and_hindi_examples(self):
        follow_ups = [
            "Explain reasons.",
            "Give me an example.",
            "What if I fail anyway?",
            "Explain that in Hindi.",
            "Tell me more about the second point.",
            "I still don't understand.",
            "मुझे उदाहरण दीजिए",
            "इसे हिंदी में समझाइए",
        ]

        for query in follow_ups:
            with self.subTest(query=query):
                self.assertTrue(dharma_ai._is_contextual_follow_up(query))

    def test_explicit_language_request_overrides_preference_for_this_turn(self):
        self.assertEqual(dharma_ai._response_language("Explain that in Hindi.", "en"), "hi")
        self.assertEqual(dharma_ai._response_language("हिंदी में समझाओ", "en"), "hi")
        self.assertEqual(dharma_ai._response_language("Explain that in English.", "hi"), "en")
        self.assertEqual(dharma_ai._response_language("Give me an example.", "hi"), "hi")
        self.assertTrue(dharma_ai._is_explicit_language_request("Explain that in Hindi."))

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_new_chat_does_not_send_previous_conversation(self, load_chroma, load_groq):
        load_chroma.return_value.query.return_value = {
            "documents": [["A teaching about acting with care."]],
            "metadatas": [[{"source": "Ethics"}]],
            "distances": [[0.2]],
        }
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="A fresh response."))]
        )
        completions = SimpleNamespace(create=Mock(return_value=[chunk]))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )

        dharma_ai.generate_response(
            "What should I consider?",
            conversation_history=[],
        )

        messages = completions.create.call_args.kwargs["messages"]
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertEqual(messages[-1]["content"], "What should I consider?")
        self.assertNotIn("fear of failure", messages[0]["content"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_follow_up_uses_prior_roles_and_skips_retrieval(self, load_chroma, load_groq):
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="That helps because it makes the risk manageable."))]
        )
        completions = SimpleNamespace(create=Mock(return_value=[chunk]))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        history = [
            {"role": "user", "content": "How can I overcome fear of failure?"},
            {
                "role": "assistant",
                "content": "Start with one small action. It creates evidence that you can handle the task.",
            },
            {"role": "user", "content": "Explain reasons."},
        ]

        response = dharma_ai.generate_response(
            "Explain reasons.",
            conversation_history=history,
        )

        self.assertEqual(response, "That helps because it makes the risk manageable.")
        load_chroma.assert_called_once()
        messages = completions.create.call_args.kwargs["messages"]
        self.assertEqual(
            [message["role"] for message in messages],
            ["system", "user", "assistant", "user"],
        )
        self.assertEqual(messages[-1]["content"], "Explain reasons.")
        self.assertEqual(
            sum(message["content"] == "Explain reasons." for message in messages),
            1,
        )
        self.assertIn("Do not repeat the original answer", messages[0]["content"])
        self.assertIn("2–5 sentences", messages[0]["content"])
        self.assertIn("Start with one small action.", messages[2]["content"])
        self.assertEqual(completions.create.call_args.kwargs["max_tokens"], 600)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_generation_continues_when_model_hits_token_limit(
        self, load_chroma, load_groq
    ):
        load_chroma.return_value.query.return_value = {
            "documents": [["A teaching about acting with compassion."]],
            "metadatas": [[{"source": "Bhagavad Gita", "chapter": 2, "verse": 47}]],
            "distances": [[0.2]],
        }
        first_stream = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="A complete answer needs"),
                        finish_reason=None,
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(delta=SimpleNamespace(content=""), finish_reason="length")
                ]
            ),
        ]
        continuation_stream = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=" context and a clear conclusion."),
                        finish_reason="stop",
                    )
                ]
            )
        ]
        completions = SimpleNamespace(
            create=Mock(side_effect=[first_stream, continuation_stream])
        )
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        streamed = []

        response = dharma_ai.generate_response(
            "How should I approach this?",
            on_token=streamed.append,
        )

        self.assertEqual(response, "A complete answer needs context and a clear conclusion.")
        self.assertEqual("".join(streamed), response)
        self.assertEqual(completions.create.call_count, 2)
        continuation_messages = completions.create.call_args_list[1].kwargs["messages"]
        self.assertEqual(continuation_messages[-2]["content"], "A complete answer needs")
        self.assertIn("Do not repeat", continuation_messages[-1]["content"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_common_follow_ups_use_the_previous_exchange(self, load_chroma, load_groq):
        queries = [
            "Explain reasons.",
            "Give me an example.",
            "What if I fail anyway?",
            "Tell me more about the second point.",
            "I still don't understand.",
        ]
        response_streams = [
            [
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="A focused follow-up."))]
                )
            ]
            for _ in queries
        ]
        completions = SimpleNamespace(create=Mock(side_effect=response_streams))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        earlier_exchange = [
            {"role": "user", "content": "How can I overcome fear of failure?"},
            {
                "role": "assistant",
                "content": "First, choose one small action. Second, treat the result as information, not a verdict.",
            },
        ]

        for query in queries:
            with self.subTest(query=query):
                response = dharma_ai.generate_response(
                    query,
                    conversation_history=[
                        *earlier_exchange,
                        {"role": "user", "content": query},
                    ],
                )
                self.assertEqual(response, "A focused follow-up.")

        self.assertEqual(load_chroma.call_count, len(queries))
        self.assertEqual(completions.create.call_count, len(queries))
        for call, query in zip(completions.create.call_args_list, queries):
            messages = call.kwargs["messages"]
            self.assertEqual(messages[-1], {"role": "user", "content": query})
            self.assertIn("Second, treat the result as information", messages[-2]["content"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
    @patch("dharma_ai.load_groq")
    @patch("dharma_ai.load_chroma")
    def test_hindi_follow_up_keeps_context_and_uses_natural_hindi_guidance(
        self, load_chroma, load_groq
    ):
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="छोटा कदम डर को संभालने योग्य बनाता है।"))]
        )
        completions = SimpleNamespace(create=Mock(return_value=[chunk]))
        load_groq.return_value = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        history = [
            {"role": "user", "content": "How can I overcome fear of failure?"},
            {"role": "assistant", "content": "Start with one small action."},
            {"role": "user", "content": "Explain that in Hindi."},
        ]

        dharma_ai.generate_response(
            "Explain that in Hindi.",
            conversation_history=history,
            language="en",
        )

        load_chroma.assert_called_once()
        messages = completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[-1]["content"], "Explain that in Hindi.")
        self.assertIn("idiomatic Hindi with natural grammar", messages[0]["content"])
        self.assertIn("without adding new advice", messages[0]["content"])
        self.assertEqual(messages[2]["content"], "Start with one small action.")

    def test_follow_up_retrieval_query_includes_both_previous_turns(self):
        history = [
            {"role": "user", "content": "How can I overcome fear of failure?"},
            {"role": "assistant", "content": "Start with one small action."},
        ]

        retrieval_query = dharma_ai._build_retrieval_query("Explain reasons.", history)

        self.assertIn("How can I overcome fear of failure?", retrieval_query)
        self.assertIn("Start with one small action.", retrieval_query)
        self.assertTrue(retrieval_query.endswith("Explain reasons."))


if __name__ == "__main__":
    unittest.main()
