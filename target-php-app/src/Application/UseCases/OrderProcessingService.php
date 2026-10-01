<?php

declare(strict_types=1);

namespace OrderBillingSystem\Application\UseCases;

use LogicException;
use OrderBillingSystem\Domain\Aggregates\Order;
use OrderBillingSystem\Domain\Entities\OrderItem;
use OrderBillingSystem\Domain\Exceptions\DomainException;
use OrderBillingSystem\Domain\Services\NotificationServiceInterface;
use OrderBillingSystem\Domain\Services\OrderRepositoryInterface;
use OrderBillingSystem\Domain\Services\PaymentGatewayInterface;
use OrderBillingSystem\Domain\ValueObjects\Money;
use OrderBillingSystem\Domain\ValueObjects\TaxRate;

final readonly class CreateOrderCommand
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public string $countryCode,
        public int|float|string $taxRatePercentage,
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
        public int|float|string $unitPrice,
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

        $unitPrice = new Money($command->unitPrice, $order->currency);
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

        if ($result->transactionId === null || trim($result->transactionId) === '') {
            throw new DomainException('Payment succeeded without a transaction ID.');
        }
        $order->markAsPaid($result->transactionId);
        $this->repository->save($order);
        $this->notificationService->sendPaymentReceipt($order->customerId, $order->id, $total);

        return $order;
    }
}
