<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Events;
use DateTimeImmutable;
abstract readonly class AbstractDomainEvent implements DomainEvent
{
    public string $eventId;
    public DateTimeImmutable $occurredOn;
    public function __construct(?DateTimeImmutable $occurredOn = null) { $this->eventId = bin2hex(random_bytes(16)); $this->occurredOn = $occurredOn ?? new DateTimeImmutable(); }
    public function getEventId(): string { return $this->eventId; }
    public function getOccurredOn(): DateTimeImmutable { return $this->occurredOn; }
}
