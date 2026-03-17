#!/bin/bash

echo "🔍 Procurando onde pipeline_config é usado como dict:"
echo ""

# Procurar por pipeline_config[ ou pipeline_config.get
grep -n "pipeline_config\[" qualia/api/__init__.py
grep -n "pipeline_config\.get" qualia/api/__init__.py

echo ""
echo "🔍 Mostrando contexto da função execute_pipeline:"
echo ""

# Mostrar a função inteira
grep -A 30 "async def execute_pipeline" qualia/api/__init__.py | grep -E "(pipeline_config|return|status|pipeline)"