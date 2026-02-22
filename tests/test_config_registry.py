"""
Testes para o ConfigurationRegistry.

Cobre: normalização de schema, validação de tipos/range/options,
resolução de config (default → text_size → profile), text_size_category,
e visão consolidada.
"""

import pytest
from unittest.mock import MagicMock
from qualia.core.config import ConfigurationRegistry, TEXT_SIZE_THRESHOLDS


# ============================================================================
# Helpers — plugins fake para testes
# ============================================================================

def _make_plugin(plugin_id, parameters, provides=None, requires=None):
    """Cria um plugin mock com meta() configurável."""
    meta = MagicMock()
    meta.id = plugin_id
    meta.name = f"Test Plugin {plugin_id}"
    meta.type = MagicMock()
    meta.type.value = "analyzer"
    meta.version = "1.0.0"
    meta.description = f"Test plugin {plugin_id}"
    meta.provides = provides or []
    meta.requires = requires or []
    meta.parameters = parameters

    plugin = MagicMock()
    plugin.meta.return_value = meta
    return plugin


def _registry_with_plugins(plugins_dict):
    """Cria registry a partir de dict {id: parameters}."""
    plugins = {}
    for pid, params in plugins_dict.items():
        plugins[pid] = _make_plugin(pid, params)
    return ConfigurationRegistry(plugins)


# ============================================================================
# Normalização de schema
# ============================================================================

class TestSchemaNormalization:
    def test_integer_normalized_to_int(self):
        reg = _registry_with_plugins({
            "p": {"count": {"type": "integer", "default": 10}}
        })
        schema = reg.get_plugin_schema("p")
        assert schema["parameters"]["count"]["type"] == "int"

    def test_string_normalized_to_str(self):
        reg = _registry_with_plugins({
            "p": {"name": {"type": "string", "default": "abc"}}
        })
        assert reg.get_plugin_schema("p")["parameters"]["name"]["type"] == "str"

    def test_boolean_normalized_to_bool(self):
        reg = _registry_with_plugins({
            "p": {"flag": {"type": "boolean", "default": True}}
        })
        assert reg.get_plugin_schema("p")["parameters"]["flag"]["type"] == "bool"

    def test_choice_normalized_to_str_with_options(self):
        reg = _registry_with_plugins({
            "p": {"lang": {"type": "choice", "options": ["pt", "en"], "default": "pt"}}
        })
        param = reg.get_plugin_schema("p")["parameters"]["lang"]
        assert param["type"] == "str"
        assert param["options"] == ["pt", "en"]

    def test_min_max_normalized_to_range(self):
        reg = _registry_with_plugins({
            "p": {"threshold": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0}}
        })
        param = reg.get_plugin_schema("p")["parameters"]["threshold"]
        assert param["range"] == [0.0, 1.0]

    def test_range_preserved_as_is(self):
        reg = _registry_with_plugins({
            "p": {"val": {"type": "int", "default": 5, "range": [1, 10]}}
        })
        assert reg.get_plugin_schema("p")["parameters"]["val"]["range"] == [1, 10]

    def test_already_normalized_types_unchanged(self):
        reg = _registry_with_plugins({
            "p": {
                "a": {"type": "int", "default": 1},
                "b": {"type": "float", "default": 1.0},
                "c": {"type": "bool", "default": False},
                "d": {"type": "str", "default": "x"},
                "e": {"type": "list", "default": []},
                "f": {"type": "dict", "default": {}},
            }
        })
        params = reg.get_plugin_schema("p")["parameters"]
        assert params["a"]["type"] == "int"
        assert params["b"]["type"] == "float"
        assert params["c"]["type"] == "bool"
        assert params["d"]["type"] == "str"
        assert params["e"]["type"] == "list"
        assert params["f"]["type"] == "dict"

    def test_get_all_schemas(self):
        reg = _registry_with_plugins({
            "a": {"x": {"type": "int", "default": 1}},
            "b": {"y": {"type": "str", "default": "z"}},
        })
        schemas = reg.get_all_schemas()
        assert set(schemas.keys()) == {"a", "b"}

    def test_unknown_plugin_returns_none(self):
        reg = _registry_with_plugins({"p": {}})
        assert reg.get_plugin_schema("nonexistent") is None

    def test_text_size_adjustments_preserved(self):
        reg = _registry_with_plugins({
            "p": {"count": {
                "type": "integer",
                "default": 50,
                "text_size_adjustments": {"short_text": 20, "long_text": 200},
            }}
        })
        param = reg.get_plugin_schema("p")["parameters"]["count"]
        assert param["text_size_adjustments"]["short_text"] == 20
        assert param["text_size_adjustments"]["long_text"] == 200


