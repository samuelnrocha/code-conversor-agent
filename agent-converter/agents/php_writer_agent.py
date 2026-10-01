from pathlib import Path
from typing import Dict

class PhpWriterAgent:
    """
    Agente de escritura da aplicação em PHP 8.4.
    Aplica as melhores práticas modernas do ecossistema PHP (PHP 8.1 - 8.4):
    - declare(strict_types=1);
    - readonly class para DTOs e Value Objects imutáveis
    - Backed Enums fortemente tipados
    - Constructor property promotion
    - Encapsulamento DDD e match expressions
    """

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def write_all(self):
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self._write_composer_json()
        self._write_enums()
        self._write_value_objects()
        self._write_entities()
        self._write_events()
        self._write_strategies()
        self._write_exceptions()
        self._write_aggregates()
        self._write_services()
        self._write_use_cases()
        self._write_infrastructure()
        self._write_security_and_database()
        self._write_runner()
        self._write_tests()

    def _write_file(self, rel_path: str, content: str):
        full_path = self.target_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _write_composer_json(self):
        content = """{
  "name": "conversor/order-billing-system-php",
  "description": "Migrated Order & Billing Processing System in modern PHP 8.4",
  "type": "project",
  "license": "MIT",
  "require": {
    "php": ">=8.4.0",
    "ext-bcmath": "*",
    "ext-json": "*"
  },
  "autoload": {
    "psr-4": {
      "OrderBillingSystem\\\\": "src/"
    }
  },
  "autoload-dev": {
    "psr-4": {
      "OrderBillingSystem\\\\Tests\\\\": "tests/"
    }
  }
}
"""
        self._write_file("composer.json", content)

    def _write_enums(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Enums;

enum OrderStatus: int
{
    case Draft = 1;
    case Confirmed = 2;
    case Paid = 3;
    case Shipped = 4;
    case Cancelled = 5;
    case Refunded = 6;

    public function label(): string
    {
        return match ($this) {
            self::Draft => 'Draft',
            self::Confirmed => 'Confirmed',
            self::Paid => 'Paid',
            self::Shipped => 'Shipped',
            self::Cancelled => 'Cancelled',
            self::Refunded => 'Refunded',
        };
    }
}
"""
        self._write_file("src/Domain/Enums/OrderStatus.php", content)

    def _write_value_objects(self):
        money_content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\ValueObjects;

use InvalidArgumentException;
use LogicException;

final readonly class Money
{
    public float $amount;
    public string $currency;

    public function __construct(float $amount, string $currency = 'BRL')
    {
        if ($amount < 0.0) {
            throw new InvalidArgumentException('Amount cannot be negative.');
        }

        if (trim($currency) === '') {
            throw new InvalidArgumentException('Currency code cannot be empty.');
        }

        $this->amount = round($amount, 2);
        $this->currency = strtoupper(trim($currency));
    }

    public static function zero(string $currency = 'BRL'): self
    {
        return new self(0.0, $currency);
    }

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->amount + $other->amount, $this->currency);
    }

    public function subtract(self $other): self
    {
        $this->ensureSameCurrency($other);
        if ($this->amount < $other->amount) {
            throw new LogicException('Resulting money cannot be negative.');
        }
        return new self($this->amount - $other->amount, $this->currency);
    }

    public function multiply(float|int $multiplier): self
    {
        if ($multiplier < 0) {
            throw new InvalidArgumentException('Multiplier cannot be negative.');
        }
        return new self($this->amount * $multiplier, $this->currency);
    }

    private function ensureSameCurrency(self $other): void
    {
        if ($this->currency !== $other->currency) {
            throw new LogicException(
                sprintf('Cannot operate on different currencies: %s and %s', $this->currency, $other->currency)
            );
        }
    }

    public function __toString(): string
    {
        return sprintf('%s %s', $this->currency, number_format($this->amount, 2, '.', ','));
    }
}
"""
        self._write_file("src/Domain/ValueObjects/Money.php", money_content)

        tax_content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\ValueObjects;

use InvalidArgumentException;
use OutOfRangeException;

final readonly class TaxRate
{
    public string $countryCode;
    public float $ratePercentage;

    public function __construct(string $countryCode, float $ratePercentage)
    {
        if (trim($countryCode) === '') {
            throw new InvalidArgumentException('Country code is required.');
        }

        if ($ratePercentage < 0.0 || $ratePercentage > 100.0) {
            throw new OutOfRangeException('Tax rate must be between 0 and 100.');
        }

        $this->countryCode = strtoupper(trim($countryCode));
        $this->ratePercentage = $ratePercentage;
    }

    public function calculateTax(Money $subtotal): Money
    {
        $taxAmount = $subtotal->amount * ($this->ratePercentage / 100.0);
        return new Money($taxAmount, $subtotal->currency);
    }
}
"""
        self._write_file("src/Domain/ValueObjects/TaxRate.php", tax_content)

    def _write_entities(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Entities;

use InvalidArgumentException;
use OutOfRangeException;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;

final class OrderItem
{
    public function __construct(
        public readonly string $sku,
        public readonly string $name,
        public readonly Money $unitPrice,
        public private(set) int $quantity,
        public private(set) float $discountPercent = 0.0
    ) {
        if (trim($sku) === '') {
            throw new InvalidArgumentException('SKU is required.');
        }

        if (trim($name) === '') {
            throw new InvalidArgumentException('Item name is required.');
        }

        if ($quantity <= 0) {
            throw new OutOfRangeException('Quantity must be greater than zero.');
        }

        if ($discountPercent < 0.0 || $discountPercent > 100.0) {
            throw new OutOfRangeException('Discount must be between 0 and 100.');
        }
    }

    public function calculateGrossTotal(): Money
    {
        return $this->unitPrice->multiply($this->quantity);
    }

    public function calculateDiscountAmount(): Money
    {
        if ($this->discountPercent === 0.0) {
            return Money::zero($this->unitPrice->currency);
        }

        $discount = ($this->unitPrice->amount * $this->quantity) * ($this->discountPercent / 100.0);
        return new Money($discount, $this->unitPrice->currency);
    }

    public function calculateNetTotal(): Money
    {
        return $this->calculateGrossTotal()->subtract($this->calculateDiscountAmount());
    }

    public function updateQuantity(int $newQuantity): void
    {
        if ($newQuantity <= 0) {
            throw new OutOfRangeException('Quantity must be greater than zero.');
        }
        $this->quantity = $newQuantity;
    }
}
"""
        self._write_file("src/Domain/Entities/OrderItem.php", content)

    def _write_events(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Events;

use DateTimeImmutable;
use OrderBillingSystem\\Domain\\Enums\\OrderStatus;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;

interface DomainEvent
{
    public function getEventId(): string;
    public function getOccurredOn(): DateTimeImmutable;
}

abstract readonly class AbstractDomainEvent implements DomainEvent
{
    protected string $eventId;
    protected DateTimeImmutable $occurredOn;

    public function __construct(?DateTimeImmutable $occurredOn = null)
    {
        $this->eventId = bin2hex(random_bytes(16));
        $this->occurredOn = $occurredOn ?? new DateTimeImmutable();
    }

    public function getEventId(): string
    {
        return $this->eventId;
    }

    public function getOccurredOn(): DateTimeImmutable
    {
        return $this->occurredOn;
    }
}

final readonly class OrderCreatedEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}

final readonly class OrderStatusChangedEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public OrderStatus $oldStatus,
        public OrderStatus $newStatus,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}

