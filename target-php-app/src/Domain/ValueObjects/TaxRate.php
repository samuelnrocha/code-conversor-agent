<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\ValueObjects;

use InvalidArgumentException;
use OutOfRangeException;

final readonly class TaxRate
{
    public string $countryCode;
    public float $ratePercentage;
    private int $basisPoints;

    public function __construct(string $countryCode, int|float|string $ratePercentage)
    {
        if (trim($countryCode) === '') {
            throw new InvalidArgumentException('Country code is required.');
        }

        if ((float) $ratePercentage < 0.0 || (float) $ratePercentage > 100.0) {
            throw new OutOfRangeException('Tax rate must be between 0 and 100.');
        }

        $this->countryCode = strtoupper(trim($countryCode));
        $this->ratePercentage = (float) $ratePercentage;
        $this->basisPoints = (int) round($this->ratePercentage * 100);
    }

    public function calculateTax(Money $subtotal): Money
    {
        return new Money(($subtotal->cents * $this->basisPoints) / 10000 / 100, $subtotal->currency);
    }
}
