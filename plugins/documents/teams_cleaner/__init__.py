# plugins/teams_cleaner/__init__.py
"""
Plugin para limpeza e estruturação de transcrições do Microsoft Teams

Processa transcrições exportadas do Teams, removendo ruído e estruturando
o conteúdo para análise posterior.
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime

# MUDANÇA: Importar BaseDocumentPlugin
from qualia.core import BaseDocumentPlugin, PluginMetadata, PluginType, Document


class TeamsTranscriptCleaner(BaseDocumentPlugin):  # MUDANÇA: Herdar de Base
    """
    Limpa e estrutura transcrições do Microsoft Teams
    
    Features:
    - Remove mensagens do sistema (joined/left meeting)
    - Normaliza nomes de participantes
    - Agrupa falas consecutivas do mesmo speaker
    - Gera variantes do documento (por speaker, apenas participantes)
    - Relatório de qualidade da transcrição
    
    Exemplo de uso via CLI:
        qualia process transcript.txt -p teams_cleaner --save-as cleaned.txt
        qualia process meeting.txt -p teams_cleaner -P remove_timestamps=true
    
    Exemplo de uso via Python:
        from qualia.core import QualiaCore
        
        core = QualiaCore()
        doc = core.add_document("meeting", open("transcript.txt").read())
        
        result = core.execute_plugin("teams_cleaner", doc, {
            "remove_system_messages": True,
            "merge_consecutive": True
        })
        
        # Salvar documento limpo
        with open("cleaned.txt", "w") as f:
            f.write(result["cleaned_document"])
            
        # Ver estatísticas
        print(f"Speakers: {len(result['speakers'])}")
        print(f"Quality score: {result['quality_report']['quality_score']}/100")
    
    Formatos suportados:
    - [10:23:45] João Silva: Texto da fala
    - João Silva (10:23:45): Texto da fala  
    - João Silva: Texto da fala
    """
    
    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            id="teams_cleaner",
            name="Teams Transcript Cleaner", 
            type=PluginType.DOCUMENT,
            version="1.0.0",
            description="Limpa e estrutura transcrições exportadas do Microsoft Teams",
            provides=[
                "cleaned_document",      # Documento limpo principal
                "document_variants",     # Variantes (por speaker, etc)
                "speakers",             # Lista de participantes
                "quality_report",       # Relatório de qualidade
                "metadata"              # Metadados extraídos
            ],
            parameters={
                "remove_timestamps": {
                    "type": "boolean",
                    "default": False,
                    "description": "Remover timestamps das falas"
                },
                "remove_system_messages": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Remover mensagens do sistema (joined/left)"
                },
                "normalize_speakers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Normalizar nomes dos participantes"
                },
                "merge_consecutive": {
                    "type": "boolean",
                    "default": True,
                    "description": "Mesclar falas consecutivas do mesmo speaker"
                },
                "min_utterance_length": {
                    "type": "integer",
                    "default": 2,
                    "description": "Tamanho mínimo de fala para manter (palavras)"
                },
                "create_variants": {
                    "type": "boolean",
                    "default": True,
                    "description": "Criar variantes do documento (por speaker, etc)"
                }
            }
        )
    
    # MUDANÇA: Renomear process para _process_impl
    def _process_impl(self, document: Document, config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa e limpa a transcrição
        
        Args:
            document: Documento com a transcrição
            config: Configurações (já validadas)
            context: Contexto de execução
            
        Returns:
            Dict com documento limpo, variantes, speakers, etc.
        """
        
        original_text = document.content
        lines = original_text.split('\n')
        
        # Extrair utterances (falas)
        utterances = self._extract_utterances(lines, config)
        
        # Limpar e filtrar
        utterances = self._clean_utterances(utterances, config)
        
        # Mesclar consecutivas se configurado
        if config['merge_consecutive']:
            utterances = self._merge_consecutive_utterances(utterances)
        
        # Gerar texto limpo
        cleaned_text = self._format_utterances(utterances, config)
        
        # Extrair informações
        speakers = self._extract_speakers(utterances)
        metadata = self._extract_metadata(original_text, utterances)
        
        # Criar variantes se solicitado
        variants = {}
        if config['create_variants']:
            variants = self._create_variants(utterances, config)
        
        # Gerar relatório de qualidade
        quality_report = self._generate_quality_report(
            original_text, cleaned_text, utterances
        )
        
        return {
            "cleaned_document": cleaned_text,
            "original_length": len(original_text),
            "cleaned_length": len(cleaned_text),
            "document_variants": variants,
            "speakers": speakers,
            "metadata": metadata,
            "quality_report": quality_report,
            "utterance_count": len(utterances)
        }
    
    def _extract_utterances(self, lines: List[str], 
                           config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrai utterances (falas) das linhas da transcrição
        
        Suporta múltiplos formatos:
        - [HH:MM:SS] Speaker: Text
        - Speaker (HH:MM:SS): Text
        - Speaker: Text
        """
        utterances = []
        
        # Padrões regex para diferentes formatos
        patterns = [
            # [10:23:45] João Silva: Olá pessoal
            (r'^\[?(\d{1,2}:\d{2}:\d{2})\]?\s*([^:]+):\s*(.+)$', 
             lambda m: (m.group(2), m.group(3), m.group(1))),
            
            # João Silva (10:23:45): Olá pessoal
            (r'^([^(]+)\s*\((\d{1,2}:\d{2}:\d{2})\):\s*(.+)$',
             lambda m: (m.group(1), m.group(3), m.group(2))),
            
            # João Silva: Olá pessoal (sem timestamp)
            (r'^([^:]+):\s*(.+)$',
             lambda m: (m.group(1), m.group(2), None))
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Tentar cada padrão
            for pattern, extractor in patterns:
                match = re.match(pattern, line)
                if match:
                    speaker, text, timestamp = extractor(match)
                    
                    utterances.append({
                        'line_number': i,
                        'speaker': speaker.strip(),
                        'text': text.strip(),
                        'timestamp': timestamp
                    })
                    break
        
        return utterances
    
    def _clean_utterances(self, utterances: List[Dict[str, Any]], 
                         config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Limpa e filtra utterances baseado na configuração
        """
        cleaned = []
        
        # Indicadores de mensagens do sistema
        system_indicators = [
            'Recording Started', 'Recording Stopped',
            'Gravação Iniciada', 'Gravação Parada',
            'joined the meeting', 'left the meeting',
            'entrou na reunião', 'saiu da reunião',
            'started recording', 'stopped recording',
            'iniciou a gravação', 'parou a gravação',
            'is presenting', 'stopped presenting',
            'está apresentando', 'parou de apresentar',
            'was admitted', 'foi admitido'
        ]
        
        for utt in utterances:
            # Filtrar mensagens do sistema
            if config['remove_system_messages']:
                if any(indicator in utt['text'] for indicator in system_indicators):
                    continue
                
                # Também filtrar por speaker suspeito
                if any(sys in utt['speaker'].lower() 
                      for sys in ['teams', 'system', 'recording', 'gravação']):
                    continue
            
            # Filtrar por tamanho mínimo
            word_count = len(utt['text'].split())
            if word_count < config['min_utterance_length']:
                continue
            
            # Normalizar nome do speaker
            if config['normalize_speakers']:
                utt['speaker'] = self._normalize_speaker_name(utt['speaker'])
            
            cleaned.append(utt)
        
        return cleaned
    
    def _normalize_speaker_name(self, name: str) -> str:
        """
        Normaliza nome do participante
        
        - Remove sufixos como (Guest), (Convidado), etc
        - Padroniza capitalização
        - Remove espaços extras
        """
        # Sufixos comuns para remover
        suffixes_to_remove = [
            '(Guest)', '(Convidado)', '(External)', '(Externo)',
            '(Organizer)', '(Organizador)', '(Presenter)', '(Apresentador)',
            '[Guest]', '[Convidado]', '[External]', '[Externo]'
        ]
        
        normalized = name
        for suffix in suffixes_to_remove:
            normalized = normalized.replace(suffix, '')
        
        # Limpar espaços e capitalizar
        normalized = normalized.strip()
        
        # Capitalizar cada palavra (exceto conectivos)
        words = normalized.split()
        conectivos = {'de', 'da', 'do', 'dos', 'das', 'e'}
        
        capitalized = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in conectivos:
                capitalized.append(word.capitalize())
            else:
                capitalized.append(word.lower())
        
        return ' '.join(capitalized)
    
    def _merge_consecutive_utterances(self, 
                                     utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mescla falas consecutivas do mesmo speaker
        
        Útil quando alguém envia múltiplas mensagens seguidas
        """
        if not utterances:
            return []
        
        merged = []
        current = utterances[0].copy()
        
        for utt in utterances[1:]:
            if utt['speaker'] == current['speaker']:
                # Mesclar com a fala atual
                current['text'] += ' ' + utt['text']
                # Manter o timestamp da primeira fala
            else:
                # Adicionar a atual e começar nova
                merged.append(current)
                current = utt.copy()
        
        # Adicionar a última
        merged.append(current)
        
        return merged
    
    def _format_utterances(self, utterances: List[Dict[str, Any]], 
                          config: Dict[str, Any]) -> str:
        """
        Formata utterances em texto limpo e legível
        """
        lines = []
        
        for utt in utterances:
            # Formatar linha baseado na configuração
            if config['remove_timestamps'] or not utt.get('timestamp'):
                line = f"{utt['speaker']}: {utt['text']}"
            else:
                line = f"[{utt['timestamp']}] {utt['speaker']}: {utt['text']}"
            
            lines.append(line)
        
        # Separar com linha em branco para melhor legibilidade
        return '\n\n'.join(lines)
    
    def _extract_speakers(self, utterances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extrai informações sobre os participantes
        """
        speaker_stats = {}
        
        for utt in utterances:
            speaker = utt['speaker']
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    'name': speaker,
                    'utterance_count': 0,
                    'word_count': 0,
                    'avg_utterance_length': 0,
                    'first_appearance': utt.get('line_number', 0),
                    'timestamps': []
                }
            
            # Atualizar estatísticas
            stats = speaker_stats[speaker]
            stats['utterance_count'] += 1
            words = len(utt['text'].split())
            stats['word_count'] += words
            
            if utt.get('timestamp'):
                stats['timestamps'].append(utt['timestamp'])
        
        # Calcular médias
        for stats in speaker_stats.values():
            if stats['utterance_count'] > 0:
                stats['avg_utterance_length'] = round(
                    stats['word_count'] / stats['utterance_count'], 1
                )
        
        return list(speaker_stats.values())
    
    def _extract_metadata(self, original_text: str, 
                         utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extrai metadados da transcrição
        """
        metadata = {}
        
        # Tentar encontrar data
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
            r'(\d{2}/\d{2}/\d{4})',  # 15/01/2024
            r'(\d{2}-\d{2}-\d{4})'   # 15-01-2024
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, original_text[:500])  # Buscar no início
            if match:
                metadata['date'] = match.group(1)
                break
        
        # Duração baseada em timestamps
        if utterances and utterances[0].get('timestamp') and utterances[-1].get('timestamp'):
            metadata['start_time'] = utterances[0]['timestamp']
            metadata['end_time'] = utterances[-1]['timestamp']
            
            # Calcular duração (simplificado)
            try:
                # Parse HH:MM:SS
                start_parts = utterances[0]['timestamp'].split(':')
                end_parts = utterances[-1]['timestamp'].split(':')
                
                start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
                end_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
                
                duration_seconds = end_seconds - start_seconds
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                
                metadata['duration'] = f"{hours}h {minutes}min"
            except:
                metadata['duration'] = None
        
        # Estatísticas gerais
        metadata['total_speakers'] = len(set(utt['speaker'] for utt in utterances))
        metadata['total_utterances'] = len(utterances)
        metadata['total_words'] = sum(len(utt['text'].split()) for utt in utterances)
        
        return metadata
    
    def _create_variants(self, utterances: List[Dict[str, Any]], 
                        config: Dict[str, Any]) -> Dict[str, str]:
        """
        Cria variantes do documento para análises específicas
        """
        variants = {}
        
        # Variante 1: Apenas participantes (sem sistema)
        participant_utterances = [
            utt for utt in utterances
            if not any(sys in utt['speaker'].lower() 
                      for sys in ['system', 'teams', 'recording', 'gravação'])
        ]
        
        if participant_utterances:
            variants['participants_only'] = self._format_utterances(
                participant_utterances, config
            )
        
        # Variante 2: Por speaker individual
        speakers = set(utt['speaker'] for utt in utterances)
        
        for speaker in speakers:
            speaker_utterances = [
                utt for utt in utterances 
                if utt['speaker'] == speaker
            ]
            
            if speaker_utterances:
                # Criar nome seguro para arquivo
                safe_name = re.sub(r'[^\w\s-]', '', speaker)
                safe_name = safe_name.replace(' ', '_').lower()
                
                variant_key = f'speaker_{safe_name}'
                variants[variant_key] = self._format_utterances(
                    speaker_utterances, config
                )
        
        # Variante 3: Apenas perguntas (experimental)
        questions = [
            utt for utt in utterances
            if '?' in utt['text']
        ]
        
        if questions:
            variants['questions_only'] = self._format_utterances(questions, config)
        
        return variants
    
    def _generate_quality_report(self, original: str, cleaned: str, 
                                utterances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera relatório de qualidade da transcrição
        
        Avalia aspectos como:
        - Quantidade de conteúdo preservado
        - Proporção de falas muito curtas
        - Presença de timestamps
        - Problemas identificados
        """
        issues = []
        warnings = []
        
        # Verificar se encontrou falas
        if not utterances:
            issues.append("Nenhuma fala identificada - verificar formato")
            quality_score = 0
        else:
            # Calcular métricas
            total_utterances = len(utterances)
            
            # Falas muito curtas
            short_utterances = sum(1 for utt in utterances 
                                 if len(utt['text'].split()) < 5)
            short_percentage = (short_utterances / total_utterances) * 100
            
            if short_percentage > 50:
                issues.append(f"{short_percentage:.0f}% das falas são muito curtas (< 5 palavras)")
            elif short_percentage > 30:
                warnings.append(f"{short_percentage:.0f}% das falas são curtas")
            
            # Verificar timestamps
            with_timestamps = sum(1 for utt in utterances if utt.get('timestamp'))
            if with_timestamps == 0:
                warnings.append("Nenhum timestamp encontrado")
            elif with_timestamps < total_utterances * 0.5:
                warnings.append("Poucos timestamps encontrados")
            
            # Verificar speakers
            speakers = set(utt['speaker'] for utt in utterances)
            if len(speakers) == 1:
                warnings.append("Apenas um participante identificado")
            elif len(speakers) > 20:
                warnings.append(f"Muitos participantes ({len(speakers)}) - possível erro de parsing")
            
            # Calcular score
            quality_score = 100
            quality_score -= len(issues) * 20
            quality_score -= len(warnings) * 10
            quality_score = max(0, min(100, quality_score))
        
        # Estatísticas adicionais
        reduction_pct = ((len(original) - len(cleaned)) / len(original)) * 100 if original else 0
        
        avg_utterance_length = (
            sum(len(utt['text'].split()) for utt in utterances) / len(utterances)
        ) if utterances else 0
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'warnings': warnings,
            'reduction_percentage': round(reduction_pct, 1),
            'avg_utterance_length': round(avg_utterance_length, 1),
            'statistics': {
                'original_chars': len(original),
                'cleaned_chars': len(cleaned),
                'total_utterances': len(utterances),
                'unique_speakers': len(set(utt['speaker'] for utt in utterances)) if utterances else 0
            }
        }


# Teste standalone
if __name__ == "__main__":
    # Exemplo de transcrição Teams
    sample = """
[00:00:00] Recording Started
[00:00:05] João Silva: Bom dia pessoal, vamos começar a reunião?
[00:00:10] Maria Santos: Bom dia! Sim, podemos começar.
[00:00:15] João Silva: Ótimo.
[00:00:16] João Silva: Primeiro item da pauta...
[00:00:20] Pedro Oliveira (Guest): Oi, desculpem o atraso
[00:00:25] Maria Santos: Sem problemas Pedro!
[00:00:30] Sistema: Pedro Oliveira is now presenting
    """
    
    from qualia.core import Document
    
    cleaner = TeamsTranscriptCleaner()
    doc = Document(id="test", content=sample)
    
    result = cleaner._process_impl(doc, {
        "remove_system_messages": True,
        "merge_consecutive": True
    }, {})
    
    print("Documento limpo:")
    print(result['cleaned_document'])
    print(f"\nQualidade: {result['quality_report']['quality_score']}/100")
    print(f"Speakers: {[s['name'] for s in result['speakers']]}")