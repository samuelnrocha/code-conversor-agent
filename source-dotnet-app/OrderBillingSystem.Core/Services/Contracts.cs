using OrderBillingSystem.Core.Aggregates;
using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.Services;

public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(string id);
    Task SaveAsync(Order order);
    Task<IReadOnlyList<Order>> GetByCustomerIdAsync(string customerId);
}

public interface IPaymentGateway
{
    Task<PaymentResult> ProcessPaymentAsync(string orderId, Money amount, string paymentMethodToken);
}

public interface INotificationService
{
    Task SendOrderConfirmationAsync(string customerId, string orderId);
    Task SendPaymentReceiptAsync(string customerId, string orderId, Money amount);
}

public sealed record PaymentResult(bool Success, string? TransactionId, string? ErrorMessage);
