<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Services;
use OrderBillingSystem\Domain\ValueObjects\Money;
interface NotificationServiceInterface { public function sendOrderConfirmation(string $customerId, string $orderId): void; public function sendPaymentReceipt(string $customerId, string $orderId, Money $amount): void; }
