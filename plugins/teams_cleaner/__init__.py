# plugins/teams_cleaner/__init__.py
"""
Teams Transcript Cleaner Plugin

Este é um exemplo de como aquele script útil de limpeza do Teams
que estava perdido em alguma pasta vira um plugin PERMANENTE!

Agora em vez de procurar "teams_clean_v3_final_FINAL.py",
você só precisa rodar:

$ qualia process transcript.txt --plugin="teams_cleaner"

E ele sempre estará lá, com a mesma configuração que funcionou!
"""

import re
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime

from qualia.core import (
    IDocumentPlugin,
    PluginMetadata,
    PluginType,
    Document
)


class TeamsTranscriptCleaner(IDocumentPlugin):
    """
    Limpa e estrutura transcrições do Microsoft Teams
    
    Transforma aquele script perdido em funcionalidade permanente!
    """
    
    def meta(self) -> PluginMetadata:
        """Auto-descrição do plugin"""
        return PluginMetadata(
            id="teams_cleaner",
            type=PluginType.DOCUMENT,
            name="Microsoft Teams Transcript Cleaner",
            description="Limpa e estrutura transcrições exportadas do Teams",
            version="1.0.0",
            
            provides=[
                "cleaned_document",     # Documento limpo
                "document_variants",    # Variantes (moderator_only, etc)
                "speaker_map",         # Mapeamento de speakers
                "transcript_metadata", # Metadados extraídos
                "quality_report"       # Relatório de qualidade
            ],
            
            requires=[],  # Não depende de outros plugins
            
            parameters={
                "remove_timestamps": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remove timestamps do Teams"
                },
                "fix_speaker_names": {
                    "type": "boolean",
                    "default": True,
                    "description": "Normaliza nomes de speakers"
                },
                "merge_continued_speech": {
                    "type": "boolean",
                    "default": True,
                    "description": "Junta falas continuadas do mesmo speaker"
                },
                "remove_system_messages": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remove mensagens do sistema"
                },
                "create_variants": {
                    "type": "list",
                    "default": ["full", "participants_only"],
                    "options": [
                        "full",
                        "participants_only",
                        "moderator_only",
                        "no_timestamps",
                        "speaker_separated"
                    ],
                    "description": "Variantes do documento para criar"
                },
                "speaker_aliases": {
                    "type": "dict",
                    "default": {},
                    "description": "Mapeamento de aliases (ex: {'João Silva': 'João'})"
                },
                "quality_checks": {
                    "type": "list",
                    "default": ["encoding", "speaker_consistency", "timestamp_format"],
                    "options": [
                        "encoding",
                        "speaker_consistency", 
                        "timestamp_format",
                        "audio_quality_markers",
                        "interruptions"
                    ],
                    "description": "Verificações de qualidade a executar"
                }
            }
        )
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida configuração"""
        meta = self.meta()
        
        for param, value in config.items():
            if param not in meta.parameters:
                return False, f"Parâmetro desconhecido: {param}"
            
            param_schema = meta.parameters[param]
            param_type = param_schema.get("type")
            
            # Validação de tipos
            if param_type == "boolean" and not isinstance(value, bool):
                return False, f"{param} deve ser booleano"
            elif param_type == "list" and not isinstance(value, list):
                return False, f"{param} deve ser uma lista"
            elif param_type == "dict" and not isinstance(value, dict):
                return False, f"{param} deve ser um dicionário"
            
            # Validação de opções em listas
            if param_type == "list" and "options" in param_schema:
                valid_options = param_schema["options"]
                for item in value:
                    if item not in valid_options:
                        return False, f"{item} não é uma opção válida para {param}"
        
        return True, None
    
    def process(self, raw_content: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa transcrição do Teams
        
        Este é o método principal que transforma o conteúdo bruto
        """
        params = self._apply_defaults(config)
        
        # Detecta formato e extrai estrutura
        transcript_data = self._parse_teams_format(raw_content)
        
        # Aplica limpezas configuradas
        if params["remove_timestamps"]:
            transcript_data = self._remove_timestamps(transcript_data)
        
        if params["fix_speaker_names"]:
            transcript_data = self._normalize_speakers(
                transcript_data, 
                params.get("speaker_aliases", {})
            )
        
        if params["merge_continued_speech"]:
            transcript_data = self._merge_continued_speech(transcript_data)
        
        if params["remove_system_messages"]:
            transcript_data = self._remove_system_messages(transcript_data)
        
        # Cria documento limpo principal
        cleaned_text = self._rebuild_transcript(transcript_data)
        
        # Executa verificações de qualidade
        quality_report = self._run_quality_checks(
            transcript_data, 
            params["quality_checks"]
        )
        
        # Cria variantes solicitadas
        variants = self._create_variants(
            transcript_data,
            params["create_variants"]
        )
        
        # Extrai metadados
        metadata = self._extract_metadata(transcript_data)
        
        # Monta resultado completo
        return {
            "cleaned_document": cleaned_text,
            "document_variants": variants,
            "speaker_map": self._build_speaker_map(transcript_data),
            "transcript_metadata": metadata,
            "quality_report": quality_report,
            "processing_params": params,
            "original_length": len(raw_content),
            "cleaned_length": len(cleaned_text)
        }
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores default"""
        meta = self.meta()
        params = {}
        
        for param_name, param_schema in meta.parameters.items():
            if param_name in config:
                params[param_name] = config[param_name]
            else:
                params[param_name] = param_schema.get("default")
        
        return params
    
    def _parse_teams_format(self, raw_content: str) -> List[Dict[str, Any]]:
        """
        Parseia formato típico do Teams
        
        Formato esperado:
        [timestamp] Speaker Name: Text
        """
        lines = raw_content.strip().split('\n')
        transcript_data = []
        
        # Patterns comuns no Teams
        patterns = [
            # [00:00:00] João Silva: Texto
            r'\[(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)',
            # 00:00:00 João Silva: Texto
            r'(\d{2}:\d{2}:\d{2})\s*([^:]+):\s*(.*)',
            # João Silva (00:00:00): Texto
            r'([^(]+)\s*\((\d{2}:\d{2}:\d{2})\):\s*(.*)',
        ]
        
        current_entry = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    # Salva entrada anterior se existir
                    if current_entry:
                        transcript_data.append(current_entry)
                    
                    # Cria nova entrada
                    groups = match.groups()
                    if len(groups) == 3:
                        timestamp, speaker, text = groups
                    else:
                        # Ajusta ordem se necessário
                        speaker, timestamp, text = groups
                    
                    current_entry = {
                        'timestamp': timestamp,
                        'speaker': speaker.strip(),
                        'text': text.strip(),
                        'original_line': line
                    }
                    matched = True
                    break
            
            if not matched and current_entry:
                # Continuação da fala anterior
                current_entry['text'] += ' ' + line
        
        # Adiciona última entrada
        if current_entry:
            transcript_data.append(current_entry)
        
        return transcript_data
    
    def _remove_timestamps(self, transcript_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove timestamps mantendo a estrutura"""
        for entry in transcript_data:
            entry['timestamp'] = None
        return transcript_data
    
    def _normalize_speakers(self, 
                           transcript_data: List[Dict[str, Any]], 
                           aliases: Dict[str, str]) -> List[Dict[str, Any]]:
        """Normaliza nomes de speakers"""
        # Primeiro, aplica aliases explícitos
        for entry in transcript_data:
            speaker = entry['speaker']
            if speaker in aliases:
                entry['speaker'] = aliases[speaker]
                entry['original_speaker'] = speaker
        
        # Depois, tenta detectar variações do mesmo nome
        speaker_variations = {}
        
        for entry in transcript_data:
            speaker = entry['speaker']
            normalized = self._normalize_name(speaker)
            
            if normalized not in speaker_variations:
                speaker_variations[normalized] = []
            speaker_variations[normalized].append(speaker)
        
        # Cria mapeamento de normalização
        normalization_map = {}
        for normalized, variations in speaker_variations.items():
            if len(variations) > 1:
                # Usa a variação mais comum
                most_common = max(set(variations), key=variations.count)
                for variation in variations:
                    if variation != most_common:
                        normalization_map[variation] = most_common
        
        # Aplica normalização
        for entry in transcript_data:
            speaker = entry['speaker']
            if speaker in normalization_map:
                entry['speaker'] = normalization_map[speaker]
                if 'original_speaker' not in entry:
                    entry['original_speaker'] = speaker
        
        return transcript_data
    
    def _normalize_name(self, name: str) -> str:
        """Normaliza nome para comparação"""
        # Remove títulos comuns
        titles = ['Dr.', 'Dra.', 'Prof.', 'Profa.', 'Sr.', 'Sra.']
        normalized = name
        for title in titles:
            normalized = normalized.replace(title, '')
        
        # Remove espaços extras e converte para minúsculas
        normalized = ' '.join(normalized.split()).lower()
        
        return normalized
    
    def _merge_continued_speech(self, 
                               transcript_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Junta falas continuadas do mesmo speaker"""
        if not transcript_data:
            return transcript_data
        
        merged = []
        current = transcript_data[0].copy()
        
        for entry in transcript_data[1:]:
            if entry['speaker'] == current['speaker']:
                # Mesmo speaker, junta o texto
                current['text'] += ' ' + entry['text']
                # Mantém timestamp da primeira fala
            else:
                # Speaker diferente, salva atual e começa novo
                merged.append(current)
                current = entry.copy()
        
        # Adiciona última entrada
        merged.append(current)
        
        return merged
    
    def _remove_system_messages(self, 
                               transcript_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove mensagens do sistema Teams"""
        system_patterns = [
            r'.*joined the meeting.*',
            r'.*left the meeting.*',
            r'.*started recording.*',
            r'.*stopped recording.*',
            r'.*is now presenting.*',
            r'.*stopped presenting.*',
        ]
        
        filtered = []
        for entry in transcript_data:
            is_system = False
            for pattern in system_patterns:
                if re.match(pattern, entry['text'], re.IGNORECASE):
                    is_system = True
                    break
            
            if not is_system:
                filtered.append(entry)
        
        return filtered
    
    def _rebuild_transcript(self, transcript_data: List[Dict[str, Any]]) -> str:
        """Reconstrói transcrição limpa"""
        lines = []
        
        for entry in transcript_data:
            if entry.get('timestamp'):
                line = f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}"
            else:
                line = f"{entry['speaker']}: {entry['text']}"
            lines.append(line)
        
        return '\n\n'.join(lines)
    
    def _run_quality_checks(self, 
                           transcript_data: List[Dict[str, Any]], 
                           checks: List[str]) -> Dict[str, Any]:
        """Executa verificações de qualidade"""
        report = {
            'checks_performed': checks,
            'issues': [],
            'stats': {},
            'quality_score': 100  # Começa com 100 e deduz por problemas
        }
        
        if 'encoding' in checks:
            # Verifica problemas de encoding
            encoding_issues = 0
            for entry in transcript_data:
                if '�' in entry['text'] or '???' in entry['text']:
                    encoding_issues += 1
            
            if encoding_issues > 0:
                report['issues'].append(f"Encontrados {encoding_issues} possíveis problemas de encoding")
                report['quality_score'] -= min(20, encoding_issues * 2)
            
            report['stats']['encoding_issues'] = encoding_issues
        
        if 'speaker_consistency' in checks:
            # Verifica consistência de speakers
            speakers = set(entry['speaker'] for entry in transcript_data)
            speaker_counts = {}
            for entry in transcript_data:
                speaker = entry['speaker']
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            # Detecta speakers com poucas falas (possível erro)
            rare_speakers = [s for s, count in speaker_counts.items() if count < 3]
            if rare_speakers:
                report['issues'].append(f"Speakers com poucas falas: {rare_speakers}")
                report['quality_score'] -= 10
            
            report['stats']['unique_speakers'] = len(speakers)
            report['stats']['speaker_distribution'] = speaker_counts
        
        if 'timestamp_format' in checks:
            # Verifica formato consistente de timestamps
            timestamp_formats = set()
            for entry in transcript_data:
                if entry.get('timestamp'):
                    # Detecta formato
                    if re.match(r'\d{2}:\d{2}:\d{2}', entry['timestamp']):
                        timestamp_formats.add('HH:MM:SS')
                    elif re.match(r'\d{2}:\d{2}', entry['timestamp']):
                        timestamp_formats.add('MM:SS')
                    else:
                        timestamp_formats.add('OTHER')
            
            if len(timestamp_formats) > 1:
                report['issues'].append("Formatos inconsistentes de timestamp")
                report['quality_score'] -= 15
            
            report['stats']['timestamp_formats'] = list(timestamp_formats)
        
        if 'audio_quality_markers' in checks:
            # Detecta marcadores de problemas de áudio
            quality_markers = ['[inaudível]', '[inaudible]', '???', '...', '[ruído]']
            quality_issues = 0
            
            for entry in transcript_data:
                for marker in quality_markers:
                    if marker in entry['text']:
                        quality_issues += 1
                        break
            
            if quality_issues > 0:
                percentage = (quality_issues / len(transcript_data)) * 100
                report['issues'].append(f"{quality_issues} trechos com problemas de áudio ({percentage:.1f}%)")
                report['quality_score'] -= min(30, int(percentage * 3))
            
            report['stats']['audio_quality_issues'] = quality_issues
        
        # Garante que o score não fique negativo
        report['quality_score'] = max(0, report['quality_score'])
        
        return report
    
    def _create_variants(self, 
                        transcript_data: List[Dict[str, Any]], 
                        variants: List[str]) -> Dict[str, str]:
        """Cria variantes do documento"""
        result = {}
        
        if 'full' in variants:
            result['full'] = self._rebuild_transcript(transcript_data)
        
        if 'participants_only' in variants:
            # Assume que moderador tem certas palavras-chave no nome
            moderator_keywords = ['moderator', 'moderador', 'host', 'apresentador']
            filtered = []
            
            for entry in transcript_data:
                is_moderator = any(
                    keyword in entry['speaker'].lower() 
                    for keyword in moderator_keywords
                )
                if not is_moderator:
                    filtered.append(entry)
            
            result['participants_only'] = self._rebuild_transcript(filtered)
        
        if 'moderator_only' in variants:
            moderator_keywords = ['moderator', 'moderador', 'host', 'apresentador']
            filtered = []
            
            for entry in transcript_data:
                is_moderator = any(
                    keyword in entry['speaker'].lower() 
                    for keyword in moderator_keywords
                )
                if is_moderator:
                    filtered.append(entry)
            
            result['moderator_only'] = self._rebuild_transcript(filtered)
        
        if 'no_timestamps' in variants:
            no_ts_data = [
                {**entry, 'timestamp': None} 
                for entry in transcript_data
            ]
            result['no_timestamps'] = self._rebuild_transcript(no_ts_data)
        
        if 'speaker_separated' in variants:
            # Agrupa por speaker
            by_speaker = {}
            for entry in transcript_data:
                speaker = entry['speaker']
                if speaker not in by_speaker:
                    by_speaker[speaker] = []
                by_speaker[speaker].append(entry['text'])
            
            separated_text = []
            for speaker, texts in by_speaker.items():
                separated_text.append(f"=== {speaker} ===")
                separated_text.extend(texts)
                separated_text.append("")  # Linha em branco
            
            result['speaker_separated'] = '\n'.join(separated_text)
        
        return result
    
    def _build_speaker_map(self, transcript_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Constrói mapa detalhado de speakers"""
        speaker_map = {}
        
        for i, entry in enumerate(transcript_data):
            speaker = entry['speaker']
            
            if speaker not in speaker_map:
                speaker_map[speaker] = {
                    'first_appearance': i,
                    'utterances': [],
                    'total_words': 0,
                    'original_names': set()
                }
            
            word_count = len(entry['text'].split())
            speaker_map[speaker]['utterances'].append({
                'index': i,
                'timestamp': entry.get('timestamp'),
                'word_count': word_count
            })
            speaker_map[speaker]['total_words'] += word_count
            
            if 'original_speaker' in entry:
                speaker_map[speaker]['original_names'].add(entry['original_speaker'])
        
        # Converte sets para listas para serialização
        for speaker_data in speaker_map.values():
            speaker_data['original_names'] = list(speaker_data['original_names'])
        
        return speaker_map
    
    def _extract_metadata(self, transcript_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai metadados da transcrição"""
        if not transcript_data:
            return {}
        
        # Calcula duração se tiver timestamps
        duration = None
        if transcript_data[0].get('timestamp') and transcript_data[-1].get('timestamp'):
            try:
                # Assume formato HH:MM:SS
                start_parts = transcript_data[0]['timestamp'].split(':')
                end_parts = transcript_data[-1]['timestamp'].split(':')
                
                if len(start_parts) == 3 and len(end_parts) == 3:
                    start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                    end_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
                    duration = end_seconds - start_seconds
            except:
                pass
        
        # Conta palavras e turnos
        total_words = sum(len(entry['text'].split()) for entry in transcript_data)
        speakers = list(set(entry['speaker'] for entry in transcript_data))
        
        return {
            'duration_seconds': duration,
            'duration_formatted': f"{duration // 3600:02d}:{(duration % 3600) // 60:02d}:{duration % 60:02d}" if duration else None,
            'total_utterances': len(transcript_data),
            'total_words': total_words,
            'unique_speakers': len(speakers),
            'speakers': speakers,
            'avg_words_per_utterance': total_words / len(transcript_data) if transcript_data else 0,
            'has_timestamps': any(entry.get('timestamp') for entry in transcript_data)
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Simula uma transcrição do Teams
    sample_transcript = """
[00:00:00] Sistema: Recording started
[00:00:05] João Silva: Bom dia pessoal, vamos começar nossa reunião sobre o projeto.
[00:00:12] Maria Santos: Bom dia João! Estou com os dados aqui.
[00:00:15] Maria Santos: Deixa eu compartilhar a tela...
[00:00:18] Sistema: Maria Santos is now presenting
[00:00:20] João Silva: Perfeito, Maria. Enquanto isso, gostaria de [inaudível]
[00:00:25] Pedro Oliveira: Desculpem o atraso, tive problemas com o áudio.
[00:00:30] João Silva: Sem problemas, Pedro. Maria estava mostrando os resultados.
[00:00:35] Maria Santos: Isso, como vocês podem ver no gráfico...
[00:00:40] Maria Santos: Os números mostram uma tendência interessante.
[00:00:45] Dr. João Silva: Muito bom! Isso confirma nossa hipótese.
[00:00:50] Pedro Oliveira: Concordo, mas acho que precisamos considerar [ruído]
[00:00:55] Sistema: Maria Santos stopped presenting
[00:01:00] Maria Santos: Obrigada pessoal, alguma pergunta?
"""
    
    # Cria e testa o plugin
    cleaner = TeamsTranscriptCleaner()
    
    # Configuração customizada
    config = {
        "remove_timestamps": False,  # Mantém timestamps neste teste
        "fix_speaker_names": True,
        "merge_continued_speech": True,
        "speaker_aliases": {
            "Dr. João Silva": "João Silva"  # Normaliza variação
        },
        "create_variants": ["full", "participants_only", "speaker_separated"],
        "quality_checks": ["encoding", "speaker_consistency", "audio_quality_markers"]
    }
    
    # Processa
    result = cleaner.process(sample_transcript, config)
    
    print("=== RESULTADO DO PROCESSAMENTO ===\n")
    
    print("Documento Limpo:")
    print("-" * 50)
    print(result['cleaned_document'][:500] + "...\n")
    
    print("Metadados Extraídos:")
    print(result['transcript_metadata'])
    print()
    
    print("Relatório de Qualidade:")
    print(f"Score: {result['quality_report']['quality_score']}/100")
    print(f"Problemas: {result['quality_report']['issues']}")
    print()
    
    print("Mapa de Speakers:")
    for speaker, data in result['speaker_map'].items():
        print(f"- {speaker}: {data['total_words']} palavras em {len(data['utterances'])} falas")