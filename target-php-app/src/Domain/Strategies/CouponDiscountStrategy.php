<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Strategies;
use OrderBillingSystem\Domain\ValueObjects\Money;
final readonly class CouponDiscountStrategy implements DiscountStrategy
{
    public function __construct(public string $couponCode, public Money $fixedDiscount) {}
    public function getStrategyName(): string { return "Coupon: {$this->couponCode}"; }
    public function applyDiscount(Money $currentSubtotal): Money { return $currentSubtotal->cents <= $this->fixedDiscount->cents ? $currentSubtotal : $this->fixedDiscount; }
}
