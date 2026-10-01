<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Events;
use DateTimeImmutable;
use OrderBillingSystem\Domain\ValueObjects\Money;
final readonly class OrderPaidEvent extends AbstractDomainEvent
{ public function __construct(public string $orderId, public Money $amountPaid, public string $transactionId, ?DateTimeImmutable $occurredOn = null) { parent::__construct($occurredOn); } }
