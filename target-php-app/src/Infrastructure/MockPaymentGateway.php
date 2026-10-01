<?php
declare(strict_types=1);
namespace OrderBillingSystem\Infrastructure;
use OrderBillingSystem\Domain\Services\PaymentGatewayInterface;
use OrderBillingSystem\Domain\Services\PaymentResult;
use OrderBillingSystem\Domain\ValueObjects\Money;
final class MockPaymentGateway implements PaymentGatewayInterface
{
    public function processPayment(string $orderId, Money $amount, string $paymentMethodToken): PaymentResult
    { if ($paymentMethodToken === 'invalid_token') return new PaymentResult(false, null, 'Card declined: Invalid test token.'); return new PaymentResult(true, 'tx_'.bin2hex(random_bytes(8))); }
}
