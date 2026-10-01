<?php
declare(strict_types=1);
namespace OrderBillingSystem\Infrastructure;
use OrderBillingSystem\Domain\Aggregates\Order;
use OrderBillingSystem\Domain\Services\OrderRepositoryInterface;
final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */ private array $orders = [];
    public function getById(string $id): ?Order { return $this->orders[$id] ?? null; }
    public function save(Order $order): void { $this->orders[$order->id] = $order; }
    public function getByCustomerId(string $customerId): array { return array_values(array_filter($this->orders, static fn (Order $order): bool => $order->customerId === $customerId)); }
}
