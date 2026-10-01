# Relatório de Compatibilidade Técnica — .NET 8 → PHP 8.4

**Projeto analisado:** `source-dotnet-app/OrderBillingSystem.sln`  
**Data da análise:** 2026-10-01  
**Escopo:** análise estática de fontes `.cs`, `.csproj` e configuração; nenhuma migração de código foi realizada.

## 1. Veredito executivo

**Viabilidade: POSSÍVEL FAZER.** O projeto é um domínio de pedidos/faturamento pequeno, multiplataforma e sem dependências de UI, Windows, COM, P/Invoke ou bibliotecas binárias proprietárias. A lógica pode ser portada para PHP 8.4 com alta fidelidade usando classes imutáveis, enums nativos, interfaces, exceções e uma camada de persistência/serviços substituível.

**Score de compatibilidade estimado: 96%**

O desconto de 4 pontos não representa blocker: decorre principalmente da necessidade de substituir `Task`/`async`, `ConcurrentDictionary`, LINQ, semântica de `decimal`/arredondamento e operadores sobrecarregados por convenções explícitas em PHP, além de definir uma solução de persistência e integração de pagamento reais. O score assume uma aplicação PHP 8.4 de backend/CLI e não exige equivalência de runtime byte a byte.

## 2. Inventário analisado

### Núcleo de domínio (`OrderBillingSystem.Core`)

- `Aggregates/Order.cs`: aggregate root `Order`, máquina de estados, itens, descontos e eventos de domínio.
- `Entities/OrderItem.cs`: entidade com quantidade e desconto percentual.
- `ValueObjects/Money.cs`: record, `decimal`, arredondamento monetário e operadores `+`, `-`, `*`.
- `ValueObjects/TaxRate.cs`: record/value object de imposto.
- `Enums/OrderStatus.cs`: enum de estado (`Draft`, `Confirmed`, `Paid`, `Shipped`, `Cancelled`, `Refunded`).
- `Events/OrderEvents.cs`: contrato `IDomainEvent` e três records de eventos.
- `Services/Contracts.cs`: `IOrderRepository`, `IPaymentGateway`, `INotificationService` e `PaymentResult`.
- `Strategies/DiscountStrategies.cs`: estratégia de desconto, VIP e cupom fixo.
- `UseCases/OrderProcessingService.cs`: comandos record e orquestração assíncrona do caso de uso.
- `Exceptions/DomainException.cs`: exceções de domínio e de estado inválido.

### Aplicação e testes

- `App/Infrastructure/Implementations.cs`: repositório em memória concorrente, gateway de pagamento mock e notificações em console.
- `App/Program.cs`: composição manual de dependências e cenário demonstrativo completo.
- `Tests/OrderAggregateTests.cs`: 8 testes xUnit cobrindo criação, itens, descontos/impostos, transições e invariantes de dinheiro.

### Projeto e dependências

- Core e App têm target `net8.0`, `Nullable=enable` e `ImplicitUsings=enable`.
- App referencia somente o projeto Core; não há PackageReference de produção.
- Tests usa `xunit 2.5.3`, `xunit.runner.visualstudio 2.5.3`, `Microsoft.NET.Test.Sdk 17.8.0` e `coverlet.collector 6.0.0`.
- `appsettings.json` contém configuração de banco e pagamento, mas não é consumida pelo código demonstrativo atual.
- Artefatos `bin/` e `obj/` foram encontrados, mas não fazem parte do código-fonte necessário à conversão.

## 3. Recursos identificados e mapeamento PHP 8.4

| Recurso .NET observado | Local | Equivalente recomendado em PHP 8.4 | Risco |
|---|---|---|---|
| Records imutáveis/value objects | `Money`, `TaxRate`, eventos, comandos, `PaymentResult` | `final readonly class` com constructor property promotion; validação no construtor | Baixo |
| Enum CLR | `OrderStatus` | `enum OrderStatus: string` (ou `int` se for necessário preservar os valores 1–6), com métodos auxiliares | Baixo |
| `decimal` monetário | Money, impostos, descontos | `Money` encapsulado; evitar `float`; usar escala inteira em centavos ou biblioteca decimal/BCMath com arredondamento explícito | Médio |
| Sobrecarga `+`, `-`, `*` | `Money` | Métodos semânticos `add()`, `subtract()`, `multiply()`; validar moeda e não-negatividade | Baixo |
| Interfaces/DI | contratos de repositório, pagamento, notificações e estratégias | `interface`, classes concretas e composição via container/factory | Baixo |
| Nullable reference types | `Order?`, `string?`, `DateTime?`, null-forgiving `!` | Tipos `?`, validações de entrada e retorno `?`; não há null-safety automática equivalente | Médio |
| Coleções somente leitura | `IReadOnlyCollection<T>`, `IReadOnlyList<T>` | cópias defensivas e arrays expostos como `list`/iterables; não retornar o array interno mutável | Baixo |
| Eventos de domínio | `IDomainEvent`, `Order*Event` | interface/marker, `final readonly class`, UUID e `DateTimeImmutable`; dispatcher opcional | Baixo |
| Async/Tasks | use case, repositório e gateways | chamadas síncronas para implementação simples; adaptador HTTP/queue assíncrono quando necessário | Médio |
| LINQ | `FirstOrDefault`, `Any`, `Sum`, `Where`, `ToList` | `foreach`, `array_filter`, `array_reduce` ou Collections de framework | Baixo |
| Concorrência | `ConcurrentDictionary` | repositório em memória não deve ser assumido como concorrente em PHP-FPM; para produção usar DB/transações/lock | Médio |
| Exceções | `ArgumentException`, `InvalidOperationException`, exceções de domínio | `InvalidArgumentException`, `LogicException`/`RuntimeException` e exceções de domínio próprias | Baixo |

