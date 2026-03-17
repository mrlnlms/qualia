from qualia.core import QualiaCore, PipelineConfig, PipelineStep

# Setup
core = QualiaCore()
core.discover_plugins()

# Documento
with open("transcript_teams.txt", "r") as f:
    doc = core.add_document("pipeline_test", f.read())

# Definir pipeline
pipeline = PipelineConfig(
    name="analysis_pipeline",
    steps=[
        PipelineStep("teams_cleaner", {"remove_system_messages": True}),
        PipelineStep("word_frequency", {"min_word_length": 3})
    ]
)

# Executar
print("=== Executando Pipeline ===")
results = core.execute_pipeline(pipeline, doc)

for step_name, result in results.items():
    print(f"\n{step_name}:")
    print(f"  - Keys: {list(result.keys())}")
