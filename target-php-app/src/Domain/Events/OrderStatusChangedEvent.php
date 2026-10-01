<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Events;
use DateTimeImmutable;
use OrderBillingSystem\Domain\Enums\OrderStatus;
final readonly class OrderStatusChangedEvent extends AbstractDomainEvent
{ public function __construct(public string $orderId, public OrderStatus $oldStatus, public OrderStatus $newStatus, ?DateTimeImmutable $occurredOn = null) { parent::__construct($occurredOn); } }
