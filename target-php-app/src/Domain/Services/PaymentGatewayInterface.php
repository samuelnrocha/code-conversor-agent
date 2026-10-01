<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Services;
use OrderBillingSystem\Domain\ValueObjects\Money;
interface PaymentGatewayInterface { public function processPayment(string $orderId, Money $amount, string $paymentMethodToken): PaymentResult; }
