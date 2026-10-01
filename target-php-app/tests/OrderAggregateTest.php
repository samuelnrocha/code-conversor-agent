<?php

declare(strict_types=1);

// PSR-4 Autoloader
spl_autoload_register(function ($class) {
    $prefix = 'OrderBillingSystem\\';
    $baseDir = __DIR__ . '/../src/';
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }
    $relativeClass = substr($class, $len);
    $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';
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
use OrderBillingSystem\Domain\Aggregates\Order;
use OrderBillingSystem\Domain\Entities\OrderItem;
use OrderBillingSystem\Domain\Enums\OrderStatus;
use OrderBillingSystem\Domain\Exceptions\InvalidOrderStateException;
use OrderBillingSystem\Domain\Strategies\VipDiscountStrategy;
use OrderBillingSystem\Domain\ValueObjects\Money;
use OrderBillingSystem\Domain\ValueObjects\TaxRate;
use OrderBillingSystem\Infrastructure\Database\DatabaseConfig;
use OrderBillingSystem\Infrastructure\Database\SafeDatabaseConnection;

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
                    echo "  [PASS] {$method}\n";
                } catch (Throwable $e) {
                    $this->failed++;
                    $this->failures[] = "[FAIL] {$method}: {$e->getMessage()} at {$e->getFile()}:{$e->getLine()}";
                    echo "  [FAIL] {$method}: {$e->getMessage()}\n";
                }
            }
        }

        echo "\n=========================================\n";
        echo "Test Results: {$this->passed} passed, {$this->failed} failed\n";
        echo "=========================================\n";

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
            password: str_repeat('p', 24)
        );

        $debug = $config->__debugInfo();
        assert($debug['password'] === '******** (REDACTED)', 'Debug password must be redacted');
        assert(!str_contains(print_r($debug, true), 'UltraSecretPassword!987#'), 'print_r must not leak raw password');
        assert($config->getPassword() === str_repeat('p', 24), 'Accessor must return actual password for internal PDO');
    }

    public function testDatabaseConnectionFailureShouldRedactCredentials(): void
    {
        $config = new DatabaseConfig(
            host: '127.0.0.1',
            database: 'non_existent_db',
            user: 'test_user',
            password: str_repeat('q', 20),
            port: 59999
        );

        $conn = new SafeDatabaseConnection($config);
        $caught = false;
        try {
            $conn->getPdo();
        } catch (RuntimeException $e) {
            $caught = true;
            assert(!str_contains($e->getMessage(), str_repeat('q', 20)), 'Exception message must never leak password');
            assert(!str_contains($e->getMessage(), 'test_user'), 'Exception message must redact credentials');
        }

        assert($caught, 'SafeDatabaseConnection must throw sanitized RuntimeException on connection failure');
    }
}

$runner = new TestRunner();
$success = $runner->run();
exit($success ? 0 : 1);
