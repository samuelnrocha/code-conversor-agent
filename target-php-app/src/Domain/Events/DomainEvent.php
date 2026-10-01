<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Events;
use DateTimeImmutable;
interface DomainEvent { public function getEventId(): string; public function getOccurredOn(): DateTimeImmutable; }
