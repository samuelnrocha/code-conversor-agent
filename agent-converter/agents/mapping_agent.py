from typing import Dict, List
from models import DependencyMapping

class MappingAgent:
    """
    Agente de mapeamento de demandas, bibliotecas, namespaces e tipos
    entre C# .NET e PHP 8.4.
    """

    def map_architecture(self) -> DependencyMapping:
        csharp_namespaces = [
            "OrderBillingSystem.Core.Enums",
            "OrderBillingSystem.Core.ValueObjects",
            "OrderBillingSystem.Core.Entities",
            "OrderBillingSystem.Core.Aggregates",
            "OrderBillingSystem.Core.Events",
            "OrderBillingSystem.Core.Strategies",
            "OrderBillingSystem.Core.Exceptions",
            "OrderBillingSystem.Core.Services",
            "OrderBillingSystem.Core.UseCases",
            "OrderBillingSystem.App.Infrastructure",
            "OrderBillingSystem.Tests"
        ]

        target_php_namespaces = {
            "OrderBillingSystem.Core.Enums": "OrderBillingSystem\\Domain\\Enums",
            "OrderBillingSystem.Core.ValueObjects": "OrderBillingSystem\\Domain\\ValueObjects",
            "OrderBillingSystem.Core.Entities": "OrderBillingSystem\\Domain\\Entities",
            "OrderBillingSystem.Core.Aggregates": "OrderBillingSystem\\Domain\\Aggregates",
            "OrderBillingSystem.Core.Events": "OrderBillingSystem\\Domain\\Events",
            "OrderBillingSystem.Core.Strategies": "OrderBillingSystem\\Domain\\Strategies",
            "OrderBillingSystem.Core.Exceptions": "OrderBillingSystem\\Domain\\Exceptions",
            "OrderBillingSystem.Core.Services": "OrderBillingSystem\\Domain\\Services",
            "OrderBillingSystem.Core.UseCases": "OrderBillingSystem\\Application\\UseCases",
            "OrderBillingSystem.App.Infrastructure": "OrderBillingSystem\\Infrastructure",
            "OrderBillingSystem.Tests": "OrderBillingSystem\\Tests"
        }

        mapped_types = {
            "OrderStatus": "OrderStatus (PHP 8.1+ Backed Enum: int)",
            "Money": "Money (PHP 8.2+ readonly class with immutable methods)",
            "TaxRate": "TaxRate (PHP 8.2+ readonly class)",
            "OrderItem": "OrderItem (PHP 8.4 class with constructor promotion)",
            "Order": "Order (DDD Aggregate Root with encapsulation)",
            "IDomainEvent": "DomainEvent (PHP Interface)",
            "OrderCreatedEvent": "OrderCreatedEvent (PHP 8.2+ readonly class)",
            "OrderStatusChangedEvent": "OrderStatusChangedEvent (PHP 8.2+ readonly class)",
            "OrderPaidEvent": "OrderPaidEvent (PHP 8.2+ readonly class)",
            "IDiscountStrategy": "DiscountStrategy (PHP Interface)",
            "VipDiscountStrategy": "VipDiscountStrategy (PHP Concrete Strategy)",
            "CouponDiscountStrategy": "CouponDiscountStrategy (PHP Concrete Strategy)",
            "DomainException": "DomainException (extends \\DomainException)",
            "InvalidOrderStateException": "InvalidOrderStateException (extends DomainException)",
            "IOrderRepository": "OrderRepositoryInterface (PHP Interface)",
            "IPaymentGateway": "PaymentGatewayInterface (PHP Interface)",
            "INotificationService": "NotificationServiceInterface (PHP Interface)",
            "OrderProcessingService": "OrderProcessingService (PHP Application Service)",
            "InMemoryOrderRepository": "InMemoryOrderRepository (PHP Infrastructure)",
            "MockPaymentGateway": "MockPaymentGateway (PHP Infrastructure)",
            "ConsoleNotificationService": "ConsoleNotificationService (PHP Infrastructure)",
            "OrderAggregateTests": "OrderAggregateTest (PHPUnit / Standalone Test Harness)"
        }

        composer_packages = {
            "php": ">=8.4.0",
            "ext-bcmath": "*",
            "ext-json": "*"
        }

        return DependencyMapping(
            csharp_namespaces=csharp_namespaces,
            target_php_namespaces=target_php_namespaces,
            mapped_types=mapped_types,
            composer_packages=composer_packages
        )
