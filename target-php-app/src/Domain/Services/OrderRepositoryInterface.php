<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Services;
use OrderBillingSystem\Domain\Aggregates\Order;
interface OrderRepositoryInterface { public function getById(string $id): ?Order; public function save(Order $order): void; /** @return list<Order> */ public function getByCustomerId(string $customerId): array; }
