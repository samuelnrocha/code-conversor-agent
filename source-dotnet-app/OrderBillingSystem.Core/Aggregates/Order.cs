using OrderBillingSystem.Core.Entities;
using OrderBillingSystem.Core.Enums;
using OrderBillingSystem.Core.Events;
using OrderBillingSystem.Core.Exceptions;
using OrderBillingSystem.Core.Strategies;
using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.Aggregates;

public sealed class Order
{
    private readonly List<OrderItem> _items = new();
    private readonly List<IDomainEvent> _domainEvents = new();
    private readonly List<IDiscountStrategy> _discounts = new();

    public string Id { get; }
    public string CustomerId { get; }
    public OrderStatus Status { get; private set; }
    public TaxRate TaxRate { get; }
    public DateTime CreatedAt { get; }
    public DateTime? PaidAt { get; private set; }

    public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    public IReadOnlyCollection<IDiscountStrategy> AppliedDiscounts => _discounts.AsReadOnly();

    public Order(string id, string customerId, TaxRate taxRate, string currency = "BRL")
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("Order ID cannot be empty.", nameof(id));
        }

        if (string.IsNullOrWhiteSpace(customerId))
        {
            throw new ArgumentException("Customer ID cannot be empty.", nameof(customerId));
        }

        Id = id;
        CustomerId = customerId;
        TaxRate = taxRate ?? throw new ArgumentNullException(nameof(taxRate));
        Status = OrderStatus.Draft;
        CreatedAt = DateTime.UtcNow;

        _domainEvents.Add(new OrderCreatedEvent(Id, CustomerId, CreatedAt));
    }

    public void AddItem(OrderItem item)
    {
        EnsureInStatus(OrderStatus.Draft);

        var existing = _items.FirstOrDefault(i => i.Sku == item.Sku);
        if (existing != null)
        {
            existing.UpdateQuantity(existing.Quantity + item.Quantity);
        }
        else
        {
            _items.Add(item);
        }
    }

    public void RemoveItem(string sku)
    {
        EnsureInStatus(OrderStatus.Draft);

        var item = _items.FirstOrDefault(i => i.Sku == sku);
        if (item == null)
        {
            throw new InvalidOperationException($"Item with SKU {sku} not found in order.");
        }

        _items.Remove(item);
    }

    public void ApplyDiscount(IDiscountStrategy discountStrategy)
    {
        EnsureInStatus(OrderStatus.Draft);
        _discounts.Add(discountStrategy ?? throw new ArgumentNullException(nameof(discountStrategy)));
    }

    public Money CalculateGrossSubtotal()
    {
        if (!_items.Any())
        {
            return Money.Zero();
        }

        string currency = _items[0].UnitPrice.Currency;
        decimal total = _items.Sum(i => i.CalculateNetTotal().Amount);
        return new Money(total, currency);
    }

    public Money CalculateTotalDiscount()
    {
        Money subtotal = CalculateGrossSubtotal();
        decimal totalDiscountAmount = 0m;

        foreach (var strategy in _discounts)
        {
            Money discount = strategy.ApplyDiscount(subtotal);
            totalDiscountAmount += discount.Amount;
        }

        if (totalDiscountAmount > subtotal.Amount)
        {
            totalDiscountAmount = subtotal.Amount;
        }

        return new Money(totalDiscountAmount, subtotal.Currency);
    }

    public Money CalculateSubtotalAfterDiscounts()
    {
        Money gross = CalculateGrossSubtotal();
        Money discounts = CalculateTotalDiscount();
        return gross - discounts;
    }

    public Money CalculateTaxAmount()
    {
        Money subtotal = CalculateSubtotalAfterDiscounts();
        return TaxRate.CalculateTax(subtotal);
    }

    public Money CalculateFinalTotal()
    {
        return CalculateSubtotalAfterDiscounts() + CalculateTaxAmount();
    }

    public void Confirm()
    {
        EnsureInStatus(OrderStatus.Draft);

        if (!_items.Any())
        {
            throw new InvalidOrderStateException("Cannot confirm an order without items.");
        }

        TransitionTo(OrderStatus.Confirmed);
    }

    public void MarkAsPaid(string transactionId)
    {
        EnsureInStatus(OrderStatus.Confirmed);

        if (string.IsNullOrWhiteSpace(transactionId))
        {
            throw new ArgumentException("Transaction ID is required to mark as paid.", nameof(transactionId));
        }

        PaidAt = DateTime.UtcNow;
        TransitionTo(OrderStatus.Paid);

        _domainEvents.Add(new OrderPaidEvent(Id, CalculateFinalTotal(), transactionId, PaidAt.Value));
    }

    public void Ship()
    {
        EnsureInStatus(OrderStatus.Paid);
        TransitionTo(OrderStatus.Shipped);
    }

    public void Cancel(string reason)
    {
        if (Status == OrderStatus.Shipped)
        {
            throw new InvalidOrderStateException("Cannot cancel an order that has already been shipped.");
        }

        if (Status == OrderStatus.Cancelled)
        {
            return;
        }

        TransitionTo(OrderStatus.Cancelled);
    }

    public void ClearEvents()
    {
        _domainEvents.Clear();
    }

    private void EnsureInStatus(OrderStatus required)
    {
        if (Status != required)
        {
            throw new InvalidOrderStateException($"Action requires order status '{required}', but current status is '{Status}'.");
        }
    }

    private void TransitionTo(OrderStatus newStatus)
    {
        OrderStatus old = Status;
        Status = newStatus;
        _domainEvents.Add(new OrderStatusChangedEvent(Id, old, newStatus, DateTime.UtcNow));
    }
}
