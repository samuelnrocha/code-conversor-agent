<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Enums;

enum OrderStatus: int
{
    case Draft = 1;
    case Confirmed = 2;
    case Paid = 3;
    case Shipped = 4;
    case Cancelled = 5;
    case Refunded = 6;

    public function label(): string
    {
        return match ($this) {
            self::Draft => 'Draft',
            self::Confirmed => 'Confirmed',
            self::Paid => 'Paid',
            self::Shipped => 'Shipped',
            self::Cancelled => 'Cancelled',
            self::Refunded => 'Refunded',
        };
    }
}
