# qualia/core/cache.py
"""
Gerenciamento de cache com LRU e TTL para resultados de análises.
"""

import hashlib
import json
import pickle
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class CacheManager:
    """Gerencia cache de resultados de análises com LRU e TTL.

    Thread-safe: todas as operações são protegidas por lock.
    Pickle: usado para persistência local. Seguro para uso local-first;
    não expor cache_dir a fontes não confiáveis.

    Args:
        cache_dir: diretório para arquivos .pkl
        max_size: máximo de entradas (0 = sem limite)
        ttl: time-to-live em segundos (0 = sem expiração)
    """

    def __init__(self, cache_dir: Path, max_size: int = 0, ttl: int = 0):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.ttl = ttl
        self._lock = threading.Lock()
        # Ordem de acesso (mais recente no final) — OrderedDict para O(1) em move/delete
        self._access_order: OrderedDict = OrderedDict()
        # Timestamps de criação
        self._timestamps: Dict[str, float] = {}
        # Contadores
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        # Índice reverso para invalidação seletiva
        self._doc_index: Dict[str, set] = {}
        self._plugin_index: Dict[str, set] = {}
        # Forward mapping: cache_key → (doc_id, plugin_id) para O(1) em _remove_entry
        self._key_metadata: Dict[str, Tuple[str, str]] = {}
        # Reconstruir índices de entradas em disco (sobrevive a restart)
        self._rebuild_index()

    @property
    def _index_file(self) -> Path:
        return self.cache_dir / ".cache_index.json"

    def _rebuild_index(self) -> None:
        """Reconstruir índices reversos a partir do arquivo de índice em disco.

        Sem isso, invalidate() após restart não encontra nenhuma entrada
        porque _doc_index/_plugin_index estariam vazios.
        """
        if not self._index_file.exists():
            return
        try:
            raw = json.loads(self._index_file.read_text())
            for cache_key, (doc_id, plugin_id) in raw.items():
                # Só reconstruir se o .pkl correspondente ainda existe
                if (self.cache_dir / f"{cache_key}.pkl").exists():
                    self._key_metadata[cache_key] = (doc_id, plugin_id)
                    self._doc_index.setdefault(doc_id, set()).add(cache_key)
                    self._plugin_index.setdefault(plugin_id, set()).add(cache_key)
                    self._access_order[cache_key] = None
                    self._timestamps[cache_key] = (self.cache_dir / f"{cache_key}.pkl").stat().st_mtime
        except (json.JSONDecodeError, KeyError, TypeError):
            # Índice corrompido — ignora, será reconstruído nas próximas operações
            pass

    def _save_index(self) -> None:
        """Persiste o forward mapping em disco para sobreviver a restart."""
        data = {k: list(v) for k, v in self._key_metadata.items()}
        self._index_file.write_text(json.dumps(data))

    @staticmethod
    def _canonicalize(obj: Any) -> Any:
        """Converte recursivamente para forma canônica JSON-serializável.

        set/frozenset → sorted list, Path → str, dict → sorted keys,
        demais → repr como fallback leaf.
        """
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, dict):
            return {str(k): CacheManager._canonicalize(v) for k, v in sorted(obj.items())}
        if isinstance(obj, (set, frozenset)):
            return sorted((CacheManager._canonicalize(x) for x in obj), key=str)
        if isinstance(obj, (list, tuple)):
            return [CacheManager._canonicalize(x) for x in obj]
        if isinstance(obj, Path):
            return str(obj)
        return f"{type(obj).__name__}:{obj!r}"

    def _get_cache_key(self, doc_id: str, plugin_id: str, config: Dict[str, Any]) -> str:
        """Gera chave única para cache. Canônica para tipos Python comuns."""
        canonical = self._canonicalize(config)
        config_str = json.dumps(canonical, sort_keys=True)
        content = f"{doc_id}:{plugin_id}:{config_str}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, doc_id: str, plugin_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recupera resultado do cache se existir"""
        cache_key = self._get_cache_key(doc_id, plugin_id, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        with self._lock:
            if not cache_file.exists():
                self._misses += 1
                return None

            # Reintegrar no tracking se carregado do disco (pós-restart)
            if cache_key not in self._access_order:
                self._access_order[cache_key] = None
                self._timestamps[cache_key] = cache_file.stat().st_mtime
                self._key_metadata[cache_key] = (doc_id, plugin_id)
                self._doc_index.setdefault(doc_id, set()).add(cache_key)
                self._plugin_index.setdefault(plugin_id, set()).add(cache_key)

            # Checar TTL (após reintegração — cobre também arquivos do disco)
            if self.ttl > 0 and cache_key in self._timestamps:
                age = time.time() - self._timestamps[cache_key]
                if age > self.ttl:
                    self._remove_entry(cache_key)
                    self._misses += 1
                    return None

        # File I/O fora do lock
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
        except Exception:
            with self._lock:
                self._remove_entry(cache_key)
                self._misses += 1
            return None

        with self._lock:
            if cache_key in self._access_order:
                self._access_order.move_to_end(cache_key, last=True)
            self._hits += 1

        return result

    def set(self, doc_id: str, plugin_id: str, config: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Armazena resultado no cache.

        Lock cobre eviction + write + tracking atomicamente.
        Pickle de resultados locais é rápido o suficiente para segurar o lock.
        """
        cache_key = self._get_cache_key(doc_id, plugin_id, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        with self._lock:
            # Evictar LRU se necessário
            if self.max_size > 0:
                is_new = cache_key not in self._access_order
                while is_new and len(self._access_order) >= self.max_size:
                    self._evict_lru()

            # File I/O + tracking sob o mesmo lock — garante atomicidade
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            self._access_order[cache_key] = None
            self._access_order.move_to_end(cache_key, last=True)
            self._timestamps[cache_key] = time.time()
            self._key_metadata[cache_key] = (doc_id, plugin_id)
            self._doc_index.setdefault(doc_id, set()).add(cache_key)
            self._plugin_index.setdefault(plugin_id, set()).add(cache_key)
            self._save_index()

    def _remove_entry(self, cache_key: str) -> None:
        """Remove uma entrada do cache (arquivo, tracking e índices). O(1) via forward mapping."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        cache_file.unlink(missing_ok=True)
        self._timestamps.pop(cache_key, None)
        self._access_order.pop(cache_key, None)
        ids = self._key_metadata.pop(cache_key, None)
        if ids:
            doc_id, plugin_id = ids
            doc_set = self._doc_index.get(doc_id)
            if doc_set:
                doc_set.discard(cache_key)
                if not doc_set:
                    del self._doc_index[doc_id]
            plugin_set = self._plugin_index.get(plugin_id)
            if plugin_set:
                plugin_set.discard(cache_key)
                if not plugin_set:
                    del self._plugin_index[plugin_id]
        self._save_index()

    def _evict_lru(self) -> None:
        """Remove a entrada menos recentemente usada"""
        if not self._access_order:
            return
        oldest_key = next(iter(self._access_order))
        self._remove_entry(oldest_key)
        self._evictions += 1

    def invalidate(self, doc_id: Optional[str] = None, plugin_id: Optional[str] = None) -> None:
        """Invalida cache por documento, plugin, ou intersecção dos dois."""
        if not doc_id and not plugin_id:
            return

        with self._lock:
            doc_keys = self._doc_index.get(doc_id, set()) if doc_id else None
            plugin_keys = self._plugin_index.get(plugin_id, set()) if plugin_id else None

            if doc_keys is not None and plugin_keys is not None:
                keys_to_remove = set(doc_keys & plugin_keys)
            elif doc_keys is not None:
                keys_to_remove = set(doc_keys)
            else:
                keys_to_remove = set(plugin_keys)

            for cache_key in keys_to_remove:
                self._remove_entry(cache_key)

    def clear(self) -> None:
        """Remove todas as entradas do cache"""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
            self._access_order.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._doc_index.clear()
            self._plugin_index.clear()
            self._key_metadata.clear()
            self._index_file.unlink(missing_ok=True)

    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            return {
                "size": len(self._access_order),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
            }
