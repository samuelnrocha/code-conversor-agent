# Matriz de Mapeamento C# (.NET 8) para PHP 8.4

Este documento estabelece o contrato de tradução semântica utilizado pelo **MappingAgent** e pelo **PhpWriterAgent** para garantir preservação estrita de invariantes de negócio e tipos.

---

## 1. Mapeamento de Primitivas e Construtos de Linguagem

| Recurso em C# (.NET 8) | Equivalente em PHP 8.4 | Justificativa Arquitetural & Invariante |
| :--- | :--- | :--- |
| **`record class` / `record struct`** | `final readonly class` | Garante imutabilidade superficial e profunda, além de semântica de Value Object. |
| **Primary Constructors (`public class Order(string id)`)** | **Constructor Property Promotion (`public function __construct(public string $id)`)** | Reduz boilerplate mantendo a tipagem estrita no momento de instanciação. |
| **`decimal` (Precisão monetária de 128 bits)** | **Value Object `Money` com aritmética em ponto flutuante escalonada ou `bcmath`** | O tipo primitivo `float` do PHP sofre de drift binário IEEE 754. Encapsular em `Money` impede arredondamentos indevidos. |
| **Sobrecarga de Operadores (`+`, `-`, `*`)** | **Métodos explícitos (`add()`, `subtract()`, `multiply()`)** | O PHP não suporta sobrecarga de operadores para classes de usuário. A semântica explícita mantém a legibilidade e previne bugs silenciosos. |
| **Backed Enums com Métodos (`enum OrderStatus`)** | **Backed Enums (`enum OrderStatus: string`) com métodos auxiliares** | PHP 8.1+ suporta enums com valores associados e métodos nativos, fornecendo paridade total de máquina de estados. |
| **Nullable Reference Types (`string?`)** | **Tipos anuláveis (`?string`) e uniões de tipo** | O motor de tipos do PHP 8.4 valida nulos em tempo de execução via `strict_types=1`. |
| **Domain Events (`IReadOnlyCollection<IDomainEvent>`)** | **Array tipado no PHPDoc (`list<DomainEvent>`) com accessor imutável** | Preserva o padrão de eventos de domínio sem acoplamento a bibliotecas externas. |
| **Tratamento de Exceções (`InvalidOrderStateException`)** | **Herança de `DomainException`** | Mantém a taxonomia de erros de domínio separada de exceções de infraestrutura. |

---

## 2. Exemplo Comparativo Lado a Lado: Value Object `Money`

### Em C# (.NET 8):
```csharp
public sealed record Money(decimal Amount, string Currency = "BRL")
{
    public static Money Zero(string currency = "BRL") => new(0m, currency);

    public Money Add(Money other)
    {
        EnsureSameCurrency(other);
        return this with { Amount = Amount + other.Amount };
    }

    public static Money operator +(Money left, Money right) => left.Add(right);
}
```

### Em PHP 8.4:
```php
declare(strict_types=1);

namespace OrderBillingSystem\Domain\ValueObjects;

use InvalidArgumentException;
use LogicException;

final readonly class Money
{
    public float $amount;
    public string $currency;

    public function __construct(float $amount, string $currency = 'BRL')
    {
        if ($amount < 0.0) {
            throw new InvalidArgumentException('Money amount cannot be negative.');
        }
        $this->amount = round($amount, 4);
        $this->currency = strtoupper(trim($currency));
    }

    public function add(Money $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->amount + $other->amount, $this->currency);
    }
}
```
