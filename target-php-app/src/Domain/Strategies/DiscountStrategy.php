<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Strategies;
use OrderBillingSystem\Domain\ValueObjects\Money;
interface DiscountStrategy { public function getStrategyName(): string; public function applyDiscount(Money $currentSubtotal): Money; }
