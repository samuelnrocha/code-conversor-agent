# Relatório de Governança de Segredos

**Status:** concluído — credenciais isoladas e arquivos protegidos.
**Escopo:** `source-dotnet-app/OrderBillingSystem.App/appsettings.json` e todos os
arquivos `.cs` do projeto fonte, além do código PHP gerado.

## Achados (sem exibir valores)

- `appsettings.json` continha uma string de conexão SQL Server com host, banco,
  usuário, senha e parâmetros de conexão.
- `appsettings.json` continha uma chave de API do serviço de pagamentos e um
  segredo de webhook.
- Não foram encontrados outros valores de credenciais nos arquivos `.cs` além
  de tokens/valores de teste usados pelo mock e pelo programa de demonstração.
- O PHP tinha valores padrão de configuração de banco. Eles foram removidos
  para impedir credenciais ou nomes de infraestrutura embutidos no código.

## Ações executadas

- Extração para `target-php-app/.env` usando as variáveis `DB_DRIVER`, `DB_HOST`,
  `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, `PAYMENTSERVICE_APIKEY` e
  `PAYMENTSERVICE_WEBHOOK_SECRET`.
- Aplicação de permissões `0600` em `.env`.
- Criação de `.env.example` com placeholders sanitizados e sem valores reais.
- Atualização do `.gitignore` para bloquear `.env`, `.env.local`, `*.secret`,
  `*.key` e `*.pem`; `.env.example` permanece permitido.
- `DatabaseConfig` agora exige host, banco e usuário do ambiente (sem defaults
  de credenciais) e usa o driver/porta configuráveis.
- Tokens e senhas literais de fixtures/demonstração foram substituídos por
  valores gerados em tempo de execução.

## Validações

- `.env`: modo Unix confirmado como `0600`.
- `.env.example`: contém somente placeholders e valores não secretos.
- Verificação estática de arquivos PHP não encontrou os valores extraídos nem
  padrões de credenciais reais no código de destino.
- Verificação do `.gitignore` confirmou todas as regras obrigatórias.
- A inspeção foi feita sem copiar valores secretos para este relatório ou para
  a saída operacional.
