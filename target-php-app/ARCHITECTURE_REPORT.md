# Relatório de Arquitetura e Plano de Destino — OrderBillingSystem

**Origem:** `source-dotnet-app/OrderBillingSystem.sln`  
**Destino:** `target-php-app`  
**Runtime alvo:** PHP 8.4  
**Status:** mapeamento estrutural; **nenhuma transpile completa foi executada nesta etapa**.

## 1. Decisão e limites

O `GATE_DECISION.md` aprovou a migração (`GO`, compatibilidade estimada de 96%).
O `COMPATIBILITY_REPORT.md` não encontrou bloqueadores de plataforma, mas registra
riscos que devem orientar a implementação: precisão monetária, nulabilidade,
persistência transacional, concorrência e substituição de `Task`/LINQ.

Este documento define o destino de namespaces, tipos, contratos e componentes.
Ele não é uma implementação alternativa nem autoriza copiar configurações do
projeto .NET. Segredos do `appsettings.json` não são reproduzidos aqui.

## 2. Convenção PSR-4

O namespace raiz é `OrderBillingSystem\\`, mapeado para `src/` em
`composer.json`. O namespace de testes é `OrderBillingSystem\\Tests\\`, mapeado
para `tests/` apenas em `autoload-dev`.

| Namespace C# | Namespace PHP 8.4 | Diretório de destino |
|---|---|---|
| `OrderBillingSystem.Core.Enums` | `OrderBillingSystem\\Domain\\Enums` | `src/Domain/Enums/` |
| `OrderBillingSystem.Core.ValueObjects` | `OrderBillingSystem\\Domain\\ValueObjects` | `src/Domain/ValueObjects/` |
| `OrderBillingSystem.Core.Entities` | `OrderBillingSystem\\Domain\\Entities` | `src/Domain/Entities/` |
| `OrderBillingSystem.Core.Aggregates` | `OrderBillingSystem\\Domain\\Aggregates` | `src/Domain/Aggregates/` |
| `OrderBillingSystem.Core.Events` | `OrderBillingSystem\\Domain\\Events` | `src/Domain/Events/` |
| `OrderBillingSystem.Core.Strategies` | `OrderBillingSystem\\Domain\\Strategies` | `src/Domain/Strategies/` |
| `OrderBillingSystem.Core.Exceptions` | `OrderBillingSystem\\Domain\\Exceptions` | `src/Domain/Exceptions/` |
| `OrderBillingSystem.Core.Services` | `OrderBillingSystem\\Domain\\Services` | `src/Domain/Services/` |
| `OrderBillingSystem.Core.UseCases` | `OrderBillingSystem\\Application\\UseCases` | `src/Application/UseCases/` |
| `OrderBillingSystem.App.Infrastructure` | `OrderBillingSystem\\Infrastructure` | `src/Infrastructure/` |
| `OrderBillingSystem.Tests` | `OrderBillingSystem\\Tests` | `tests/` |

### Regra de arquivos

Na implementação definitiva, cada classe, interface, enum e exception deve
ficar em arquivo cujo nome corresponda ao símbolo (`Money.php`,
`OrderRepositoryInterface.php`, etc.). Os arquivos agrupados atualmente
(`DomainEvents.php`, `Contracts.php`, `Implementations.php`) são úteis como
estado intermediário, mas devem ser separados antes de depender exclusivamente
do autoload PSR-4 em produção.

## 3. Mapa de tipos de domínio

