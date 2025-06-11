from qualia.core import QualiaCore
from pathlib import Path

# Inicializar
core = QualiaCore()
core.discover_plugins()

# Ler transcrição
with open("transcript_teams.txt", "r") as f:
    content = f.read()

# Criar documento
doc = core.add_document("teams_001", content)

# Processar com Teams Cleaner
if "teams_cleaner" in core.plugins:
    print("=== Processando com Teams Cleaner ===")
    result = core.execute_plugin("teams_cleaner", doc, {
        "remove_timestamps": False,
        "fix_speaker_names": True,
        "remove_system_messages": True
    })
    
    print("\nDocumento Limpo:")
    print("-" * 50)
    print(result["cleaned_document"])
    
    print("\nRelatório de Qualidade:")
    print(f"Score: {result['quality_report']['quality_score']}/100")
    print(f"Speakers: {result['transcript_metadata']['speakers']}")
