# qualia/core/base_plugins.py
"""
Base classes para plugins do Qualia Core.

Thread-safety: plugins são singletons. __init__ roda na main thread;
métodos de execução rodam em worker threads via asyncio.to_thread.
Carregue modelos, corpora e recursos pesados no __init__.
"""

from typing import Any, Dict, Optional, Tuple

from qualia.core.interfaces import IAnalyzerPlugin, IDocumentPlugin, IVisualizerPlugin
from qualia.core.models import Document


class BaseAnalyzerPlugin(IAnalyzerPlugin):
    """Base class com funcionalidades comuns para analyzers.

    Thread-safety: plugins são singletons. __init__ roda na main thread;
    _analyze_impl roda em worker threads via asyncio.to_thread.
    Carregue modelos, corpora e recursos pesados no __init__.
    """

    # meta() NÃO é abstrato aqui - será implementado pelas subclasses
    # Removemos @abstractmethod para não conflitar

    def analyze(self, document: Document, config: Dict[str, Any],
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper que valida e prepara antes de chamar _analyze_impl"""
        validated_config = self._validate_config(config)
        return self._analyze_impl(document, validated_config, context)

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração delegando para _validate_config"""
        try:
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros, com conversão de tipos."""
        meta = self.meta()
        validated = {}

        # Rejeitar parâmetros desconhecidos (alinhado com API/ConfigRegistry)
        known_params = set(meta.parameters.keys())
        unknown = set(config.keys()) - known_params
        if unknown:
            raise ValueError(f"Parâmetro(s) desconhecido(s): {', '.join(sorted(unknown))}")

        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                value = config[param_name]
                param_type = param_spec.get('type')
                if param_type in ('integer', 'int'):
                    validated[param_name] = int(value)
                elif param_type == 'float':
                    validated[param_name] = float(value)
                elif param_type in ('boolean', 'bool'):
                    if isinstance(value, str):
                        validated[param_name] = value.lower() in ('true', '1', 'yes')
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                validated[param_name] = param_spec.get('default')

        return validated

    def _analyze_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real do analyzer - override este método"""
        raise NotImplementedError("Subclasse deve implementar _analyze_impl()")


class BaseVisualizerPlugin(IVisualizerPlugin):
    """Base class com funcionalidades comuns para visualizers.

    Plugin author implementa _render_impl(data, config) retornando:
    - plotly.Figure → BaseClass serializa pra HTML ou PNG/SVG
    - matplotlib.Figure → BaseClass serializa pra HTML ou PNG/SVG
    - str (HTML) → BaseClass envolve em dict

    O formato de saída é controlado pelo consumer via output_format no config.
    Formatos disponíveis são detectados dinamicamente baseado nas libs instaladas.
    """

    # Subclasse declara: "plotly", "matplotlib", ou "html"
    RENDER_LIB = "html"

    def render(self, data, config):
        """Valida, renderiza e serializa visualização."""
        config = dict(config)  # cópia — não muta o dict do caller
        output_format = config.pop("output_format", "html")
        validated = self._validate_config(config)
        self._validate_data(data)
        fig = self._render_impl(data, validated)
        return self._serialize(fig, output_format)

    def _render_impl(self, data, config):
        """Plugin implementa: (data, config) → figure object ou HTML str."""
        raise NotImplementedError("Subclasse deve implementar _render_impl()")

    def _serialize(self, fig, fmt):
        """Detecta tipo da figura via duck-typing e serializa pro formato pedido."""
        import base64 as b64_mod
        import io

        # HTML string pura
        if isinstance(fig, str):
            if fmt != "html":
                raise ValueError(f"Plugin retorna HTML puro; formato '{fmt}' não suportado")
            return {"html": fig}

        # plotly.Figure (duck-typed via to_html)
        if hasattr(fig, 'to_html'):
            if fmt == "html":
                return {"html": fig.to_html(include_plotlyjs="cdn", full_html=True)}
            elif fmt in ("png", "svg"):
                try:
                    img_bytes = fig.to_image(format=fmt)
                except Exception as e:
                    raise ValueError(
                        f"Formato '{fmt}' requer kaleido funcional. "
                        f"Erro: {e}. Use output_format='html' como alternativa."
                    ) from e
                return {"data": b64_mod.b64encode(img_bytes).decode(), "encoding": "base64", "format": fmt}
            else:
                raise ValueError(f"Formato '{fmt}' não suportado para plotly.Figure")

        # matplotlib.Figure (duck-typed via savefig)
        if hasattr(fig, 'savefig'):
            try:
                if fmt == "html":
                    return {"html": self._matplotlib_to_html(fig)}
                elif fmt in ("png", "svg"):
                    buf = io.BytesIO()
                    fig.savefig(buf, format=fmt, bbox_inches='tight', dpi=150)
                    return {"data": b64_mod.b64encode(buf.getvalue()).decode(), "encoding": "base64", "format": fmt}
                else:
                    raise ValueError(f"Formato '{fmt}' não suportado para matplotlib.Figure")
            finally:
                import matplotlib.pyplot as plt
                plt.close(fig)

        raise TypeError(f"Tipo de figura não suportado: {type(fig).__name__}")

    @staticmethod
    def _matplotlib_to_html(fig):
        """Converte matplotlib Figure → HTML com imagem base64 inline."""
        import base64 as b64_mod
        import io

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        b64 = b64_mod.b64encode(buf.getvalue()).decode()
        return (
            '<html><body style="margin:0;display:flex;justify-content:center">'
            f'<img src="data:image/png;base64,{b64}" style="max-width:100%">'
            '</body></html>'
        )

    @staticmethod
    def get_supported_formats(render_lib):
        """Retorna formatos disponíveis baseado na lib e nas deps instaladas."""
        if render_lib == "html":
            return ["html"]
        elif render_lib == "matplotlib":
            return ["html", "png", "svg"]
        elif render_lib == "plotly":
            formats = ["html"]
            if BaseVisualizerPlugin._kaleido_works():
                formats.extend(["png", "svg"])
            return formats
        return ["html"]

    @staticmethod
    def _kaleido_works():
        """Testa se kaleido está instalado E funcional (não só presente)."""
        try:
            import kaleido  # noqa: F401
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.to_image(format="png", width=1, height=1)
            return True
        except Exception:
            return False

    def _validate_config(self, config):
        """Valida e converte tipos dos parâmetros."""
        meta = self.meta()
        validated = {}

        # Rejeitar parâmetros desconhecidos (alinhado com API/ConfigRegistry)
        # output_format já foi extraído no render(), então não estará em config
        known_params = {k for k in meta.parameters.keys() if k != "output_format"}
        unknown = set(config.keys()) - known_params
        if unknown:
            raise ValueError(f"Parâmetro(s) desconhecido(s): {', '.join(sorted(unknown))}")

        for param_name, param_spec in meta.parameters.items():
            if param_name == "output_format":
                continue  # já extraído no render()
            if param_name in config:
                value = config[param_name]
                param_type = param_spec.get('type')
                if param_type in ('integer', 'int'):
                    validated[param_name] = int(value)
                elif param_type == 'float':
                    validated[param_name] = float(value)
                elif param_type in ('boolean', 'bool'):
                    if isinstance(value, str):
                        validated[param_name] = value.lower() in ('true', '1', 'yes')
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                validated[param_name] = param_spec.get('default')
        return validated

    def validate_config(self, config):
        """Valida config e retorna (ok, error_msg)."""
        try:
            # output_format é extraído por render() antes de _validate_config,
            # mas validate_config() pode ser chamado diretamente com config completa
            config = {k: v for k, v in config.items() if k != "output_format"}
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_data(self, data):
        """Verifica que campos requeridos existem nos dados."""
        meta = self.meta()
        if meta.requires:
            for field in meta.requires:
                if field not in data:
                    raise ValueError(
                        f"Visualizador '{meta.id}' requer campo '{field}' nos dados. "
                        f"Campos disponíveis: {list(data.keys())}"
                    )


class BaseDocumentPlugin(IDocumentPlugin):
    """Base class para document processors"""

    def process(self, document: Document, config: Dict[str, Any],
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper que valida antes de processar"""
        validated_config = self._validate_config(config)
        return self._process_impl(document, validated_config, context)

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração delegando para _validate_config"""
        try:
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros, com conversão de tipos."""
        meta = self.meta()
        validated = {}

        # Rejeitar parâmetros desconhecidos (alinhado com API/ConfigRegistry)
        known_params = set(meta.parameters.keys())
        unknown = set(config.keys()) - known_params
        if unknown:
            raise ValueError(f"Parâmetro(s) desconhecido(s): {', '.join(sorted(unknown))}")

        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                value = config[param_name]
                param_type = param_spec.get('type')
                if param_type in ('integer', 'int'):
                    validated[param_name] = int(value)
                elif param_type == 'float':
                    validated[param_name] = float(value)
                elif param_type in ('boolean', 'bool'):
                    if isinstance(value, str):
                        validated[param_name] = value.lower() in ('true', '1', 'yes')
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                validated[param_name] = param_spec.get('default')

        return validated

    def _process_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real - override este método"""
        raise NotImplementedError("Subclasse deve implementar _process_impl()")
