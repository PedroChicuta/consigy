#!/usr/bin/env bash
# Ralph loop: a cada iteração, uma sessão nova do agente (Claude ou Antigravity)
# implementa UMA issue do GitHub (próxima sem bloqueio e sem assignee) via
# /implement e encerra. O acesso às issues é feito pelo MCP do GitHub (sem gh).
#
# Uso: scripts/ralph.sh [--agent claude|agy] [--model MODELO] [MAX_ITERACOES]
# Variáveis:
#   RALPH_AGENT    claude (padrão) ou agy
#   RALPH_MODEL    modelo opcional repassado a --model
#   RALPH_LOG_DIR  diretório de logs (padrão: .ralph-logs)
# Requer: agente escolhido com o MCP do GitHub ativo, árvore git limpa, branch != main.
set -euo pipefail

usage() {
  cat <<'EOF'
Uso: scripts/ralph.sh [opções] [MAX_ITERACOES]

Opções:
  -a, --agent <claude|agy>  Agente a executar (padrão: $RALPH_AGENT ou claude)
  -m, --model <modelo>      Modelo opcional repassado para --model
  -h, --help                Exibe esta ajuda

Exemplos:
  scripts/ralph.sh                  # 10 iterações com Claude
  scripts/ralph.sh 5                # 5 iterações com Claude
  scripts/ralph.sh --agent agy 5    # 5 iterações com Antigravity (agy)
  RALPH_AGENT=agy scripts/ralph.sh  # 10 iterações com Antigravity (agy)
EOF
}

AGENT=${RALPH_AGENT:-claude}
MODEL=${RALPH_MODEL:-}
MAX=10
MAX_DEFINIDO=0
LOG_DIR=${RALPH_LOG_DIR:-.ralph-logs}
SENTINELA='NADA_A_FAZER'

while [[ $# -gt 0 ]]; do
  case "$1" in
    -a|--agent)
      [[ $# -ge 2 ]] || { echo 'Faltou valor para --agent (use claude ou agy).' >&2; exit 1; }
      AGENT=$2
      shift 2
      ;;
    --agent=*)
      AGENT=${1#*=}
      shift
      ;;
    -m|--model)
      [[ $# -ge 2 ]] || { echo 'Faltou valor para --model.' >&2; exit 1; }
      MODEL=$2
      shift 2
      ;;
    --model=*)
      MODEL=${1#*=}
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ $MAX_DEFINIDO -eq 0 && $1 =~ ^[0-9]+$ ]]; then
        MAX=$1
        MAX_DEFINIDO=1
        shift
      else
        echo "Argumento inválido: $1" >&2
        usage >&2
        exit 1
      fi
      ;;
  esac
done

case "$AGENT" in
  claude) ;;
  agy|antigravity) AGENT='agy' ;;
  *)
    echo "Agente inválido: '$AGENT' (use 'claude' ou 'agy')." >&2
    exit 1
    ;;
esac

if [[ $AGENT == 'claude' ]]; then
  command -v claude >/dev/null || { echo 'claude não encontrado' >&2; exit 1; }
  claude mcp list 2>/dev/null | grep -qi github \
    || { echo 'MCP do GitHub não configurado no claude (veja: claude mcp list)' >&2; exit 1; }
else
  command -v agy >/dev/null || { echo 'agy não encontrado' >&2; exit 1; }
  agy mcp list 2>/dev/null | awk 'tolower($1) == "github" && tolower($3) == "enabled" { ok=1 } END { exit !ok }' \
    || { echo 'MCP do GitHub não configurado/ativo no Antigravity (veja: agy mcp list)' >&2; exit 1; }
fi

# owner/repo a partir do remote origin (https ou ssh)
repo_slug=$(git remote get-url origin | sed -E 's#^(git@github.com:|https://github.com/)##; s#\.git$##')
owner=${repo_slug%%/*}
repo=${repo_slug##*/}

branch=$(git branch --show-current)
if [[ -z $branch || $branch == main ]]; then
  echo 'Rode em uma branch dedicada (git switch -c ralph/<nome>), nunca na main.' >&2
  exit 1
fi
if [[ -n $(git status --porcelain) ]]; then
  echo 'Árvore git suja: commite ou faça stash antes.' >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

