#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================================================"
echo "    OPENCODE MULTI-AGENT MIGRATION PIPELINE (VIA OPENROUTER)"
echo "    Modelo: openai/gpt-5.6-luna (Roteamento: Provedor Mais Barato)"
echo "========================================================================"

# Verificar se OPENROUTER_API_KEY está configurada
if [ -z "$OPENROUTER_API_KEY" ]; then
    # Verificar se existe em .env
    if [ -f "$ROOT_DIR/.env" ]; then
        KEY_IN_ENV=$(grep "^OPENROUTER_API_KEY=" "$ROOT_DIR/.env" | cut -d'=' -f2- | tr -d ' "')
        if [ -n "$KEY_IN_ENV" ]; then
            export OPENROUTER_API_KEY="$KEY_IN_ENV"
            echo "✔ OPENROUTER_API_KEY carregada a partir de .env"
        fi
    fi
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY não foi encontrada no ambiente!"
    echo "   Por favor, configure com: export OPENROUTER_API_KEY='sk-or-v1-...'"
    echo "   Ou adicione no arquivo .env na raiz do projeto."
    exit 1
fi

AGENT="${1:-orchestrator}"
PROMPT="${2:-Inicie o pipeline completo de conversão do projeto .NET para PHP 8.4 seguindo todos os subagentes.}"

echo "Iniciando OpenCode com subagente: '$AGENT'..."
cd "$ROOT_DIR"
opencode run --standalone --agent "$AGENT" "$PROMPT"
