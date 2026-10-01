<?php
declare(strict_types=1);
namespace OrderBillingSystem\Infrastructure;
use OrderBillingSystem\Domain\Services\NotificationServiceInterface;
use OrderBillingSystem\Domain\ValueObjects\Money;
final class ConsoleNotificationService implements NotificationServiceInterface
{
    /** @var list<string> */ public array $notifications = [];
    public function sendOrderConfirmation(string $customerId, string $orderId): void { $this->notifications[] = "Order {$orderId} confirmed for customer {$customerId}."; }
    public function sendPaymentReceipt(string $customerId, string $orderId, Money $amount): void { $this->notifications[] = "Payment receipt: Order {$orderId} paid {$amount} for customer {$customerId}."; }
}
