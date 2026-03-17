# qualia/core/base_plugins.py
"""
Base classes para plugins do Qualia Core.

Thread-safety: plugins são singletons. __init__ roda na main thread;
métodos de execução rodam em worker threads via asyncio.to_thread.
Carregue modelos, corpora e recursos pesados no __init__.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

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

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Implementação concreta do validate_config"""
        # Por enquanto sempre retorna True
        # TODO: implementar validação baseada em meta().parameters
        return True, None

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros"""
        meta = self.meta()
        validated = {}

        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                validated[param_name] = config[param_name]
            else:
                validated[param_name] = param_spec.get('default')

        return validated

    def _analyze_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real do analyzer - override este método"""
        raise NotImplementedError("Subclasse deve implementar _analyze_impl()")


class BaseVisualizerPlugin(IVisualizerPlugin):
    """Base class com funcionalidades comuns para visualizers.

    Thread-safety: plugins são singletons. __init__ roda na main thread;
    _render_impl roda em worker threads. Carregue recursos pesados no __init__.
    """

    def render(self, data: Dict[str, Any], config: Dict[str, Any],
               output_path: Union[str, Path]) -> Union[str, Path]:
        """Wrapper que valida e prepara antes de chamar _render_impl"""
        # Configurar matplotlib headless antes de qualquer uso
        try:
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            pass  # Plugin pode não usar matplotlib

        # Garantir que output_path é Path
        output_path = self._ensure_path(output_path)

        # Criar diretório se necessário
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Validar config
        validated_config = self._validate_config(config)

        # Validar que temos os dados necessários
        self._validate_data(data)

        # Chamar implementação real
        return self._render_impl(data, validated_config, output_path)

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Implementação concreta do validate_config"""
        try:
            # Tentar validar usando _validate_config
            self._validate_config(config)
            return True, None
        except Exception as e:
            return False, str(e)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e aplica defaults aos parâmetros"""
        meta = self.meta()
        validated = {}

        # IMPORTANTE: Aplicar defaults de TODOS os parâmetros definidos no metadata!
        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                # Valor foi fornecido, usar ele
                value = config[param_name]

                # Converter tipos se necessário
                if param_spec.get('type') == 'integer':
                    validated[param_name] = int(value)
                elif param_spec.get('type') == 'float':
                    validated[param_name] = float(value)
                elif param_spec.get('type') == 'bool':
                    if isinstance(value, str):
                        validated[param_name] = value.lower() == 'true'
                    else:
                        validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            else:
                # CRUCIAL: Aplicar valor default se não fornecido!
                if 'default' in param_spec:
                    validated[param_name] = param_spec['default']

        return validated

    def _ensure_path(self, path: Union[str, Path]) -> Path:
        """Converte para Path se necessário"""
        return Path(path) if not isinstance(path, Path) else path


    def _validate_data(self, data: Dict[str, Any]):
        """Valida que os dados têm os campos necessários"""
        meta = self.meta()
        if meta.requires:
            for required_field in meta.requires:
                if required_field not in data:
                    raise ValueError(
                        f"Visualizador '{meta.id}' requer campo '{required_field}' nos dados"
                    )

    def _render_impl(self, data: Dict[str, Any], config: Dict[str, Any],
                     output_path: Path) -> Path:
        """Implementação real do visualizer - override este método"""
        raise NotImplementedError("Subclasse deve implementar _render_impl()")


class BaseDocumentPlugin(IDocumentPlugin):
    """Base class para document processors"""

    def process(self, document: Document, config: Dict[str, Any],
                context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper que valida antes de processar"""
        validated_config = self._validate_config(config)
        return self._process_impl(document, validated_config, context)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Implementação concreta do validate_config"""
        return True, None

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Reutiliza lógica de validação"""
        meta = self.meta()
        validated = {}

        for param_name, param_spec in meta.parameters.items():
            if param_name in config:
                validated[param_name] = config[param_name]
            else:
                validated[param_name] = param_spec.get('default')

        return validated

    def _process_impl(self, document: Document, config: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação real - override este método"""
        raise NotImplementedError("Subclasse deve implementar _process_impl()")
