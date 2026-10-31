#!/usr/bin/env bash
# Ralph loop: a cada iteração, uma sessão nova do Claude implementa UMA issue
# do GitHub (próxima sem bloqueio e sem assignee) via /implement e encerra.
# O acesso às issues é feito pelo MCP do GitHub configurado no claude (sem gh).
#
# Uso: scripts/ralph.sh [MAX_ITERACOES]   (padrão: 10)
# Requer: claude com o MCP do GitHub, árvore git limpa, branch != main.
set -euo pipefail

MAX=${1:-10}
LOG_DIR=${RALPH_LOG_DIR:-.ralph-logs}
SENTINELA='NADA_A_FAZER'

command -v claude >/dev/null || { echo 'claude não encontrado' >&2; exit 1; }
claude mcp list 2>/dev/null | grep -qi github \
  || { echo 'MCP do GitHub não configurado no claude (veja: claude mcp list)' >&2; exit 1; }

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

read -r -d '' PROMPT <<EOF || true
Você está em um loop automatizado (Ralph). Faça exatamente UMA issue e pare.
Use as ferramentas do MCP do GitHub (mcp__github__*) no repo ${owner}/${repo}.

1. Liste as issues abertas (list_issues, state OPEN). Escolha a de menor
   número que: não tem assignee, não tem a label ready-for-human e não tem
   bloqueio aberto (a linha "Blocked by: #N" no corpo ou nos comentários só
   pode citar issues já fechadas; confira com issue_read).
2. Se não existir nenhuma, responda apenas ${SENTINELA} e pare.
3. Reivindique: issue_write (update) com assignees ["${owner}"].
4. Rode /implement nessa issue (leia CLAUDE.md, GLOSSARY.md e os ADRs
   relevantes; use /tdd e rode ruff/pytest). Commite na branch atual.
5. Só se os testes e o lint passarem: add_issue_comment com o resumo e
   issue_write (update) com state closed e state_reason completed.
   Se não passarem, NÃO feche: remova o assignee (assignees []), comente o
   motivo na issue e responda apenas FALHOU.
EOF

for i in $(seq 1 "$MAX"); do
  log="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-$i.log"
  echo "=== Iteração $i/$MAX (branch $branch) — log: $log ==="

  claude -p "$PROMPT" \
    --permission-mode acceptEdits \
    --allowedTools 'Bash(git *)' 'Bash(.venv/bin/*)' 'Bash(docker compose *)' \
      'mcp__github__list_issues' 'mcp__github__issue_read' \
      'mcp__github__issue_write' 'mcp__github__add_issue_comment' \
      Read Edit Write Grep Glob Skill \
    | tee "$log"

  if grep -q "$SENTINELA" "$log"; then
    echo 'Nenhuma issue elegível restante. Fim.'
    exit 0
  fi
  if grep -qx 'FALHOU' "$log"; then
    echo "Iteração $i falhou; veja $log. Parando." >&2
    exit 1
  fi
done

echo "Limite de $MAX iterações atingido."
