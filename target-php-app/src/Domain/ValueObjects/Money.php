<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\ValueObjects;

use InvalidArgumentException;
use LogicException;

final readonly class Money
{
    public float $amount;
    public string $currency;

    public function __construct(float $amount, string $currency = 'BRL')
    {
        if ($amount < 0.0) {
            throw new InvalidArgumentException('Amount cannot be negative.');
        }

        if (trim($currency) === '') {
            throw new InvalidArgumentException('Currency code cannot be empty.');
        }

        $this->amount = round($amount, 2);
        $this->currency = strtoupper(trim($currency));
    }

    public static function zero(string $currency = 'BRL'): self
    {
        return new self(0.0, $currency);
    }

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->amount + $other->amount, $this->currency);
    }

    public function subtract(self $other): self
    {
        $this->ensureSameCurrency($other);
        if ($this->amount < $other->amount) {
            throw new LogicException('Resulting money cannot be negative.');
        }
        return new self($this->amount - $other->amount, $this->currency);
    }

    public function multiply(float|int $multiplier): self
    {
        if ($multiplier < 0) {
            throw new InvalidArgumentException('Multiplier cannot be negative.');
        }
        return new self($this->amount * $multiplier, $this->currency);
    }

    private function ensureSameCurrency(self $other): void
    {
        if ($this->currency !== $other->currency) {
            throw new LogicException(
                sprintf('Cannot operate on different currencies: %s and %s', $this->currency, $other->currency)
            );
        }
    }

    public function __toString(): string
    {
        return sprintf('%s %s', $this->currency, number_format($this->amount, 2, '.', ','));
    }
}