| Origem | Destino recomendado | Papel e invariantes |
|---|---|---|
| `Enums/OrderStatus.cs` — `OrderStatus` | `Domain\\Enums\\OrderStatus` | `enum` string nativo: `draft`, `confirmed`, `paid`, `shipped`, `cancelled`, `refunded`; transições devem ser controladas pelo agregado. |
| `ValueObjects/Money.cs` — `Money` | `Domain\\ValueObjects\\Money` | `final readonly class`; moeda normalizada; não aceitar negativos; não usar `float`; `add`, `subtract` e `multiply` substituem operadores. Preferir centavos inteiros ou BCMath e arredondamento explícito equivalente a `AwayFromZero`. |
| `ValueObjects/TaxRate.cs` — `TaxRate` | `Domain\\ValueObjects\\TaxRate` | `final readonly class`; país obrigatório, taxa entre 0 e 100; calcula imposto na moeda do subtotal. |
| `Entities/OrderItem.cs` — `OrderItem` | `Domain\\Entities\\OrderItem` | entidade mutável apenas na quantidade; SKU, nome, preço, quantidade positiva e desconto percentual validado; soma SKU repetido no agregado. |
| `Aggregates/Order.cs` — `Order` | `Domain\\Aggregates\\Order` | aggregate root; mantém itens, estratégias e eventos; protege estado `Draft → Confirmed → Paid → Shipped` e cancelamento; expõe cópias/visões defensivas. |
| `Events/OrderEvents.cs` — `IDomainEvent` | `Domain\\Events\\DomainEvent` (ou `IDomainEvent`) | contrato marcador para eventos imutáveis, UUID e `DateTimeImmutable`. |
| `OrderCreatedEvent` | `Domain\\Events\\OrderCreatedEvent` | emitido na criação. |
| `OrderStatusChangedEvent` | `Domain\\Events\\OrderStatusChangedEvent` | registra estado anterior, novo estado e instante. |
| `OrderPaidEvent` | `Domain\\Events\\OrderPaidEvent` | registra total, transação e instante; transação não pode ser nula em pagamento bem-sucedido. |
| `Strategies/DiscountStrategies.cs` | `Domain\\Strategies\\DiscountStrategyInterface` e estratégias concretas | contrato de desconto; `VipDiscountStrategy` e `FixedCouponDiscountStrategy`; preservar soma sobre o mesmo subtotal e limite ao subtotal. |
| `Exceptions/DomainException.cs` | `Domain\\Exceptions\\DomainException` | exceção base de domínio; `InvalidOrderStateException` para transições/invariantes de estado. |

O construtor de `Order` deve manter a moeda do pedido explicitamente. Não
reproduzir a falha observada no caso de uso que infere moeda de um subtotal
vazio (`BRL`). `Cancel(reason)` deve ter uma decisão funcional antes da
persistência: persistir/auditar o motivo ou removê-lo do contrato.

## 4. Contratos e aplicação

| Origem | Destino PHP | Contrato |
|---|---|---|
| `IOrderRepository` | `Domain\\Services\\OrderRepositoryInterface` | `getById(string): ?Order`, `save(Order): void`, `getByCustomerId(string): array/list<Order>`. A implementação de produção deve ser transacional. |
| `IPaymentGateway` | `Domain\\Services\\PaymentGatewayInterface` | `processPayment(string, Money, string): PaymentResult`; token deve ser tratado como dado sensível e nunca logado. |
| `INotificationService` | `Domain\\Services\\NotificationServiceInterface` | confirmação e recibo; adaptadores podem ser síncronos ou encaminhar para fila. |
| `PaymentResult` | `Domain\\Services\\PaymentResult` | `final readonly class`; sucesso exige `transactionId` não nulo/não vazio; falha pode conter mensagem segura. |
| `CreateOrderCommand` | `Application\\UseCases\\CreateOrderCommand` | DTO imutável de criação, país, taxa e moeda. |
| `AddItemCommand` | `Application\\UseCases\\AddItemCommand` | DTO imutável de item; validar quantidade, preço e desconto no limite de entrada/domínio. |
| `ProcessOrderPaymentCommand` | `Application\\UseCases\\ProcessOrderPaymentCommand` | DTO imutável de ordem e token de pagamento. |
| `OrderProcessingService` | `Application\\UseCases\\OrderProcessingService` | orquestra repositório, gateway e notificações; implementação PHP pode ser síncrona, sem prometer concorrência de `Task`. |

Fluxo do caso de uso: carregar/agregar → executar comando no agregado → salvar
→ emitir notificação. Pagamento falho vira `DomainException`; pagamento
bem-sucedido deve validar `PaymentResult.transactionId` antes de chamar
`markAsPaid`.

## 5. Infraestrutura e banco seguro

