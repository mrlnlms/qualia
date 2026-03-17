#!/bin/bash
echo "🧪 Testando Qualia..."

echo -e "\n1. Versão:"
python -m qualia --version

echo -e "\n2. Plugins disponíveis:"
python -m qualia list

echo -e "\n3. Criando arquivo teste..."
echo "Teste rápido do Qualia framework" > teste.txt

echo -e "\n4. Analisando..."
python -m qualia analyze teste.txt -p word_frequency -o resultado.json

echo -e "\n5. Abrindo menu..."
python -m qualia menu