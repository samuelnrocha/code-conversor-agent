# Plano de Arquitetura da Documentação (Information Architecture)

> Elaborado de acordo com as diretrizes do **Docs Assist** (`edwardangert/docs-agent-plugin`) e alinhado aos padrões da documentação moderna orientada a tarefas e conceitos.

---

## 1. Visão Geral da Arquitetura de Informação (IA)

O ecossistema de documentação do **Code Conversor Agent** é desenhado em quatro quadrantes canônicos (Diátaxis Framework), garantindo que desenvolvedores, arquitetos de software e lideranças técnicas encontrem a informação certa sem atrito:

```
                     CONHECIMENTO TEÓRICO
                              ▲
                              │
         CONCEITOS            │          REFERÊNCIA
    (Por que é assim?)        │     (Contratos e APIs)
                              │
 ─────────────────────────────┼─────────────────────────────► CONHECIMENTO PRÁTICO
                              │
          TUTORIAIS           │         COMO FAZER
      (Primeiros Passos)      │     (Guias de Execução)
                              │
                              ▼
```

### Matriz de Conteúdo

| Tipo de Conteúdo | Documento Alvo | Público / Intenção | Localização |
| :--- | :--- | :--- | :--- |
| **Ponto de Entrada & Narrativa** | `README.md` | Lideranças, Engenheiros Staff e Devs buscando visão holística e contextual | `/README.md` |
| **Conceito & Arquitetura** | `docs/architecture.md` | Arquitetos e Engenheiros que precisam entender o pipeline multi-agente e as garantias do compilador | `/docs/architecture.md` |
| **Referência de Segurança** | `docs/security.md` | SecOps e Desenvolvedores auditando as 5 camadas de proteção de dados e credenciais | `/docs/security.md` |
| **Guia de Conversão & Paridade** | `docs/csharp-to-php-mapping.md` | Desenvolvedores C# e PHP acompanhando o mapeamento sintático e de tipos DDD | `/docs/csharp-to-php-mapping.md` |
| **Critérios de Inviabilidade** | `DOCUMENTO_INVIABILIDADE_MIGRACAO.md` | Times de arquitetura avaliando se um projeto legado pode ou não ser migrado | `/DOCUMENTO_INVIABILIDADE_MIGRACAO.md` |
| **Relatório de Auditoria** | `target-php-app/SECURITY_AUDIT_REPORT.md` | Evidência automatizada de conformidade com OWASP | `/target-php-app/SECURITY_AUDIT_REPORT.md` |

---

## 2. Jornada do Usuário (User Journey Mapping)

### Jornada 1: O Engenheiro Staff ou Arquiteto de Software
- **Objetivo:** Avaliar a viabilidade de converter um serviço crítico legado em .NET para PHP 8.4 sem criar riscos de segurança ou divergências matemáticas.
- **Passos na Documentação:**
  1. Lê o `README.md` para entender a dor e a filosofia da conversão assistida por agentes com gatekeepers determinísticos.
  2. Consulta `docs/architecture.md` para inspecionar os agentes, o parser AST e as garantias de tipagem.
  3. Verifica `docs/security.md` para auditar como segredos, strings de conexão e senhas são isolados em vaults com `chmod 0600`.
  4. Executa a simulação de inviabilidade com `--simulate-incompatible` para ver o fail-safe em ação.

### Jornada 2: O Desenvolvedor Backend / Executor da Migração
- **Objetivo:** Executar o pipeline, verificar os testes unitários e inspecionar o código PHP 8.4 gerado.
- **Passos na Documentação:**
  1. Executa o Quickstart reproduzível no `README.md`.
  2. Roda os testes xUnit em .NET para atestar a baseline de origem.
  3. Executa o `orchestrator.py` e acompanha os logs sanitizados em tempo real.
  4. Inspeciona `docs/csharp-to-php-mapping.md` para comparar a equivalência entre C# Records e PHP 8.4 `readonly class`.

---

## 3. Rastreabilidade de Afirmações (Claim-to-Code Traceability)

Todas as declarações presentes nesta documentação são comprovadas por código executável e testável:

- **Afirmação:** *"O pipeline mascara segredos ativamente nos streams de saída."*
  - **Prova no Código:** [`SecretVault.mask_text()`](file:///home/samuel/code-conversor-agent/agent-converter/security/secret_vault.py) intercepta logs de stdout/stderr substituindo credenciais por `[REDACTED_***]`.
- **Afirmação:** *"O PHP 8.4 previne injeção SQL nativamente no driver PDO."*
  - **Prova no Código:** [`SafeDatabaseConnection.php`](file:///home/samuel/code-conversor-agent/target-php-app/src/Infrastructure/Database/SafeDatabaseConnection.php) impõe `PDO::ATTR_EMULATE_PREPARES => false`.
- **Afirmação:** *"As senhas de banco nunca são exibidas em var_dump ou print_r."*
  - **Prova no Código:** [`DatabaseConfig.php`](file:///home/samuel/code-conversor-agent/target-php-app/src/Infrastructure/Database/DatabaseConfig.php) implementa `__debugInfo()` com mascaramento ativo.
- **Afirmação:** *"Há 100% de paridade comportamental entre C# e PHP 8.4."*
  - **Prova no Código:** 8 testes em `OrderBillingSystem.Tests.csproj` e 10 testes em `target-php-app/tests/OrderAggregateTest.php` com asserções equivalentes.
