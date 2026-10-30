# 1. Registrar decisões arquiteturais

Data: 2026-10-30

## Status

Aceito

## Contexto

O projeto está no início e várias decisões de arquitetura estão sendo tomadas. Sem registro, o motivo de cada escolha se perde e fica difícil revisitá-las ou explicá-las a quem entrar depois.

## Decisão

Registramos decisões arquiteturais como ADRs no formato de Michael Nygard, em português, em `docs/adr/NNNN-titulo-em-kebab-case.md`, com numeração sequencial. O modelo está em `0000-modelo.md`.

Status possíveis: Proposto, Aceito, Substituído por ADR-NNNN, Rejeitado. Um ADR aceito não é reescrito: uma mudança de rumo vira um novo ADR que o substitui.

## Consequências

- Toda decisão arquitetural relevante passa a exigir um ADR, rascunhado como "Proposto" e marcado "Aceito" só após confirmação do responsável pelo projeto.
- O histórico das decisões fica versionado junto com o código.
- Há um pequeno custo de escrita a cada decisão.
