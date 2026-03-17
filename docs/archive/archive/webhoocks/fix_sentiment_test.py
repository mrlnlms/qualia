#!/usr/bin/env python3
"""
Corrigir o teste do sentiment no test_final_complete.py
"""

def fix_sentiment_test():
    file_path = 'test_final_complete.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # O teste está procurando por 'sentiment' mas o campo correto é 'sentiment_label'
    # Vamos corrigir a verificação
    
    # Procurar a função test_sentiment
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        # Procurar pela linha que verifica 'sentiment' in result
        if '"sentiment" in r.json().get("result", {})' in line:
            # Mudar para verificar sentiment_label ou polarity
            lines[i] = line.replace(
                '"sentiment" in r.json().get("result", {})',
                '"sentiment_label" in r.json().get("result", {})'
            )
            print(f"✅ Corrigido teste na linha {i+1}")
            modified = True
            break
    
    if not modified:
        # Tentar outro padrão
        for i, line in enumerate(lines):
            if 'return r.status_code == 200 and "sentiment"' in line:
                lines[i] = line.replace('"sentiment"', '"sentiment_label"')
                print(f"✅ Corrigido teste na linha {i+1}")
                modified = True
                break
    
    if modified:
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        print("\n✅ Arquivo de teste corrigido!")
    else:
        print("❌ Não encontrei o padrão para corrigir")
        print("\nProcurando manualmente...")
        
        # Mostrar a função test_sentiment
        in_func = False
        for i, line in enumerate(lines):
            if 'def test_sentiment' in line:
                in_func = True
            elif in_func and line.strip() and not line.startswith(' '):
                break
            elif in_func:
                print(f"{i+1}: {line}")

if __name__ == "__main__":
    fix_sentiment_test()