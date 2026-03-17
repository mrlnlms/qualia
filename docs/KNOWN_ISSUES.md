# Known Issues

## RESOLVIDO: NLTK LazyCorpusLoader não é thread-safe

**Status:** Corrigido (2026-03-16)
**Descoberto:** 2026-03-16 (test_async.py)

**O que era:** Requests concorrentes a `/analyze/word_frequency` com `remove_stopwords=True` falhavam com `'WordListCorpusReader' object has no attribute '_LazyCorpusLoader__args'`. O `LazyCorpusLoader` do NLTK não é thread-safe — quando múltiplas worker threads acessavam `stopwords.words()` antes do corpus estar carregado, ocorria race condition.

**Fix:** Warm-up dos corpora NLTK no `__init__` do plugin (`_warm_up_nltk()`). Como plugins são singletons instanciados na main thread antes de qualquer request HTTP, o `LazyCorpusLoader` resolve em contexto single-threaded. Stopwords ficam cacheadas em `_stopwords_cache` — requests subsequentes nunca tocam no lazy loader.

**Prevenção:** A convenção de thread-safety foi adicionada ao CLAUDE.md, à docstring das base classes, e ao template de criação de plugins (`tools/create_plugin.py`): carregar recursos pesados no `__init__`, nunca no método de execução.
