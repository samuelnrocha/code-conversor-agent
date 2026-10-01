<?php

declare(strict_types=1);

namespace OrderBillingSystem\Domain\Exceptions;

use DomainException as BaseDomainException;

class DomainException extends BaseDomainException
{
}

class InvalidOrderStateException extends DomainException
{
}
