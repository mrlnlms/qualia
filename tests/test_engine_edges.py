"""Testes de edge cases do engine — ciclo de dependências e resultado None."""

import pytest
from unittest.mock import patch
from qualia.core.engine import QualiaCore
from qualia.core.models import Document


@pytest.fixture
def core():
    return QualiaCore()


@pytest.fixture
def sample_document():
    return Document(id="test-doc-1", content="texto para teste", metadata={})


def test_execute_plugin_dependency_cycle_raises_value_error(core, sample_document):
    """Ciclo de dependência deve propagar ValueError descritivo."""
    original_requires = core.registry["word_frequency"].requires
    core.registry["word_frequency"].requires = ["some_dep"]
    try:
        with patch.object(core.resolver, "resolve", side_effect=ValueError("Dependência circular detectada")):
            with pytest.raises(ValueError, match="depend"):
                core.execute_plugin("word_frequency", sample_document, {})
    finally:
        core.registry["word_frequency"].requires = original_requires


def test_execute_plugin_none_result_returns_empty_dict(core, sample_document):
    """Plugin que retorna None → warning + empty dict."""
    plugin = core.loader.get_plugin("word_frequency")
    with patch.object(plugin, "analyze", return_value=None):
        result = core.execute_plugin("word_frequency", sample_document, {})
    assert result == {}
