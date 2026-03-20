# qualia/core/__init__.py
"""
Qualia Core - Bare Metal Framework for Qualitative Data Analysis

Fachada de re-exports — a implementação vive nos módulos internos.
"""

from qualia.core.interfaces import (
    IAnalyzerPlugin,
    IDocumentPlugin,
    IPlugin,
    IVisualizerPlugin,
    PluginMetadata,
    PluginType,
)
from qualia.core.models import Document, ExecutionContext, PipelineConfig, PipelineStep
from qualia.core.base_plugins import BaseAnalyzerPlugin, BaseDocumentPlugin, BaseVisualizerPlugin
from qualia.core.resolver import DependencyResolver
from qualia.core.cache import CacheManager
from qualia.core.loader import PluginLoader
from qualia.core.engine import QualiaCore
from qualia.core.config import ConfigurationRegistry

__all__ = [
    'QualiaCore',
    'PluginType',
    'PluginMetadata',
    'IPlugin',
    'IAnalyzerPlugin',
    'IVisualizerPlugin',
    'IDocumentPlugin',
    'BaseAnalyzerPlugin',
    'BaseVisualizerPlugin',
    'BaseDocumentPlugin',
    'ConfigurationRegistry',
    'Document',
    'DependencyResolver',
    'CacheManager',
    'PluginLoader',
    'ExecutionContext',
    'PipelineStep',
    'PipelineConfig',
]
