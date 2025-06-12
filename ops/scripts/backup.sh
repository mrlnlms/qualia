#!/bin/bash

# Backup Automático do Qualia Core - Versão Otimizada
# Backupa: cache, output, logs, configurações, stats
# Comprime com timestamp e remove backups antigos

set -euo pipefail  # Modo strict

# =================== CONFIGURAÇÕES ===================
QUALIA_DIR="${QUALIA_DIR:-$(pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$QUALIA_DIR/backups}"
KEEP_DAYS="${KEEP_DAYS:-30}"

# Diretórios importantes para backup
DIRS_TO_BACKUP=(
    "cache"
    "output" 
    "ops"
    "plugins"
)

# Arquivos críticos
FILES_TO_BACKUP=(
    ".env"
    "requirements.txt"
    "run_api.py"
    "circuit_breaker_stats.json"
    "*.log"
)

# =================== FUNÇÕES ===================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

check_dependencies() {
    command -v tar >/dev/null 2>&1 || error "tar não encontrado"
    command -v gzip >/dev/null 2>&1 || error "gzip não encontrado"
}

create_backup_dir() {
    [[ ! -d "$BACKUP_DIR" ]] && mkdir -p "$BACKUP_DIR"
}

calculate_size() {
    local path="$1"
    if [[ -e "$path" ]]; then
        du -sh "$path" 2>/dev/null | cut -f1 || echo "0K"
    else
        echo "0K"
    fi
}