# ============================================================================
# Validação de tipos
# ============================================================================

class TestValidationType:
    def test_valid_int(self):
        reg = _registry_with_plugins({"p": {"n": {"type": "integer", "default": 1}}})
        ok, errors = reg.validate_config("p", {"n": 42})
        assert ok
        assert errors == []

    def test_invalid_int_gets_string(self):
        reg = _registry_with_plugins({"p": {"n": {"type": "integer", "default": 1}}})
        ok, errors = reg.validate_config("p", {"n": "abc"})
        assert not ok
        assert len(errors) == 1

    def test_bool_not_accepted_as_int(self):
        reg = _registry_with_plugins({"p": {"n": {"type": "integer", "default": 1}}})
        ok, errors = reg.validate_config("p", {"n": True})
        assert not ok

    def test_valid_float_accepts_int(self):
        reg = _registry_with_plugins({"p": {"f": {"type": "float", "default": 1.0}}})
        ok, _ = reg.validate_config("p", {"f": 5})
        assert ok

    def test_valid_bool(self):
        reg = _registry_with_plugins({"p": {"b": {"type": "boolean", "default": False}}})
        ok, _ = reg.validate_config("p", {"b": True})
        assert ok

    def test_invalid_bool(self):
        reg = _registry_with_plugins({"p": {"b": {"type": "boolean", "default": False}}})
        ok, errors = reg.validate_config("p", {"b": "yes"})
        assert not ok

    def test_valid_str(self):
        reg = _registry_with_plugins({"p": {"s": {"type": "string", "default": ""}}})
        ok, _ = reg.validate_config("p", {"s": "hello"})
        assert ok

    def test_valid_list(self):
        reg = _registry_with_plugins({"p": {"l": {"type": "list", "default": []}}})
        ok, _ = reg.validate_config("p", {"l": [1, 2, 3]})
        assert ok

    def test_valid_dict(self):
        reg = _registry_with_plugins({"p": {"d": {"type": "dict", "default": {}}}})
        ok, _ = reg.validate_config("p", {"d": {"a": 1}})
        assert ok

    def test_unknown_param_rejected(self):
        reg = _registry_with_plugins({"p": {"n": {"type": "integer", "default": 1}}})
        ok, errors = reg.validate_config("p", {"unknown_param": 42})
        assert not ok
        assert "desconhecido" in errors[0]

    def test_unknown_plugin_rejected(self):
        reg = _registry_with_plugins({"p": {}})
        ok, errors = reg.validate_config("missing", {"x": 1})
        assert not ok


# ============================================================================
# Validação de range
# ============================================================================

class TestValidationRange:
    def test_value_in_range(self):
        reg = _registry_with_plugins({
            "p": {"t": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0}}
        })
        ok, _ = reg.validate_config("p", {"t": 0.7})
        assert ok

    def test_value_below_min(self):
        reg = _registry_with_plugins({
            "p": {"t": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0}}
        })
        ok, errors = reg.validate_config("p", {"t": -0.1})
        assert not ok
        assert "abaixo" in errors[0]

    def test_value_above_max(self):
        reg = _registry_with_plugins({
            "p": {"t": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0}}
        })
        ok, errors = reg.validate_config("p", {"t": 1.5})
        assert not ok
        assert "acima" in errors[0]

    def test_range_format_accepted(self):
        reg = _registry_with_plugins({
            "p": {"n": {"type": "int", "default": 5, "range": [1, 10]}}
        })
        ok, _ = reg.validate_config("p", {"n": 5})
        assert ok
        ok2, errors = reg.validate_config("p", {"n": 15})
        assert not ok2


# ============================================================================
# Validação de options
# ============================================================================

