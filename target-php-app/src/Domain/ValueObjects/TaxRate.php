<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\ValueObjects;

use InvalidArgumentException;
use OutOfRangeException;

final readonly class TaxRate
{
    public string $countryCode;
    public float $ratePercentage;

    public function __construct(string $countryCode, float $ratePercentage)
    {
        if (trim($countryCode) === '') {
            throw new InvalidArgumentException('Country code is required.');
        }

        if ($ratePercentage < 0.0 || $ratePercentage > 100.0) {
            throw new OutOfRangeException('Tax rate must be between 0 and 100.');
        }

        $this->countryCode = strtoupper(trim($countryCode));
        $this->ratePercentage = $ratePercentage;
    }

    public function calculateTax(Money $subtotal): Money
    {
        $taxAmount = $subtotal->amount * ($this->ratePercentage / 100.0);
        return new Money($taxAmount, $subtotal->currency);
    }
}
