<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Aggregates;

use DateTimeImmutable;
use InvalidArgumentException;
use LogicException;
use OrderBillingSystem\Domain\Entities\OrderItem;
use OrderBillingSystem\Domain\Enums\OrderStatus;
use OrderBillingSystem\Domain\Events\DomainEvent;
use OrderBillingSystem\Domain\Events\OrderCreatedEvent;
use OrderBillingSystem\Domain\Events\OrderPaidEvent;
use OrderBillingSystem\Domain\Events\OrderStatusChangedEvent;
use OrderBillingSystem\Domain\Exceptions\InvalidOrderStateException;
use OrderBillingSystem\Domain\Strategies\DiscountStrategy;
use OrderBillingSystem\Domain\ValueObjects\Money;
use OrderBillingSystem\Domain\ValueObjects\TaxRate;

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
