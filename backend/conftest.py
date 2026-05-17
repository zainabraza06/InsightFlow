import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: marks tests that make real LLM API calls (slow)")