final readonly class OrderPaidEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public Money $amountPaid,
        public string $transactionId,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}
"""
        self._write_file("src/Domain/Events/DomainEvents.php", content)

    def _write_strategies(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Strategies;

use OrderBillingSystem\\Domain\\ValueObjects\\Money;

interface DiscountStrategy
{
    public function getStrategyName(): string;
    public function applyDiscount(Money $currentSubtotal): Money;
}

final readonly class VipDiscountStrategy implements DiscountStrategy
{
    public function __construct(private float $discountRate = 15.0)
    {
    }

    public function getStrategyName(): string
    {
        return 'VIP Customer Discount';
    }

    public function applyDiscount(Money $currentSubtotal): Money
    {
        $discountAmount = $currentSubtotal->amount * ($this->discountRate / 100.0);
        return new Money($discountAmount, $currentSubtotal->currency);
    }
}

final readonly class CouponDiscountStrategy implements DiscountStrategy
{
    public function __construct(
        private string $couponCode,
        private Money $fixedDiscount
    ) {
    }

    public function getStrategyName(): string
    {
        return "Coupon: {$this->couponCode}";
    }

    public function applyDiscount(Money $currentSubtotal): Money
    {
        if ($currentSubtotal->amount <= $this->fixedDiscount->amount) {
            return $currentSubtotal;
        }

        return $this->fixedDiscount;
    }
}
"""
        self._write_file("src/Domain/Strategies/DiscountStrategies.php", content)

    def _write_exceptions(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Exceptions;

use DomainException as BaseDomainException;

class DomainException extends BaseDomainException
{
}

class InvalidOrderStateException extends DomainException
{
}
"""
        self._write_file("src/Domain/Exceptions/DomainExceptions.php", content)

    def _write_aggregates(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Aggregates;

use DateTimeImmutable;
use InvalidArgumentException;
use LogicException;
use OrderBillingSystem\\Domain\\Entities\\OrderItem;
use OrderBillingSystem\\Domain\\Enums\\OrderStatus;
use OrderBillingSystem\\Domain\\Events\\DomainEvent;
use OrderBillingSystem\\Domain\\Events\\OrderCreatedEvent;
use OrderBillingSystem\\Domain\\Events\\OrderPaidEvent;
use OrderBillingSystem\\Domain\\Events\\OrderStatusChangedEvent;
use OrderBillingSystem\\Domain\\Exceptions\\InvalidOrderStateException;
use OrderBillingSystem\\Domain\\Strategies\\DiscountStrategy;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;
use OrderBillingSystem\\Domain\\ValueObjects\\TaxRate;

final class Order
{
    /** @var array<string, OrderItem> */
    private array $items = [];

    /** @var list<DomainEvent> */
    private array $domainEvents = [];

    /** @var list<DiscountStrategy> */
    private array $discounts = [];

    public private(set) OrderStatus $status;
    public readonly DateTimeImmutable $createdAt;
    public private(set) ?DateTimeImmutable $paidAt = null;

    public function __construct(
        public readonly string $id,
        public readonly string $customerId,
        public readonly TaxRate $taxRate,
        public readonly string $currency = 'BRL'
    ) {
        if (trim($id) === '') {
            throw new InvalidArgumentException('Order ID cannot be empty.');
        }

        if (trim($customerId) === '') {
            throw new InvalidArgumentException('Customer ID cannot be empty.');
        }

        $this->status = OrderStatus::Draft;
        $this->createdAt = new DateTimeImmutable();

        $this->domainEvents[] = new OrderCreatedEvent($this->id, $this->customerId, $this->createdAt);
    }

    /**
     * @return list<OrderItem>
     */
    public function getItems(): array
    {
        return array_values($this->items);
    }

    /**
     * @return list<DomainEvent>
     */
    public function getDomainEvents(): array
    {
        return $this->domainEvents;
    }

    /**
     * @return list<DiscountStrategy>
     */
    public function getAppliedDiscounts(): array
    {
        return $this->discounts;
    }

    public function addItem(OrderItem $item): void
    {
        $this->ensureInStatus(OrderStatus::Draft);

        if (isset($this->items[$item->sku])) {
            $existing = $this->items[$item->sku];
            $existing->updateQuantity($existing->quantity + $item->quantity);
        } else {
            $this->items[$item->sku] = $item;
        }
    }

    public function removeItem(string $sku): void
    {
        $this->ensureInStatus(OrderStatus::Draft);

        if (!isset($this->items[$sku])) {
            throw new LogicException(sprintf('Item with SKU %s not found in order.', $sku));
        }

        unset($this->items[$sku]);
    }

    public function applyDiscount(DiscountStrategy $discountStrategy): void
    {
        $this->ensureInStatus(OrderStatus::Draft);
        $this->discounts[] = $discountStrategy;
    }

    public function calculateGrossSubtotal(): Money
    {
        if (empty($this->items)) {
            return Money::zero($this->currency);
        }

        $totalAmount = 0.0;
        foreach ($this->items as $item) {
            $totalAmount += $item->calculateNetTotal()->amount;
        }

        return new Money($totalAmount, $this->currency);
    }

    public function calculateTotalDiscount(): Money
    {
        $subtotal = $this->calculateGrossSubtotal();
        $totalDiscountAmount = 0.0;

        foreach ($this->discounts as $strategy) {
            $discount = $strategy->applyDiscount($subtotal);
            $totalDiscountAmount += $discount->amount;
        }

        if ($totalDiscountAmount > $subtotal->amount) {
            $totalDiscountAmount = $subtotal->amount;
        }

        return new Money($totalDiscountAmount, $subtotal->currency);
    }

    public function calculateSubtotalAfterDiscounts(): Money
    {
        $gross = $this->calculateGrossSubtotal();
        $discounts = $this->calculateTotalDiscount();
        return $gross->subtract($discounts);
    }

    public function calculateTaxAmount(): Money
    {
        $subtotal = $this->calculateSubtotalAfterDiscounts();
        return $this->taxRate->calculateTax($subtotal);
    }

    public function calculateFinalTotal(): Money
    {
        return $this->calculateSubtotalAfterDiscounts()->add($this->calculateTaxAmount());
    }

    public function confirm(): void
    {
        $this->ensureInStatus(OrderStatus::Draft);

        if (empty($this->items)) {
            throw new InvalidOrderStateException('Cannot confirm an order without items.');
        }

        $this->transitionTo(OrderStatus::Confirmed);
    }

    public function markAsPaid(string $transactionId): void
    {
        $this->ensureInStatus(OrderStatus::Confirmed);

        if (trim($transactionId) === '') {
            throw new InvalidArgumentException('Transaction ID is required to mark as paid.');
        }

        $this->paidAt = new DateTimeImmutable();
        $this->transitionTo(OrderStatus::Paid);

        $this->domainEvents[] = new OrderPaidEvent(
            $this->id,
            $this->calculateFinalTotal(),
            $transactionId,
            $this->paidAt
        );
    }

    public function ship(): void
    {
        $this->ensureInStatus(OrderStatus::Paid);
        $this->transitionTo(OrderStatus::Shipped);
    }

    public function cancel(string $reason): void
    {
        if ($this->status === OrderStatus::Shipped) {
            throw new InvalidOrderStateException('Cannot cancel an order that has already been shipped.');
        }

        if ($this->status === OrderStatus::Cancelled) {
            return;
        }

        $this->transitionTo(OrderStatus::Cancelled);
    }

    public function clearEvents(): void
    {
        $this->domainEvents = [];
    }

    private function ensureInStatus(OrderStatus $required): void
    {
        if ($this->status !== $required) {
            throw new InvalidOrderStateException(
                sprintf("Action requires order status '%s', but current status is '%s'.", $required->label(), $this->status->label())
            );
        }
    }

    private function transitionTo(OrderStatus $newStatus): void
    {
        $old = $this->status;
        $this->status = $newStatus;
        $this->domainEvents[] = new OrderStatusChangedEvent($this->id, $old, $newStatus, new DateTimeImmutable());
    }
}
"""
        self._write_file("src/Domain/Aggregates/Order.php", content)

    def _write_services(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Domain\\Services;

use OrderBillingSystem\\Domain\\Aggregates\\Order;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;

interface OrderRepositoryInterface
{
    public function getById(string $id): ?Order;
    public function save(Order $order): void;
    /** @return list<Order> */
    public function getByCustomerId(string $customerId): array;
}

final readonly class PaymentResult
{
    public function __construct(
        public bool $success,
        public ?string $transactionId = null,
        public ?string $errorMessage = null
    ) {
    }
}

interface PaymentGatewayInterface
{
    public function processPayment(string $orderId, Money $amount, string $paymentMethodToken): PaymentResult;
}

interface NotificationServiceInterface
{
    public function sendOrderConfirmation(string $customerId, string $orderId): void;
    public function sendPaymentReceipt(string $customerId, string $orderId, Money $amount): void;
}
"""
        self._write_file("src/Domain/Services/Contracts.php", content)

    def _write_use_cases(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Application\\UseCases;

use LogicException;
use OrderBillingSystem\\Domain\\Aggregates\\Order;
use OrderBillingSystem\\Domain\\Entities\\OrderItem;
use OrderBillingSystem\\Domain\\Exceptions\\DomainException;
use OrderBillingSystem\\Domain\\Services\\NotificationServiceInterface;
use OrderBillingSystem\\Domain\\Services\\OrderRepositoryInterface;
use OrderBillingSystem\\Domain\\Services\\PaymentGatewayInterface;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;
use OrderBillingSystem\\Domain\\ValueObjects\\TaxRate;

final readonly class CreateOrderCommand
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public string $countryCode,
        public float $taxRatePercentage,
        public string $currency = 'BRL'
    ) {
    }
}

final readonly class AddItemCommand
{
    public function __construct(
        public string $orderId,
        public string $sku,
        public string $name,
        public float $unitPrice,
        public int $quantity,
        public float $discountPercent = 0.0
    ) {
    }
}

final readonly class ProcessOrderPaymentCommand
{
    public function __construct(
        public string $orderId,
        public string $paymentToken
    ) {
    }
}

final class OrderProcessingService
{
    public function __construct(
        private readonly OrderRepositoryInterface $repository,
        private readonly PaymentGatewayInterface $paymentGateway,
        private readonly NotificationServiceInterface $notificationService
    ) {
    }

    public function createOrder(CreateOrderCommand $command): Order
    {
        $taxRate = new TaxRate($command->countryCode, $command->taxRatePercentage);
        $order = new Order($command->orderId, $command->customerId, $taxRate, $command->currency);

        $this->repository->save($order);
        return $order;
    }

    public function addItemToOrder(AddItemCommand $command): Order
    {
        $order = $this->repository->getById($command->orderId);
        if ($order === null) {
            throw new LogicException("Order {$command->orderId} not found.");
        }

        $unitPrice = new Money($command->unitPrice, $order->calculateGrossSubtotal()->currency);
        $item = new OrderItem($command->sku, $command->name, $unitPrice, $command->quantity, $command->discountPercent);

        $order->addItem($item);
        $this->repository->save($order);
        return $order;
    }

    public function confirmOrder(string $orderId): Order
    {
        $order = $this->repository->getById($orderId);
        if ($order === null) {
            throw new LogicException("Order {$orderId} not found.");
        }

        $order->confirm();
        $this->repository->save($order);
        $this->notificationService->sendOrderConfirmation($order->customerId, $order->id);

        return $order;
    }

    public function processPayment(ProcessOrderPaymentCommand $command): Order
    {
        $order = $this->repository->getById($command->orderId);
        if ($order === null) {
            throw new LogicException("Order {$command->orderId} not found.");
        }

        $total = $order->calculateFinalTotal();
        $result = $this->paymentGateway->processPayment($order->id, $total, $command->paymentToken);

        if (!$result->success) {
            throw new DomainException("Payment failed for order {$order->id}: {$result->errorMessage}");
        }

        $order->markAsPaid($result->transactionId);
        $this->repository->save($order);
        $this->notificationService->sendPaymentReceipt($order->customerId, $order->id, $total);

        return $order;
    }
}
"""
        self._write_file("src/Application/UseCases/OrderProcessingService.php", content)

    def _write_infrastructure(self):
        content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Infrastructure;

use OrderBillingSystem\\Domain\\Aggregates\\Order;
use OrderBillingSystem\\Domain\\Services\\NotificationServiceInterface;
use OrderBillingSystem\\Domain\\Services\\OrderRepositoryInterface;
use OrderBillingSystem\\Domain\\Services\\PaymentGatewayInterface;
use OrderBillingSystem\\Domain\\Services\\PaymentResult;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;

final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */
    private array $orders = [];

    public function getById(string $id): ?Order
    {
        return $this->orders[$id] ?? null;
    }

    public function save(Order $order): void
    {
        $this->orders[$order->id] = $order;
    }

    public function getByCustomerId(string $customerId): array
    {
        return array_values(
            array_filter($this->orders, fn(Order $o) => $o->customerId === $customerId)
        );
    }
}

final class MockPaymentGateway implements PaymentGatewayInterface
{
    public function processPayment(string $orderId, Money $amount, string $paymentMethodToken): PaymentResult
    {
        if ($paymentMethodToken === 'invalid_token') {
            return new PaymentResult(false, null, 'Card declined: Invalid test token.');
        }

        $txId = 'tx_' . substr(bin2hex(random_bytes(8)), 0, 12);
        return new PaymentResult(true, $txId, null);
    }
}

final class ConsoleNotificationService implements NotificationServiceInterface
{
    /** @var list<string> */
    public array $notifications = [];

    public function sendOrderConfirmation(string $customerId, string $orderId): void
    {
        $msg = "[NOTIFICATION] Order {$orderId} confirmed for customer {$customerId}.";
        $this->notifications[] = $msg;
        echo $msg . PHP_EOL;
    }

    public function sendPaymentReceipt(string $customerId, string $orderId, Money $amount): void
    {
        $msg = "[NOTIFICATION] Payment receipt: Order {$orderId} paid {$amount} for customer {$customerId}.";
        $this->notifications[] = $msg;
        echo $msg . PHP_EOL;
    }
}
"""
        self._write_file("src/Infrastructure/Implementations.php", content)

    def _write_security_and_database(self):
        db_config_content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Infrastructure\\Database;

use InvalidArgumentException;

/**
 * Configuração Segura de Banco de Dados.
 * - Carrega credenciais exclusivamente de variáveis de ambiente.
 * - Implementa __debugInfo() para NUNCA exibir a senha em var_dump(), print_r() ou logs.
 */
final readonly class DatabaseConfig
{
    public string $driver;
    public string $host;
    public int $port;
    public string $database;
    public string $user;
    private string $password;

    public function __construct(
        ?string $host = null,
        ?string $database = null,
        ?string $user = null,
        ?string $password = null,
        int $port = 3306,
        string $driver = 'mysql'
    ) {
        $this->driver = $driver;
        $this->host = $host ?? (getenv('DB_HOST') ?: '127.0.0.1');
        $this->database = $database ?? (getenv('DB_NAME') ?: 'order_billing_db');
        $this->user = $user ?? (getenv('DB_USER') ?: 'db_order_user');
        $this->password = $password ?? (getenv('DB_PASSWORD') ?: '');
        $this->port = (int) ($port ?: (getenv('DB_PORT') ?: 3306));

        if (trim($this->host) === '' || trim($this->database) === '') {
            throw new InvalidArgumentException('Database host and database name cannot be empty.');
        }
    }

    public function getDsn(): string
    {
        if ($this->driver === 'sqlite') {
            return "sqlite:{$this->database}";
        }
        return "{$this->driver}:host={$this->host};port={$this->port};dbname={$this->database};charset=utf8mb4";
    }

    public function getUser(): string
    {
        return $this->user;
    }

    public function getPassword(): string
    {
        return $this->password;
    }

    /**
     * CAMADA DE SEGURANÇA: Mascaramento ativo de credenciais.
     * Retorna array seguro quando inspecionado em debug/logs.
     */
    public function __debugInfo(): array
    {
        return [
            'driver' => $this->driver,
            'host' => $this->host,
            'port' => $this->port,
            'database' => $this->database,
            'user' => $this->user,
            'password' => '******** (REDACTED)',
        ];
    }
}
"""
        self._write_file("src/Infrastructure/Database/DatabaseConfig.php", db_config_content)

        safe_conn_content = """<?php

declare(strict_types=1);

namespace OrderBillingSystem\\Infrastructure\\Database;

use PDO;
use PDOException;
use RuntimeException;

/**
 * Conexão Segura com Banco de Dados via PDO.
 * Camadas de proteção:
 * 1. Força PDO::ATTR_EMULATE_PREPARES => false (previne SQL Injection no driver).
 * 2. Trata PDOException mascarando DSN, usuário e senha da mensagem de erro e do stack trace.
 * 3. Encoraja execução parametrizada nativa.
 */
final class SafeDatabaseConnection
{
    private ?PDO $pdo = null;

    public function __construct(private readonly DatabaseConfig $config)
    {
    }

    public function getPdo(): PDO
    {
        if ($this->pdo === null) {
            $this->connect();
        }
        return $this->pdo;
    }

    private function connect(): void
    {
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_PERSISTENT => false,
        ];

        try {
            $this->pdo = new PDO(
                $this->config->getDsn(),
                $this->config->getUser(),
                $this->config->getPassword(),
                $options
            );
        } catch (PDOException $e) {
            // CAMADA DE SEGURANÇA: Sanitização de exceção
            // Remove qualquer vestígio de senha ou host interno antes de propagar o erro
            throw new RuntimeException(
                "Database connection error [ERR_DB_AUTHENTICATION_OR_NETWORK]. Details redacted for security.",
                500
            );
        }
    }

    /**
     * Executa query usando exclusivamente prepared statements.
     */
    public function executePrepared(string $sql, array $params = []): array
    {
        $stmt = $this->getPdo()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }
}
"""
        self._write_file("src/Infrastructure/Database/SafeDatabaseConnection.php", safe_conn_content)

    def _write_runner(self):
        content = """<?php

declare(strict_types=1);

// PSR-4 Autoloader fallback without composer
spl_autoload_register(function ($class) {
    $prefix = 'OrderBillingSystem\\\\';
    $baseDir = __DIR__ . '/../src/';
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }
    $relativeClass = substr($class, $len);
    $file = $baseDir . str_replace('\\\\', '/', $relativeClass) . '.php';
    if (file_exists($file)) {
        require_once $file;
    }
});

// Require files with multiple declarations
require_once __DIR__ . '/../src/Domain/Events/DomainEvents.php';
require_once __DIR__ . '/../src/Domain/Strategies/DiscountStrategies.php';
require_once __DIR__ . '/../src/Domain/Exceptions/DomainExceptions.php';
require_once __DIR__ . '/../src/Domain/Services/Contracts.php';
require_once __DIR__ . '/../src/Infrastructure/Implementations.php';
require_once __DIR__ . '/../src/Infrastructure/Database/DatabaseConfig.php';
require_once __DIR__ . '/../src/Infrastructure/Database/SafeDatabaseConnection.php';

use OrderBillingSystem\\Application\\UseCases\\AddItemCommand;
use OrderBillingSystem\\Application\\UseCases\\CreateOrderCommand;
use OrderBillingSystem\\Application\\UseCases\\OrderProcessingService;
use OrderBillingSystem\\Application\\UseCases\\ProcessOrderPaymentCommand;
use OrderBillingSystem\\Domain\\Strategies\\VipDiscountStrategy;
use OrderBillingSystem\\Infrastructure\\ConsoleNotificationService;
use OrderBillingSystem\\Infrastructure\\Database\\DatabaseConfig;
use OrderBillingSystem\\Infrastructure\\InMemoryOrderRepository;
use OrderBillingSystem\\Infrastructure\\MockPaymentGateway;

echo "=================================================" . PHP_EOL;
echo "  PHP 8.4 Order & Billing Processing System (Migrated)" . PHP_EOL;
echo "=================================================" . PHP_EOL;

// Camada de Segurança: Leitura segura de variáveis do .env caso exista
$envFile = __DIR__ . '/../.env';
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $trimmed = trim($line);
        if (str_starts_with($trimmed, '#') || !str_contains($trimmed, '=')) {
            continue;
        }
        [$k, $v] = explode('=', $trimmed, 2);
        putenv(trim($k) . '=' . trim($v));
        $_ENV[trim($k)] = trim($v);
    }
}

// Camada de Segurança: Carregamento de credenciais do ambiente com mascaramento
$dbConfig = new DatabaseConfig();
echo sprintf(
    "[SECURITY LAYER] Database config loaded: host=%s, db=%s, user=%s (pwd=%s)\\n",
    $dbConfig->host,
    $dbConfig->database,
    $dbConfig->user,
    $dbConfig->__debugInfo()['password']
);

$repo = new InMemoryOrderRepository();
$paymentGateway = new MockPaymentGateway();
$notifications = new ConsoleNotificationService();
$service = new OrderProcessingService($repo, $paymentGateway, $notifications);

// 1. Create order
$order = $service->createOrder(new CreateOrderCommand('ORD-2026-001', 'CUST-99', 'BR', 12.0, 'BRL'));
echo sprintf("Created order %s with status: %s\\n", $order->id, $order->status->label());

// 2. Add items
$service->addItemToOrder(new AddItemCommand('ORD-2026-001', 'SKU-TECH-01', 'Enterprise Cloud Server', 1200.00, 2, 5.0));
$service->addItemToOrder(new AddItemCommand('ORD-2026-001', 'SKU-TECH-02', 'SSD NVMe 2TB Enterprise', 450.00, 4, 0.0));

// 3. Apply VIP discount
$order->applyDiscount(new VipDiscountStrategy(10.0));

echo sprintf("Gross Subtotal: %s\\n", $order->calculateGrossSubtotal());
echo sprintf("Total Discount: %s\\n", $order->calculateTotalDiscount());
echo sprintf("Subtotal After Discount: %s\\n", $order->calculateSubtotalAfterDiscounts());
echo sprintf("Tax Amount (12%%): %s\\n", $order->calculateTaxAmount());
echo sprintf("Final Total: %s\\n", $order->calculateFinalTotal());

// 4. Confirm order
$service->confirmOrder('ORD-2026-001');
echo sprintf("Confirmed order status: %s\\n", $order->status->label());

// 5. Pay order
$service->processPayment(new ProcessOrderPaymentCommand('ORD-2026-001', 'valid_token_abc'));
echo sprintf("Final order status: %s (PaidAt: %s)\\n", $order->status->label(), $order->paidAt?->format('Y-m-d H:i:s'));
echo sprintf("Domain events raised: %d\\n", count($order->getDomainEvents()));

echo "PHP 8.4 system execution completed successfully." . PHP_EOL;
"""
        self._write_file("bin/run.php", content)

    def _write_tests(self):
        content = """<?php

declare(strict_types=1);

// PSR-4 Autoloader
spl_autoload_register(function ($class) {
    $prefix = 'OrderBillingSystem\\\\';
    $baseDir = __DIR__ . '/../src/';
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }
    $relativeClass = substr($class, $len);
    $file = $baseDir . str_replace('\\\\', '/', $relativeClass) . '.php';
    if (file_exists($file)) {
        require_once $file;
    }
});

require_once __DIR__ . '/../src/Domain/Events/DomainEvents.php';
require_once __DIR__ . '/../src/Domain/Strategies/DiscountStrategies.php';
require_once __DIR__ . '/../src/Domain/Exceptions/DomainExceptions.php';
require_once __DIR__ . '/../src/Domain/Services/Contracts.php';
require_once __DIR__ . '/../src/Infrastructure/Database/DatabaseConfig.php';
require_once __DIR__ . '/../src/Infrastructure/Database/SafeDatabaseConnection.php';

use InvalidArgumentException;
use LogicException;
use RuntimeException;
use OrderBillingSystem\\Domain\\Aggregates\\Order;
use OrderBillingSystem\\Domain\\Entities\\OrderItem;
use OrderBillingSystem\\Domain\\Enums\\OrderStatus;
use OrderBillingSystem\\Domain\\Exceptions\\InvalidOrderStateException;
use OrderBillingSystem\\Domain\\Strategies\\VipDiscountStrategy;
use OrderBillingSystem\\Domain\\ValueObjects\\Money;
use OrderBillingSystem\\Domain\\ValueObjects\\TaxRate;
use OrderBillingSystem\\Infrastructure\\Database\\DatabaseConfig;
use OrderBillingSystem\\Infrastructure\\Database\\SafeDatabaseConnection;

final class TestRunner
{
    private int $passed = 0;
    private int $failed = 0;
    private array $failures = [];

    public function run(): bool
    {
        $methods = get_class_methods($this);
        foreach ($methods as $method) {
            if (str_starts_with($method, 'test')) {
                try {
                    $this->$method();
                    $this->passed++;
                    echo "  [PASS] {$method}\\n";
                } catch (Throwable $e) {
                    $this->failed++;
                    $this->failures[] = "[FAIL] {$method}: {$e->getMessage()} at {$e->getFile()}:{$e->getLine()}";
                    echo "  [FAIL] {$method}: {$e->getMessage()}\\n";
                }
            }
        }

        echo "\\n=========================================\\n";
        echo "Test Results: {$this->passed} passed, {$this->failed} failed\\n";
        echo "=========================================\\n";

        return $this->failed === 0;
    }

    private function defaultTaxRate(): TaxRate
    {
        return new TaxRate('BR', 10.0);
    }

    public function testOrderCreationShouldInitializeInDraftStatusWithCreatedEvent(): void
    {
        $order = new Order('ORD-001', 'CUST-01', $this->defaultTaxRate());

        assert($order->id === 'ORD-001', 'ID must match');
        assert($order->customerId === 'CUST-01', 'Customer ID must match');
        assert($order->status === OrderStatus::Draft, 'Initial status must be Draft');
        assert(count($order->getDomainEvents()) === 1, 'Should have 1 created event');
    }

    public function testAddItemShouldAccumulateQuantityWhenSkuAlreadyExists(): void
    {
        $order = new Order('ORD-001', 'CUST-01', $this->defaultTaxRate());
        $item1 = new OrderItem('SKU-1', 'Laptop', new Money(1000.0), 1);
        $item2 = new OrderItem('SKU-1', 'Laptop', new Money(1000.0), 2);

        $order->addItem($item1);
        $order->addItem($item2);

        $items = $order->getItems();
        assert(count($items) === 1, 'Items count should be 1');
        assert($items[0]->quantity === 3, 'Accumulated quantity should be 3');
        assert($order->calculateGrossSubtotal()->amount === 3000.0, 'Subtotal should be 3000.0');
    }

    public function testItemDiscountShouldBeCalculatedCorrectly(): void
    {
        $item = new OrderItem('SKU-A', 'Keyboard', new Money(100.0), 2, 10.0);

        assert($item->calculateGrossTotal()->amount === 200.0, 'Gross total should be 200');
        assert($item->calculateDiscountAmount()->amount === 20.0, 'Discount amount should be 20');
        assert($item->calculateNetTotal()->amount === 180.0, 'Net total should be 180');
    }

    public function testOrderDiscountsAndTaxesShouldComputeExactTotals(): void
    {
        $order = new Order('ORD-100', 'CUST-10', new TaxRate('BR', 10.0));
        $order->addItem(new OrderItem('SKU-X', 'Monitor', new Money(500.0), 2));

        $order->applyDiscount(new VipDiscountStrategy(10.0));

        assert($order->calculateGrossSubtotal()->amount === 1000.0, 'Gross subtotal should be 1000');
        assert($order->calculateTotalDiscount()->amount === 100.0, 'Total discount should be 100');
        assert($order->calculateSubtotalAfterDiscounts()->amount === 900.0, 'Subtotal after discount should be 900');
        assert($order->calculateTaxAmount()->amount === 90.0, 'Tax amount should be 90');
        assert($order->calculateFinalTotal()->amount === 990.0, 'Final total should be 990');
    }

    public function testConfirmShouldThrowWhenOrderHasNoItems(): void
    {
        $order = new Order('ORD-EMPTY', 'CUST-01', $this->defaultTaxRate());

        $thrown = false;
        try {
            $order->confirm();
        } catch (InvalidOrderStateException) {
            $thrown = true;
        }

        assert($thrown, 'Expected InvalidOrderStateException when confirming empty order');
    }

    public function testFullOrderLifecycleShouldProgressStatusCorrectly(): void
    {
        $order = new Order('ORD-FLOW', 'CUST-FLOW', $this->defaultTaxRate());
        $order->addItem(new OrderItem('SKU-1', 'Mouse', new Money(50.0), 1));

        $order->confirm();
        assert($order->status === OrderStatus::Confirmed, 'Status should be Confirmed');

        $order->markAsPaid('TX-998877');
        assert($order->status === OrderStatus::Paid, 'Status should be Paid');
        assert($order->paidAt !== null, 'PaidAt should not be null');

        $order->ship();
        assert($order->status === OrderStatus::Shipped, 'Status should be Shipped');
    }

    public function testCancelShouldThrowWhenOrderAlreadyShipped(): void
    {
        $order = new Order('ORD-SHIP', 'CUST-01', $this->defaultTaxRate());
        $order->addItem(new OrderItem('SKU-1', 'Mouse', new Money(50.0), 1));
        $order->confirm();
        $order->markAsPaid('TX-123');
        $order->ship();

        $thrown = false;
        try {
            $order->cancel('Changed mind');
        } catch (InvalidOrderStateException) {
            $thrown = true;
        }

        assert($thrown, 'Expected InvalidOrderStateException when cancelling shipped order');
    }

    public function testMoneyOperationsShouldPreserveInvariants(): void
    {
        $m1 = new Money(100.50, 'USD');
        $m2 = new Money(50.25, 'USD');

        $sum = $m1->add($m2);
        assert($sum->amount === 150.75, 'Sum amount should be 150.75');
        assert($sum->currency === 'USD', 'Sum currency should be USD');

        $diff = $m1->subtract($m2);
        assert($diff->amount === 50.25, 'Diff amount should be 50.25');

        $mult = $m2->multiply(2);
        assert($mult->amount === 100.50, 'Multiplication amount should be 100.50');

        $argExceptionThrown = false;
        try {
            new Money(-1.0);
        } catch (InvalidArgumentException) {
            $argExceptionThrown = true;
        }
        assert($argExceptionThrown, 'Should reject negative money amount');

        $currExceptionThrown = false;
        try {
            $m1->add(new Money(10.0, 'EUR'));
        } catch (LogicException) {
            $currExceptionThrown = true;
        }
        assert($currExceptionThrown, 'Should reject different currencies');
    }

    public function testDatabaseConfigShouldMaskPasswordInDebugInfo(): void
    {
        $config = new DatabaseConfig(
            host: 'db.production.internal',
            database: 'finance_orders',
            user: 'master_user',
            password: 'UltraSecretPassword!987#'
        );

        $debug = $config->__debugInfo();
        assert($debug['password'] === '******** (REDACTED)', 'Debug password must be redacted');
        assert(!str_contains(print_r($debug, true), 'UltraSecretPassword!987#'), 'print_r must not leak raw password');
        assert($config->getPassword() === 'UltraSecretPassword!987#', 'Accessor must return actual password for internal PDO');
    }

    public function testDatabaseConnectionFailureShouldRedactCredentials(): void
    {
        $config = new DatabaseConfig(
            host: '127.0.0.1',
            database: 'non_existent_db',
            user: 'test_user',
            password: 'SecretDbPassword123!',
            port: 59999
        );

        $conn = new SafeDatabaseConnection($config);
        $caught = false;
        try {
            $conn->getPdo();
        } catch (RuntimeException $e) {
            $caught = true;
            assert(!str_contains($e->getMessage(), 'SecretDbPassword123!'), 'Exception message must never leak password');
            assert(!str_contains($e->getMessage(), 'test_user'), 'Exception message must redact credentials');
        }

        assert($caught, 'SafeDatabaseConnection must throw sanitized RuntimeException on connection failure');
    }
}

$runner = new TestRunner();
$success = $runner->run();
exit($success ? 0 : 1);
"""
        self._write_file("tests/OrderAggregateTest.php", content)