if [[ $AGENT == 'claude' ]]; then
  MCP_INSTRUCAO="Use as ferramentas do MCP do GitHub (mcp__github__*) no repo ${owner}/${repo}."
  IMPLEMENT_INSTRUCAO="Rode /implement nessa issue (leia CLAUDE.md, GLOSSARY.md e os ADRs relevantes; use /tdd e rode ruff/pytest)."
else
  MCP_INSTRUCAO="Use as ferramentas do servidor MCP \"github\" (via call_mcp_tool com ServerName \"github\" ou mcp_github_*) no repo ${owner}/${repo}."
  IMPLEMENT_INSTRUCAO="Siga a skill implement (/implement) nessa issue (leia AGENTS.md, GLOSSARY.md, docs/agents/issue-tracker.md e os ADRs relevantes; leia e aplique a skill tdd e rode ruff/pytest)."
fi

read -r -d '' PROMPT <<EOF || true
Você está em um loop automatizado (Ralph). Faça exatamente UMA issue e pare.
${MCP_INSTRUCAO}

1. Liste as issues abertas (list_issues, state OPEN). Escolha a de menor
   número que: não tem assignee, não tem a label ready-for-human e não tem
   bloqueio aberto (a linha "Blocked by: #N" no corpo ou nos comentários só
   pode citar issues já fechadas; confira com issue_read).
2. Se não existir nenhuma, responda apenas ${SENTINELA} (sozinho em uma linha) e pare.
3. Reivindique: issue_write (update) com assignees ["${owner}"].
4. ${IMPLEMENT_INSTRUCAO} Commite na branch atual.
   Rode TUDO a partir da raiz do repositório, sem 'cd' e sem encadear
   comandos (só estes são permitidos): .venv/bin/pytest, .venv/bin/ruff
   check, .venv/bin/python src/manage.py makemigrations|migrate|check.
5. Só se os testes e o lint passarem: add_issue_comment com o resumo e
   issue_write (update) com state closed e state_reason completed.
   Se não passarem, NÃO feche: remova o assignee (assignees []), comente o
   motivo na issue e responda apenas 'FALHOU: <motivo em uma linha>'.
EOF

AGY_SETTINGS='{"permissions":{"allow":["command(git)","command(.venv/bin/pytest)","command(.venv/bin/ruff)","command(.venv/bin/python)","command(regex:^\\.venv/bin/)","command(docker compose)","mcp(github/*)"]}}'

guardar_stash_se_sujo() {
  local iter=$1
  if [[ -n $(git status --porcelain) ]]; then
    git stash push --include-untracked -m "ralph ($AGENT): iteração $iter falhou ($(date +%F\ %T))" >/dev/null
    echo 'Trabalho parcial guardado em stash (git stash list / git stash pop).' >&2
  fi
}

for i in $(seq 1 "$MAX"); do
  log="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-${AGENT}-$i.log"
  echo "=== Iteração $i/$MAX (agente: $AGENT, branch: $branch) — log: $log ==="

  if [[ $AGENT == 'claude' ]]; then
    cmd=(
      claude -p "$PROMPT"
      --permission-mode acceptEdits
      --allowedTools
        'Bash(git *)' 'Bash(.venv/bin/*)' 'Bash(docker compose *)'
        'mcp__github__list_issues' 'mcp__github__issue_read'
        'mcp__github__issue_write' 'mcp__github__add_issue_comment'
        Read Edit Write Grep Glob Skill
    )
  else
    cmd=(
      agy -p "$PROMPT"
      --mode accept-edits
      --settings "$AGY_SETTINGS"
    )
  fi
  [[ -n $MODEL ]] && cmd+=(--model "$MODEL")

  if ! "${cmd[@]}" | tee "$log"; then
    guardar_stash_se_sujo "$i"
    echo "Iteração $i encerrou com erro no comando '$AGENT'. Log completo: $log. Parando." >&2
    exit 1
  fi

  if grep -Eq "^[[:space:]]*${SENTINELA}[[:space:]]*$" "$log"; then
    echo 'Nenhuma issue elegível restante. Fim.'
    exit 0
  fi
  if grep -q '^FALHOU' "$log"; then
    guardar_stash_se_sujo "$i"
    echo "Iteração $i falhou: $(grep -m1 '^FALHOU' "$log")" >&2
    echo "Log completo: $log. Parando." >&2
    exit 1
  fi
done

echo "Limite de $MAX iterações atingido."
