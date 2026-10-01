<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Strategies;

use OrderBillingSystem\Domain\ValueObjects\Money;

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
