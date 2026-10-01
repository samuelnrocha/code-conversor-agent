# Arquitetura de Segurança e Gestão de Segredos

Este documento descreve detalhadamente as 5 camadas de segurança implementadas no **Code Conversor Agent** para proteger dados sensíveis, credenciais de banco e chaves de API contra vazamentos durante e após o processo de migração.

---

## 1. O Problema de Segurança em Migrações de Código

Projetos legados frequentemente possuem:
- Strings de conexão com senhas em arquivos de configuração locais (`appsettings.json`, `web.config`).
- Chaves de API hardcoded em constantes e classes utilitárias.
- Logs e rastreios de pilha (stack traces) que vazam DSNs e credenciais quando ocorre uma falha de conexão.

A abordagem comum de "passar o código para uma IA reescrever" frequentemente copia essas credenciais para o novo código ou as expõe no histórico de prompts e commits.

---

## 2. As 5 Camadas de Proteção

```
[Código .NET de Origem]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ CAMADA 1: SecretScanner (Detecção Estática & AST)       │
│ - Extrai strings de conexão e chaves de API            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ CAMADA 2: SecretVault (Isolamento em Disco)            │
│ - Gera .env com permissão estrita chmod 0600           │
│ - Gera .env.example público com valores sanitizados    │
│ - Atualiza .gitignore para bloquear arquivos sensíveis │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ CAMADA 3: Componentes PHP 8.4 Seguros                  │
│ - DatabaseConfig com __debugInfo() mascarado           │
│ - SafeDatabaseConnection (PDO sem emulação de prepares)│
│ - Tratamento de PDOException com expurgo de DSN        │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ CAMADA 4: SecurityAuditAgent (OWASP & Security-Agent)  │
│ - Varredura estática de queries, aleatoriedade e chaves│
│ - Emissão de SECURITY_AUDIT_REPORT.md                  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ CAMADA 5: Mascaramento Dinâmico de Logs                │
│ - Interceptação em tempo real de stdout/stderr         │
│ - Redação ativa: [REDACTED_DB_HOST], [REDACTED_PWD]    │
└────────────────────────────────────────────────────────┘
```

### Detalhes de Implementação

1. **`chmod 0600` no `.env`**:
   O arquivo `.env` gerado em `target-php-app/.env` recebe permissão de leitura/escrita estrita apenas para o proprietário (`stat.S_IRUSR | stat.S_IWUSR`). Nenhum outro usuário do sistema operacional tem permissão de leitura.
2. **Prevenção de SQL Injection**:
   A classe `SafeDatabaseConnection` impõe `PDO::ATTR_EMULATE_PREPARES => false`. Isso força o banco de dados remoto a compilar a consulta separadamente dos parâmetros enviados, impossibilitando que dados de entrada alterem a árvore sintática da query SQL.
3. **Mascaramento em Exceções**:
   Quando o PDO falha em conectar (por timeout ou credenciais inválidas), a mensagem padrão contém a string de conexão completa. O wrapper captura a `PDOException`, suprime a mensagem original e dispara uma `RuntimeException` genérica sem vestígios de infraestrutura interna.
4. **Mascaramento de Depuração (`__debugInfo`)**:
   Implementado em `DatabaseConfig.php`, assegura que chamadas de depuração como `var_dump()` ou ferramentas de APM (Datadog, New Relic) nunca serializem o campo de senha.
