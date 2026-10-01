<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\ValueObjects;

use InvalidArgumentException;
use LogicException;

final readonly class Money
{
    public float $amount;
    public string $currency;
    public int $cents;

    public function __construct(int|float|string $amount, string $currency = 'BRL')
    {
        if (trim($currency) === '') {
            throw new InvalidArgumentException('Currency code cannot be empty.');
        }

        $this->cents = self::toCents($amount);
        $this->amount = $this->cents / 100;
        $this->currency = strtoupper(trim($currency));
    }

    public static function zero(string $currency = 'BRL'): self
    {
        return new self(0, $currency);
    }

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self(($this->cents + $other->cents) / 100, $this->currency);
    }

    public function subtract(self $other): self
    {
        $this->ensureSameCurrency($other);
        if ($this->cents < $other->cents) {
            throw new LogicException('Resulting money cannot be negative.');
        }
        return new self(($this->cents - $other->cents) / 100, $this->currency);
    }

    public function multiply(int|float|string $multiplier): self
    {
        $multiplierString = (string) $multiplier;
        if ((float) $multiplierString < 0) {
            throw new InvalidArgumentException('Multiplier cannot be negative.');
        }
        $product = $this->cents * (float) $multiplierString;
        return new self($product / 100, $this->currency);
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

    private static function toCents(int|float|string $amount): int
    {
        $value = is_float($amount) ? sprintf('%.10F', $amount) : (string) $amount;
        $value = trim($value);
        if (!preg_match('/^\+?(\d+)(?:\.(\d+))?$/', $value, $matches)) {
            throw new InvalidArgumentException('Amount must be a non-negative decimal.');
        }
        $fraction = str_pad(substr($matches[2] ?? '', 0, 3), 3, '0');
        $third = (int) $fraction[2];
        $cents = ((int) $matches[1] * 100) + (int) substr($fraction, 0, 2);
        if ($third >= 5) {
            ++$cents;
        }
        return $cents;
    }
}