create_backup() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="qualia_backup_${timestamp}"
    local backup_file="$BACKUP_DIR/${backup_name}.tar.gz"
    local temp_dir=$(mktemp -d)
    
    log "📦 Criando backup: $backup_name"
    
    # Criar estrutura temporária
    mkdir -p "$temp_dir/$backup_name"
    
    # Copiar diretórios importantes
    for dir in "${DIRS_TO_BACKUP[@]}"; do
        if [[ -d "$QUALIA_DIR/$dir" ]]; then
            local size=$(calculate_size "$QUALIA_DIR/$dir")
            log "  📂 $dir ($size)"
            cp -r "$QUALIA_DIR/$dir" "$temp_dir/$backup_name/" 2>/dev/null || {
                log "  ⚠️  Erro copiando $dir (continuando...)"
            }
        fi
    done
    
    # Copiar arquivos críticos
    for pattern in "${FILES_TO_BACKUP[@]}"; do
        find "$QUALIA_DIR" -maxdepth 1 -name "$pattern" -type f 2>/dev/null | while read -r file; do
            if [[ -f "$file" ]]; then
                local size=$(calculate_size "$file")
                local rel_path=${file#$QUALIA_DIR/}
                log "  📄 $rel_path ($size)"
                cp "$file" "$temp_dir/$backup_name/" 2>/dev/null || true
            fi
        done
    done
    
    # Criar relatório do backup
    cat > "$temp_dir/$backup_name/backup_info.txt" << EOF
🔧 Qualia Core Backup Report
============================
📅 Data: $(date)
🖥️  Host: $(hostname)
👤 Usuário: $(whoami)
📁 Diretório: $QUALIA_DIR
🔄 Git Hash: $(cd "$QUALIA_DIR" && git rev-parse HEAD 2>/dev/null || echo "não é repositório git")
🌿 Git Branch: $(cd "$QUALIA_DIR" && git branch --show-current 2>/dev/null || echo "unknown")

📊 Status do Sistema:
$(cd "$QUALIA_DIR" && python -c "
from qualia.core import QualiaCore
try:
    core = QualiaCore()
    plugins = core.discover_plugins()
    print(f'✅ {len(plugins)} plugins funcionando')
    for pid in plugins: print(f'  - {pid}')
except Exception as e:
    print(f'❌ Erro: {e}')
" 2>/dev/null || echo "❌ Não foi possível verificar plugins")

📦 Conteúdo do Backup:
$(cd "$temp_dir/$backup_name" && find . -type f | sort)
EOF
    
    # Comprimir
    log "🗜️  Comprimindo backup..."
    (cd "$temp_dir" && tar -czf "$backup_file" "$backup_name") || error "Falha ao comprimir"
    
    # Limpar temp
    rm -rf "$temp_dir"
    
    # Mostrar resultado
    local backup_size=$(calculate_size "$backup_file")
    log "✅ Backup criado: ${backup_name}.tar.gz ($backup_size)"
    
    return 0
}

cleanup_old_backups() {
    log "🧹 Removendo backups antigos (>$KEEP_DAYS dias)..."
    
    local deleted=0
    local total_freed=0
    
    find "$BACKUP_DIR" -name "qualia_backup_*.tar.gz" -type f -mtime +$KEEP_DAYS 2>/dev/null | while read -r backup_file; do
        local size_kb=$(du -k "$backup_file" 2>/dev/null | cut -f1 || echo 0)
        local size_human=$(calculate_size "$backup_file")
        local age_days=$(( ($(date +%s) - $(stat -f %m "$backup_file" 2>/dev/null || echo 0)) / 86400 ))
        
        log "  🗑️  Removendo: $(basename "$backup_file") ($size_human, ${age_days}d)"
        rm "$backup_file" && ((deleted++)) && ((total_freed += size_kb))
    done
    
    if [[ $deleted -eq 0 ]]; then
        log "  ✨ Nenhum backup antigo para remover"
    else
        local freed_human=$(echo $total_freed | awk '{print $1/1024 "MB"}')
        log "  🗑️  $deleted backups removidos ($freed_human liberados)"
    fi
}

show_backup_summary() {
    log "📊 Resumo dos backups:"
    
    if [[ ! -d "$BACKUP_DIR" ]] || [[ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        log "  📭 Nenhum backup encontrado"
        return
    fi
    
    local total_backups=0
    local total_size_kb=0
    
    find "$BACKUP_DIR" -name "qualia_backup_*.tar.gz" -type f 2>/dev/null | sort -r | while read -r backup_file; do
        local size_kb=$(du -k "$backup_file" 2>/dev/null | cut -f1 || echo 0)
        total_size_kb=$((total_size_kb + size_kb))
        total_backups=$((total_backups + 1))
        
        local backup_name=$(basename "$backup_file" .tar.gz)
        local date_part=${backup_name#qualia_backup_}
        local formatted_date="${date_part:0:4}-${date_part:4:2}-${date_part:6:2} ${date_part:9:2}:${date_part:11:2}"
        local size_human=$(calculate_size "$backup_file")
        
        log "  📦 $formatted_date - $size_human"
    done | head -10  # Mostrar só os 10 mais recentes
    
    local total_size_mb=$((total_size_kb / 1024))
    log "  📈 Total: $total_backups backups (~${total_size_mb}MB)"
}

restore_backup() {
    local backup_file="$1"
    local restore_dir="${2:-$QUALIA_DIR/restored_$(date +%Y%m%d_%H%M%S)}"
    
    [[ ! -f "$backup_file" ]] && error "Backup não encontrado: $backup_file"
    
    log "♻️  Restaurando backup: $(basename "$backup_file")"
    log "📁 Destino: $restore_dir"
    
    mkdir -p "$restore_dir"
    tar -xzf "$backup_file" -C "$restore_dir" --strip-components=1 || error "Falha ao extrair"
    
    log "✅ Backup restaurado com sucesso!"
    log "📋 Ver relatório: cat $restore_dir/backup_info.txt"
}

# =================== MAIN ===================
main() {
    local command="${1:-backup}"
    
    case "$command" in
        backup)
            log "🚀 Iniciando backup do Qualia Core..."
            check_dependencies
            create_backup_dir
            create_backup
            cleanup_old_backups
            show_backup_summary
            log "🎉 Backup concluído!"
            ;;
            
        list)
            log "📋 Backups disponíveis:"
            show_backup_summary
            ;;
            
        cleanup)
            log "🧹 Limpando backups antigos..."
            cleanup_old_backups
            show_backup_summary
            ;;
            
        restore)
            local backup_file="$2"
            local restore_dir="${3:-}"
            [[ -z "$backup_file" ]] && error "Uso: $0 restore <arquivo_backup> [destino]"
            restore_backup "$backup_file" "$restore_dir"
            ;;
            
        cron)
            # Modo silencioso para cron
            {
                check_dependencies
                create_backup_dir
                create_backup
                cleanup_old_backups
            } 2>&1 | grep -E "(ERROR|✅|📦)" || true
            ;;
            
        help|--help|-h)
            cat << 'EOF'
🔧 Backup Automático do Qualia Core

Comandos:
    backup    Criar novo backup (padrão)
    list      Listar backups existentes  
    cleanup   Remover backups antigos
    restore   Restaurar backup específico
    cron      Modo silencioso para cron
    help      Mostrar esta ajuda

Exemplos:
    ./ops/scripts/backup.sh
    ./ops/scripts/backup.sh list
    ./ops/scripts/backup.sh restore backups/qualia_backup_20241211_143022.tar.gz
    
Configurar cron (todo dia 2AM):
    crontab -e
    # Adicionar: 0 2 * * * /caminho/completo/ops/scripts/backup.sh cron

Variáveis:
    BACKUP_DIR     Diretório dos backups (padrão: ./backups)
    KEEP_DAYS      Dias para manter (padrão: 30)
EOF
            ;;
            
        *)
            error "Comando inválido: $command. Use '$0 help' para ajuda."
            ;;
    esac
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi