using System.Collections.Concurrent;
using OrderBillingSystem.Core.Aggregates;
using OrderBillingSystem.Core.Services;
using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.App.Infrastructure;

public sealed class InMemoryOrderRepository : IOrderRepository
{
    private readonly ConcurrentDictionary<string, Order> _orders = new();

    public Task<Order?> GetByIdAsync(string id)
    {
        _orders.TryGetValue(id, out var order);
        return Task.FromResult(order);
    }

    public Task SaveAsync(Order order)
    {
        _orders[order.Id] = order;
        return Task.CompletedTask;
    }

    public Task<IReadOnlyList<Order>> GetByCustomerIdAsync(string customerId)
    {
        var list = _orders.Values.Where(o => o.CustomerId == customerId).ToList();
        return Task.FromResult<IReadOnlyList<Order>>(list);
    }
}

public sealed class MockPaymentGateway : IPaymentGateway
{
    public Task<PaymentResult> ProcessPaymentAsync(string orderId, Money amount, string paymentMethodToken)
    {
        if (paymentMethodToken == "invalid_token")
        {
            return Task.FromResult(new PaymentResult(false, null, "Card declined: Invalid test token."));
        }

        string txId = $"tx_{Guid.NewGuid().ToString("N")[..12]}";
        return Task.FromResult(new PaymentResult(true, txId, null));
    }
}

public sealed class ConsoleNotificationService : INotificationService
{
    public List<string> Notifications { get; } = new();

    public Task SendOrderConfirmationAsync(string customerId, string orderId)
    {
        string msg = $"[NOTIFICATION] Order {orderId} confirmed for customer {customerId}.";
        Notifications.Add(msg);
        Console.WriteLine(msg);
        return Task.CompletedTask;
    }

    public Task SendPaymentReceiptAsync(string customerId, string orderId, Money amount)
    {
        string msg = $"[NOTIFICATION] Payment receipt: Order {orderId} paid {amount} for customer {customerId}.";
        Notifications.Add(msg);
        Console.WriteLine(msg);
        return Task.CompletedTask;
    }
}
