<?php

declare(strict_types=1);

namespace OrderBillingSystem\Infrastructure;

use OrderBillingSystem\Domain\Aggregates\Order;
use OrderBillingSystem\Domain\Services\NotificationServiceInterface;
use OrderBillingSystem\Domain\Services\OrderRepositoryInterface;
use OrderBillingSystem\Domain\Services\PaymentGatewayInterface;
use OrderBillingSystem\Domain\Services\PaymentResult;
use OrderBillingSystem\Domain\ValueObjects\Money;

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
