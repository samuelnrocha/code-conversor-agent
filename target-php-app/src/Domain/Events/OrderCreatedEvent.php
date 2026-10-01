<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Events;
use DateTimeImmutable;
final readonly class OrderCreatedEvent extends AbstractDomainEvent
{ public function __construct(public string $orderId, public string $customerId, ?DateTimeImmutable $occurredOn = null) { parent::__construct($occurredOn); } }
