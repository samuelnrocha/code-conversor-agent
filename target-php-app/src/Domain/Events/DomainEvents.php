<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Events;

use DateTimeImmutable;
use OrderBillingSystem\Domain\Enums\OrderStatus;
use OrderBillingSystem\Domain\ValueObjects\Money;

interface DomainEvent
{
    public function getEventId(): string;
    public function getOccurredOn(): DateTimeImmutable;
}

abstract readonly class AbstractDomainEvent implements DomainEvent
{
    protected string $eventId;
    protected DateTimeImmutable $occurredOn;

    public function __construct(?DateTimeImmutable $occurredOn = null)
    {
        $this->eventId = bin2hex(random_bytes(16));
        $this->occurredOn = $occurredOn ?? new DateTimeImmutable();
    }

    public function getEventId(): string
    {
        return $this->eventId;
    }

    public function getOccurredOn(): DateTimeImmutable
    {
        return $this->occurredOn;
    }
}

final readonly class OrderCreatedEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}

final readonly class OrderStatusChangedEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public OrderStatus $oldStatus,
        public OrderStatus $newStatus,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}

final readonly class OrderPaidEvent extends AbstractDomainEvent
{
    public function __construct(
        public string $orderId,
        public Money $amountPaid,
        public string $transactionId,
        ?DateTimeImmutable $occurredOn = null
    ) {
        parent::__construct($occurredOn);
    }
}
