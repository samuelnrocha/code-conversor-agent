using OrderBillingSystem.Core.Enums;
using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.Events;

public interface IDomainEvent
{
    Guid EventId { get; }
    DateTime OccurredOn { get; }
}

public sealed record OrderCreatedEvent(string OrderId, string CustomerId, DateTime OccurredOn) : IDomainEvent
{
    public Guid EventId { get; } = Guid.NewGuid();
}

public sealed record OrderStatusChangedEvent(string OrderId, OrderStatus OldStatus, OrderStatus NewStatus, DateTime OccurredOn) : IDomainEvent
{
    public Guid EventId { get; } = Guid.NewGuid();
}

public sealed record OrderPaidEvent(string OrderId, Money AmountPaid, string TransactionId, DateTime OccurredOn) : IDomainEvent
{
    public Guid EventId { get; } = Guid.NewGuid();
}
