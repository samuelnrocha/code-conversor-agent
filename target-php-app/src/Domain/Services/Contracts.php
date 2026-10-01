<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Services;

use OrderBillingSystem\Domain\Aggregates\Order;
use OrderBillingSystem\Domain\ValueObjects\Money;

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
