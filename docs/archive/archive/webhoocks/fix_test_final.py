#!/usr/bin/env python3
"""
Corrigir o teste final para verificar sentiment_label corretamente
"""

def fix_test():
    with open('test_final_complete.py', 'r') as f:
        lines = f.readlines()
    
    # Encontrar e corrigir a função test_sentiment
    for i, line in enumerate(lines):
        # O teste atual verifica "sentiment" in result, mas deveria verificar "sentiment_label"
        if 'return r.status_code == 200 and "sentiment" in r.json().get("result", {})' in line:
            # Corrigir para sentiment_label
            lines[i] = line.replace(
                '"sentiment" in r.json().get("result", {})',
                '"sentiment_label" in r.json().get("result", {})'
            )
            print(f"✅ Corrigida linha {i+1}")
            break
    
    # Salvar
    with open('test_final_complete.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ Teste corrigido!")

if __name__ == "__main__":
    fix_test()