<?php
declare(strict_types=1);
namespace OrderBillingSystem\Domain\Services;
use InvalidArgumentException;
final readonly class PaymentResult
{
    public function __construct(public bool $success, public ?string $transactionId = null, public ?string $errorMessage = null)
    { if ($success && trim((string) $transactionId) === '') throw new InvalidArgumentException('Successful payment requires a transaction ID.'); }
}
