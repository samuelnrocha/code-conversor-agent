<?php

declare(strict_types=1);

// PSR-4 Autoloader fallback without composer
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

// Require files with multiple declarations
require_once __DIR__ . '/../src/Domain/Events/DomainEvents.php';
require_once __DIR__ . '/../src/Domain/Strategies/DiscountStrategies.php';
require_once __DIR__ . '/../src/Domain/Exceptions/DomainExceptions.php';
require_once __DIR__ . '/../src/Domain/Services/Contracts.php';
require_once __DIR__ . '/../src/Infrastructure/Implementations.php';
require_once __DIR__ . '/../src/Infrastructure/Database/DatabaseConfig.php';
require_once __DIR__ . '/../src/Infrastructure/Database/SafeDatabaseConnection.php';

use OrderBillingSystem\Application\UseCases\AddItemCommand;
use OrderBillingSystem\Application\UseCases\CreateOrderCommand;
use OrderBillingSystem\Application\UseCases\OrderProcessingService;
use OrderBillingSystem\Application\UseCases\ProcessOrderPaymentCommand;
use OrderBillingSystem\Domain\Strategies\VipDiscountStrategy;
use OrderBillingSystem\Infrastructure\ConsoleNotificationService;
use OrderBillingSystem\Infrastructure\Database\DatabaseConfig;
use OrderBillingSystem\Infrastructure\InMemoryOrderRepository;
use OrderBillingSystem\Infrastructure\MockPaymentGateway;

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
    "[SECURITY LAYER] Database config loaded: host=%s, db=%s, user=%s (pwd=%s)\n",
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
echo sprintf("Created order %s with status: %s\n", $order->id, $order->status->label());

// 2. Add items
$service->addItemToOrder(new AddItemCommand('ORD-2026-001', 'SKU-TECH-01', 'Enterprise Cloud Server', 1200.00, 2, 5.0));
$service->addItemToOrder(new AddItemCommand('ORD-2026-001', 'SKU-TECH-02', 'SSD NVMe 2TB Enterprise', 450.00, 4, 0.0));

// 3. Apply VIP discount
$order->applyDiscount(new VipDiscountStrategy(10.0));

echo sprintf("Gross Subtotal: %s\n", $order->calculateGrossSubtotal());
echo sprintf("Total Discount: %s\n", $order->calculateTotalDiscount());
echo sprintf("Subtotal After Discount: %s\n", $order->calculateSubtotalAfterDiscounts());
echo sprintf("Tax Amount (12%%): %s\n", $order->calculateTaxAmount());
echo sprintf("Final Total: %s\n", $order->calculateFinalTotal());

// 4. Confirm order
$service->confirmOrder('ORD-2026-001');
echo sprintf("Confirmed order status: %s\n", $order->status->label());

// 5. Pay order
$service->processPayment(new ProcessOrderPaymentCommand('ORD-2026-001', 'valid_token_abc'));
echo sprintf("Final order status: %s (PaidAt: %s)\n", $order->status->label(), $order->paidAt?->format('Y-m-d H:i:s'));
echo sprintf("Domain events raised: %d\n", count($order->getDomainEvents()));

echo "PHP 8.4 system execution completed successfully." . PHP_EOL;