class TestValidationOptions:
    def test_valid_option(self):
        reg = _registry_with_plugins({
            "p": {"lang": {"type": "choice", "options": ["pt", "en"], "default": "pt"}}
        })
        ok, _ = reg.validate_config("p", {"lang": "pt"})
        assert ok

    def test_invalid_option(self):
        reg = _registry_with_plugins({
            "p": {"lang": {"type": "choice", "options": ["pt", "en"], "default": "pt"}}
        })
        ok, errors = reg.validate_config("p", {"lang": "fr"})
        assert not ok
        assert "opções permitidas" in errors[0]

    def test_empty_config_is_valid(self):
        reg = _registry_with_plugins({
            "p": {"lang": {"type": "choice", "options": ["pt", "en"], "default": "pt"}}
        })
        ok, _ = reg.validate_config("p", {})
        assert ok


# ============================================================================
# Text size category
# ============================================================================

class TestTextSizeCategory:
    def test_short_text(self):
        assert ConfigurationRegistry.get_text_size_category(100) == "short_text"
        assert ConfigurationRegistry.get_text_size_category(500) == "short_text"

    def test_medium_text(self):
        assert ConfigurationRegistry.get_text_size_category(501) == "medium"
        assert ConfigurationRegistry.get_text_size_category(5000) == "medium"

    def test_long_text(self):
        assert ConfigurationRegistry.get_text_size_category(5001) == "long_text"
        assert ConfigurationRegistry.get_text_size_category(50000) == "long_text"

    def test_zero_words(self):
        assert ConfigurationRegistry.get_text_size_category(0) == "short_text"


# ============================================================================
# Resolução de config (cascata)
# ============================================================================

class TestConfigResolution:
    def test_defaults_only(self):
        reg = _registry_with_plugins({
            "p": {
                "n": {"type": "integer", "default": 10},
                "s": {"type": "string", "default": "hello"},
            }
        })
        config = reg.get_config_for_plugin("p")
        assert config == {"n": 10, "s": "hello"}

    def test_text_size_overrides_default(self):
        reg = _registry_with_plugins({
            "p": {"n": {
                "type": "integer",
                "default": 50,
                "text_size_adjustments": {"short_text": 20, "long_text": 200},
            }}
        })
        config = reg.get_config_for_plugin("p", text_size="short_text")
        assert config["n"] == 20

        config = reg.get_config_for_plugin("p", text_size="long_text")
        assert config["n"] == 200

    def test_medium_keeps_default(self):
        reg = _registry_with_plugins({
            "p": {"n": {
                "type": "integer",
                "default": 50,
                "text_size_adjustments": {"short_text": 20, "long_text": 200},
            }}
        })
        config = reg.get_config_for_plugin("p", text_size="medium")
        assert config["n"] == 50

    def test_unknown_plugin_returns_empty(self):
        reg = _registry_with_plugins({"p": {}})
        assert reg.get_config_for_plugin("missing") == {}


# ============================================================================
# Visão consolidada
# ============================================================================

class TestConsolidatedView:
    def test_structure(self):
        reg = _registry_with_plugins({
            "p1": {"n": {"type": "integer", "default": 1}},
            "p2": {"s": {"type": "string", "default": "x"}},
        })
        view = reg.get_consolidated_view()

        assert "schemas" in view
        assert "text_size_rules" in view
        assert "summary" in view
        assert view["summary"]["total_plugins"] == 2
        assert set(view["summary"]["plugin_ids"]) == {"p1", "p2"}

    def test_text_size_rules(self):
        reg = _registry_with_plugins({"p": {}})
        view = reg.get_consolidated_view()
        assert view["text_size_rules"]["categories"] == ["short_text", "medium", "long_text"]
        assert "thresholds" in view["text_size_rules"]

    def test_plugins_with_text_size_count(self):
        reg = _registry_with_plugins({
            "p1": {"n": {
                "type": "integer",
                "default": 50,
                "text_size_adjustments": {"short_text": 20},
            }},
            "p2": {"s": {"type": "string", "default": "x"}},
        })
        view = reg.get_consolidated_view()
        assert view["summary"]["plugins_with_text_size"] == 1

