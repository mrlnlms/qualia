"""
ConfigurationRegistry — Gerenciamento centralizado de configurações de plugins.

Responsabilidades:
- Normalizar schemas de parâmetros (formatos legado e novo)
- Validar configurações contra schemas
- Calibrar parâmetros por tamanho de texto
- Fornecer visão consolidada para consumers (ex: CodeMarker)
"""

from typing import Dict, Any, List, Optional, Tuple


# Mapa de normalização de tipos
_TYPE_NORMALIZE = {
    "integer": "int",
    "string": "str",
    "boolean": "bool",
    "choice": "str",
    "float": "float",
    "int": "int",
    "str": "str",
    "bool": "bool",
    "list": "list",
    "dict": "dict",
}

# Limites padrão para categorias de tamanho de texto
TEXT_SIZE_THRESHOLDS = {
    "short_text": 500,    # até 500 palavras
    "medium": 5000,       # 500–5000 palavras
    # acima de 5000 = long_text
}


class ConfigurationRegistry:
    """
    Registry centralizado de configurações de plugins.

    Recebe plugins já descobertos pelo PluginLoader e oferece:
    - Schema normalizado de cada plugin
    - Validação de tipo, range e options
    - Resolução de config com cascata: default → text_size adjustments
    - Visão consolidada para consumers
    """

    def __init__(self, plugins: Dict[str, Any]):
        """
        Args:
            plugins: Dict[plugin_id, IPlugin] — plugins já instanciados
        """
        self._plugins = plugins
        self._schemas: Dict[str, Dict[str, Any]] = {}

        # Construir schemas normalizados na inicialização
        for plugin_id, plugin in self._plugins.items():
            meta = plugin.meta()
            self._schemas[plugin_id] = self._normalize_schema(meta)

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _normalize_schema(self, meta) -> Dict[str, Any]:
        """Normaliza schema de um plugin para formato canônico."""
        normalized_params = {}

        for param_name, param_spec in meta.parameters.items():
            normalized_params[param_name] = self._normalize_param(param_spec)

        return {
            "id": meta.id,
            "name": meta.name,
            "type": meta.type.value,
            "version": meta.version,
            "description": meta.description,
            "provides": meta.provides,
            "requires": meta.requires,
            "parameters": normalized_params,
        }

    def _normalize_param(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza um parâmetro individual."""
        raw_type = spec.get("type", "str")
        norm_type = _TYPE_NORMALIZE.get(raw_type, raw_type)

        result: Dict[str, Any] = {
            "type": norm_type,
            "description": spec.get("description", ""),
        }

        # Default
        if "default" in spec:
            result["default"] = spec["default"]

        # Range — aceita tanto range:[min,max] quanto min/max separados
        if "range" in spec:
            result["range"] = spec["range"]
        elif "min" in spec or "max" in spec:
            result["range"] = [
                spec.get("min"),
                spec.get("max"),
            ]

        # Options (para choice / str com opções)
        if "options" in spec:
            result["options"] = spec["options"]

        # Text size adjustments
        if "text_size_adjustments" in spec:
            result["text_size_adjustments"] = spec["text_size_adjustments"]

        return result

    def get_plugin_schema(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Retorna schema normalizado de um plugin."""
        return self._schemas.get(plugin_id)

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todos os schemas normalizados."""
        return dict(self._schemas)

    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def validate_config(self, plugin_id: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida configuração contra o schema do plugin.

        Returns:
            (is_valid, list_of_errors)
        """
        schema = self._schemas.get(plugin_id)
        if schema is None:
            return False, [f"Plugin '{plugin_id}' não encontrado no registry"]

        errors: List[str] = []
        params = schema["parameters"]

        for key, value in config.items():
            if key not in params:
                errors.append(f"Parâmetro desconhecido: '{key}'")
                continue

            param = params[key]
            param_type = param["type"]

            # Validar tipo
            type_error = self._validate_type(key, value, param_type)
            if type_error:
                errors.append(type_error)
                continue

            # Validar range
            if "range" in param:
                range_error = self._validate_range(key, value, param["range"])
                if range_error:
                    errors.append(range_error)

            # Validar options
            if "options" in param:
                if value not in param["options"]:
                    errors.append(
                        f"'{key}': valor '{value}' não está nas opções permitidas: {param['options']}"
                    )

        return (len(errors) == 0, errors)

    def _validate_type(self, key: str, value: Any, expected: str) -> Optional[str]:
        """Valida tipo de um valor."""
        type_map = {
            "int": (int,),
            "float": (int, float),
            "bool": (bool,),
            "str": (str,),
            "list": (list,),
            "dict": (dict,),
        }

        expected_types = type_map.get(expected)
        if expected_types is None:
            return None  # tipo desconhecido, aceita

        # bool é subclasse de int em Python — tratar separadamente
        if expected == "int" and isinstance(value, bool):
            return f"'{key}': esperado int, recebido bool"

        if not isinstance(value, expected_types):
            return f"'{key}': esperado {expected}, recebido {type(value).__name__}"

        return None

    def _validate_range(self, key: str, value: Any, range_spec: List) -> Optional[str]:
        """Valida range [min, max]."""
        if not isinstance(value, (int, float)):
            return None  # range só se aplica a numéricos

        min_val, max_val = range_spec[0], range_spec[1]

        if min_val is not None and value < min_val:
            return f"'{key}': valor {value} abaixo do mínimo {min_val}"
        if max_val is not None and value > max_val:
            return f"'{key}': valor {value} acima do máximo {max_val}"

        return None

    # ------------------------------------------------------------------
    # Text Size
    # ------------------------------------------------------------------

    @staticmethod
    def get_text_size_category(word_count: int) -> str:
        """Categoriza texto por número de palavras."""
        if word_count <= TEXT_SIZE_THRESHOLDS["short_text"]:
            return "short_text"
        elif word_count <= TEXT_SIZE_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "long_text"

    # ------------------------------------------------------------------
    # Resolução de config (cascata)
    # ------------------------------------------------------------------

    def get_config_for_plugin(
        self,
        plugin_id: str,
        text_size: str = "medium",
    ) -> Dict[str, Any]:
        """
        Resolve configuração final para um plugin.

        Cascata: default → text_size adjustments

        Args:
            plugin_id: ID do plugin
            text_size: 'short_text', 'medium', ou 'long_text'

        Returns:
            Dict com valores finais de cada parâmetro
        """
        schema = self._schemas.get(plugin_id)
        if schema is None:
            return {}

        config: Dict[str, Any] = {}
        params = schema["parameters"]

        # 1. Defaults
        for param_name, param_spec in params.items():
            if "default" in param_spec:
                config[param_name] = param_spec["default"]

        # 2. Text size adjustments
        for param_name, param_spec in params.items():
            adjustments = param_spec.get("text_size_adjustments", {})
            if text_size in adjustments:
                config[param_name] = adjustments[text_size]

        return config

    # ------------------------------------------------------------------
    # Visão consolidada
    # ------------------------------------------------------------------

    def get_consolidated_view(self) -> Dict[str, Any]:
        """
        Snapshot completo para consumers.

        Retorna schemas, text_size rules e summary.
        """
        return {
            "schemas": self._schemas,
            "text_size_rules": {
                "thresholds": TEXT_SIZE_THRESHOLDS,
                "categories": ["short_text", "medium", "long_text"],
            },
            "summary": {
                "total_plugins": len(self._schemas),
                "plugins_with_text_size": sum(
                    1 for schema in self._schemas.values()
                    if any(
                        "text_size_adjustments" in p
                        for p in schema["parameters"].values()
                    )
                ),
                "plugin_ids": list(self._schemas.keys()),
            },
        }
