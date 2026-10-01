<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Entities;

use InvalidArgumentException;
use OutOfRangeException;
use OrderBillingSystem\Domain\ValueObjects\Money;

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
