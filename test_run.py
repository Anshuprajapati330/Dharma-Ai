import os
import sys
from types import SimpleNamespace

# Mock the Groq client
class MockGroqClient:
    class Chat:
        class Completions:
            def create(self, **kwargs):
                # Return a simple streaming response with one chunk
                chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Here is a compassionate answer.") )])
                return [chunk]
        def __init__(self):
            self.completions = self.Completions()
    def __init__(self, *args, **kwargs):
        self.chat = self.Chat()

# Mock load_groq to return our mock client
def mock_load_groq():
    return MockGroqClient()

# Mock load_chroma to avoid DB access
class MockCollection:
    def query(self, **kwargs):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

def mock_load_chroma():
    return MockCollection()

# Inject mocks into dharma_ai module
import dharma_ai

dharma_ai.load_groq = mock_load_groq
dharma_ai.load_chroma = mock_load_chroma

# Ensure env variable exists (prevent retrieval skip logic from loading real DB)
os.environ["GROQ_API_KEY"] = "test-key"

# Sample query
response = dharma_ai.generate_response("I feel anxious about my upcoming exam.")
print("Response:", response)
