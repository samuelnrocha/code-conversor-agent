# Relatório de Inviabilidade Técnica de Migração (.NET -> PHP 8.4)

> **Decisão:** NÃO É POSSÍVEL REALIZAR A MIGRAÇÃO AUTOMÁTICA
> **Score de Compatibilidade:** 35.0%

## Bloqueadores Críticos Detectados
- ❌ **Incompatible dependency: System.Runtime.InteropServices.Marshal (P/Invoke to native Win32 user32.dll)**
- ❌ **Incompatible dependency: System.Windows.Forms (Desktop UI not supported on target PHP CLI)**

## Avisos e Limitações

## Recomendações da Análise
- 💡 Full architectural parity is supported in PHP 8.4 using Domain-Driven Design (DDD).
- 💡 Use PHP 8.4 strict_types=1 in all emitted files.
- 💡 Represent C# Money struct as an immutable readonly class with rounding guarantees.