| Componente | Namespace/classe de destino | Plano |
|---|---|---|
| Repositório em memória | `OrderBillingSystem\\Infrastructure\\InMemoryOrderRepository` | somente testes/demo; não prometer a segurança de `ConcurrentDictionary` em PHP-FPM. |
| Repositório persistente | `OrderBillingSystem\\Infrastructure\\Persistence\\PdoOrderRepository` | próximo passo; PDO, transações, consultas parametrizadas, hidratação explícita e controle de concorrência/versão. |
| Gateway mock | `OrderBillingSystem\\Infrastructure\\Payments\\MockPaymentGateway` | testes; tokens e mensagens não devem ser registrados. |
| Gateway real | `OrderBillingSystem\\Infrastructure\\Payments\\HttpPaymentGateway` | adaptador HTTP futuro; API key e webhook secret somente via ambiente/cofre, nunca no código. |
| Notificação de console | `OrderBillingSystem\\Infrastructure\\Notifications\\ConsoleNotificationService` | demo/testes; produção deve usar adaptador de mensageria ou provedor. |
| Configuração DB | `OrderBillingSystem\\Infrastructure\\Database\\DatabaseConfig` | já presente; lê ambiente, exige host/banco/usuário e implementa `__debugInfo()` mascarando senha. Não aceitar defaults de credencial. |
| Conexão DB | `OrderBillingSystem\\Infrastructure\\Database\\SafeDatabaseConnection` | já presente; PDO com `ERRMODE_EXCEPTION`, `FETCH_ASSOC`, `ATTR_EMULATE_PREPARES=false`, conexão não persistente e exceções sanitizadas. |

`SafeDatabaseConnection::executePrepared()` deve permanecer como caminho de
consultas parametrizadas. O repositório futuro deve delimitar transações para
alterações do agregado e evitar interpolação de SQL, DSN, credenciais ou tokens
em logs/exceções.

## 6. Plano de execução em `target-php-app`

1. **Estrutura e autoload (atual):** manter `composer.json` com
   `OrderBillingSystem\\: src/`; separar símbolos agrupados em arquivos PSR-4 e
   executar `composer dump-autoload`.
2. **Núcleo matemático:** finalizar `Money`/`TaxRate`, sem `float`, com testes de
   moeda incompatível, não-negatividade e arredondamento `AwayFromZero`.
3. **Domínio:** finalizar enum, exceções, entidade, agregado, estratégias e
   eventos; preservar as oito áreas de comportamento do relatório de
   compatibilidade e corrigir a origem da moeda do pedido.
4. **Aplicação:** separar comandos e serviço; escolher síncrono para CLI/HTTP
   simples ou adaptador de fila para processamento assíncrono.
5. **Persistência:** implementar `PdoOrderRepository` com schema/migrations,
   transações e estratégia de concorrência; manter o repositório em memória para
   testes unitários.
6. **Integrações:** substituir mock de pagamento apenas quando o contrato HTTP,
   timeout, retry, idempotência e armazenamento de webhook estiverem definidos.
7. **Testes:** portar os testes xUnit para PHPUnit/Pest e adicionar moeda
   diferente, subtotal vazio, cupom maior que subtotal, transação ausente,
   cancelamento idempotente e arredondamento.
8. **Verificação final:** `php -l`, testes, `composer audit` e varredura de
   segredos antes de qualquer release.

## 7. Controle de segredos e verificação

O relatório de segurança registra que os valores reais foram extraídos para
`.env` com permissão `0600`, que `.env` é ignorado pelo Git e que `.env.example`
contém apenas placeholders. Este relatório não contém valores, hosts reais,
chaves, senhas ou tokens.

Checklist aplicado ao plano:

- não copiar `appsettings.json` para o destino;
- não inserir valores de exemplo que pareçam credenciais reais;
- manter `DB_PASSWORD`, `PAYMENTSERVICE_APIKEY` e
  `PAYMENTSERVICE_WEBHOOK_SECRET` somente em ambiente/cofre;
- nunca expor a senha em `var_dump`, `print_r`, logs ou exceções;
- não logar token de pagamento, API key, webhook secret ou DSN completo;
- revisar `git diff` e executar scanner de padrões antes do commit.

**Conclusão:** o destino PSR-4 está definido e os componentes de banco seguro
existentes estão alinhados ao gate. A próxima etapa pode implementar por fatias,
começando pelos value objects, sem realizar uma transpile integral neste estágio.