## 4. Comportamento de domínio a preservar

1. Pedido nasce em `Draft` e gera `OrderCreatedEvent`.
2. `AddItem` acumula quantidade pelo mesmo SKU e só é permitido em `Draft`.
3. Subtotal é a soma dos totais líquidos dos itens.
4. Descontos são acumulados e limitados ao subtotal bruto.
5. Imposto é calculado sobre o subtotal após descontos.
6. Fluxo normal: `Draft → Confirmed → Paid → Shipped`; cancelamento é proibido após envio e idempotente se já cancelado.
7. Pagamento falho gera `DomainException`; pagamento bem-sucedido gera evento e notificação.
8. Moedas diferentes não podem ser somadas/subtraídas; valores negativos são rejeitados.

## 5. Blockers de plataforma

**Nenhum blocker de plataforma foi detectado.** Não há ocorrências de:

- `System.Runtime.InteropServices`, P/Invoke, `user32.dll` ou APIs nativas Windows;
- Windows Forms, WPF ou Avalonia;
- COM, ActiveX ou dependências binárias proprietárias;
- chamadas a filesystem/registry/serviços exclusivos de Windows.

As implementações atuais são console, memória, `Guid`, data/hora e coleções padrão, todos portáveis. O mock de pagamento deverá ser substituído por um cliente HTTP PHP (e o repositório em memória por PDO/ORM) se o objetivo for produção.

## 6. Riscos e pontos de atenção antes da migração

### Precisão monetária (prioridade alta)

PHP não oferece um tipo nativo equivalente a C# `decimal`. `float` não é aceitável para preservar os testes e invariantes. Implementar `Money` com centavos inteiros quando a moeda permitir 2 casas, ou BCMath/uma biblioteca decimal para precisão arbitrária. Reproduzir `MidpointRounding.AwayFromZero` explicitamente; documentar escala por moeda.

### Nulabilidade e contratos

`PaymentResult.TransactionId` é nullable, mas o fluxo usa `result.TransactionId!` depois de testar apenas `Success`. A porta deve validar que sucesso implica transaction ID não nulo, em vez de confiar em um operador equivalente ao null-forgiving. `GetByIdAsync` retorna ausência como null.

### Assíncrono e concorrência

`Task` não tem equivalente direto necessário no PHP síncrono tradicional. Se a aplicação for HTTP, chamadas podem ser síncronas dentro da requisição; se houver workers/eventos, escolher ReactPHP, Swoole ou fila. Não transportar `ConcurrentDictionary` como garantia de concorrência: usar transações e restrições no banco.

### Inconsistências/decisões funcionais observadas

- `AddItemToOrderAsync` obtém a moeda de `CalculateGrossSubtotal()`. Em um pedido vazio isso devolve `BRL`, portanto um pedido criado em outra moeda perde a moeda configurada no primeiro item. Corrigir antes ou durante a migração usando a moeda do pedido.
- `Order.Cancel(string reason)` recebe `reason`, mas não o usa nem o inclui em evento; decidir se deve ser persistido/auditado.
- `Refunded` existe no enum, mas não há transição ou caso de uso de reembolso.
- O desconto de cupom retorna o subtotal inteiro quando o cupom é maior/igual ao subtotal; isso é intencionalmente equivalente a desconto limitado, mas deve ser coberto por teste.
- A soma de estratégias é calculada sobre o mesmo subtotal bruto, não de forma sequencial; preservar essa semântica salvo mudança de requisito.
- `TaxRate` valida país e taxa, mas não verifica compatibilidade entre país e moeda.

## 7. Configuração e segurança

`source-dotnet-app/OrderBillingSystem.App/appsettings.json` contém credenciais aparentes em texto claro: senha de banco, API key e webhook secret. Isso não é blocker de compatibilidade, mas é um **risco crítico de segurança e migração**. Não copiar esses valores para PHP, commits, testes ou relatório operacional. Rotacionar/revogar os segredos, removê-los do histórico se já versionados, usar variáveis de ambiente/cofre de segredos e garantir permissões restritas. O valor `appsettings.json` também não é lido pelo `Program.cs` atual, indicando configuração preparada mas não integrada.

## 8. Plano recomendado de migração (sem execução nesta etapa)

1. Definir PSR-4 e separar `Domain`, `Application`, `Infrastructure` e `Tests`.
2. Portar primeiro `Money`, `TaxRate`, `OrderStatus` e exceções, com testes de arredondamento/moeda.
3. Portar `OrderItem`, `Order` e eventos preservando invariantes e cópias defensivas.
4. Portar contratos, comandos e `OrderProcessingService` com injeção de dependências.
5. Implementar repositório PDO transacional e adaptadores de pagamento/notificação; manter mocks para testes.
6. Converter os testes xUnit para PHPUnit ou Pest, mantendo os 8 cenários atuais e adicionando casos de moeda não-BRL, null de transação, limites e arredondamento.
7. Remover segredos do JSON, configurar `.env`/cofre e executar auditoria de dependências.

## 9. Conclusão

O domínio é altamente compatível com PHP 8.4 e não possui bloqueadores de plataforma. A migração é recomendada, desde que a implementação trate precisão monetária, concorrência/persistência, nulabilidade e gestão dos segredos de configuração. Este relatório é exclusivamente de análise; nenhum arquivo de código-fonte foi convertido.
