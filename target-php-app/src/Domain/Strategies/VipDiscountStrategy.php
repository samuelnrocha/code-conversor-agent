<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Strategies;
use InvalidArgumentException;
use OrderBillingSystem\Domain\ValueObjects\Money;
final readonly class VipDiscountStrategy implements DiscountStrategy
{
    public function __construct(public float $discountRate = 15.0) { if ($discountRate < 0 || $discountRate > 100) throw new InvalidArgumentException('Discount rate must be between 0 and 100.'); }
    public function getStrategyName(): string { return 'VIP Customer Discount'; }
    public function applyDiscount(Money $currentSubtotal): Money { return new Money($currentSubtotal->cents * $this->discountRate / 100 / 100, $currentSubtotal->currency); }
}
