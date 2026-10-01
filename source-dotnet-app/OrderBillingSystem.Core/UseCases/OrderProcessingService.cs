using OrderBillingSystem.Core.Aggregates;
using OrderBillingSystem.Core.Entities;
using OrderBillingSystem.Core.Exceptions;
using OrderBillingSystem.Core.Services;
using OrderBillingSystem.Core.Strategies;
using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.UseCases;

public sealed record CreateOrderCommand(string OrderId, string CustomerId, string CountryCode, decimal TaxRatePercentage, string Currency = "BRL");
public sealed record AddItemCommand(string OrderId, string Sku, string Name, decimal UnitPrice, int Quantity, decimal DiscountPercent = 0m);
public sealed record ProcessOrderPaymentCommand(string OrderId, string PaymentToken);

public sealed class OrderProcessingService
{
    private readonly IOrderRepository _repository;
    private readonly IPaymentGateway _paymentGateway;
    private readonly INotificationService _notificationService;

    public OrderProcessingService(
        IOrderRepository repository,
        IPaymentGateway paymentGateway,
        INotificationService notificationService)
    {
        _repository = repository;
        _paymentGateway = paymentGateway;
        _notificationService = notificationService;
    }

    public async Task<Order> CreateOrderAsync(CreateOrderCommand command)
    {
        var taxRate = new TaxRate(command.CountryCode, command.TaxRatePercentage);
        var order = new Order(command.OrderId, command.CustomerId, taxRate, command.Currency);

        await _repository.SaveAsync(order);
        return order;
    }

    public async Task<Order> AddItemToOrderAsync(AddItemCommand command)
    {
        var order = await _repository.GetByIdAsync(command.OrderId);
        if (order == null)
        {
            throw new InvalidOperationException($"Order {command.OrderId} not found.");
        }

        var unitPrice = new Money(command.UnitPrice, order.CalculateGrossSubtotal().Currency);
        var item = new OrderItem(command.Sku, command.Name, unitPrice, command.Quantity, command.DiscountPercent);

        order.AddItem(item);
        await _repository.SaveAsync(order);
        return order;
    }

    public async Task<Order> ConfirmOrderAsync(string orderId)
    {
        var order = await _repository.GetByIdAsync(orderId);
        if (order == null)
        {
            throw new InvalidOperationException($"Order {orderId} not found.");
        }

        order.Confirm();
        await _repository.SaveAsync(order);
        await _notificationService.SendOrderConfirmationAsync(order.CustomerId, order.Id);

        return order;
    }

    public async Task<Order> ProcessPaymentAsync(ProcessOrderPaymentCommand command)
    {
        var order = await _repository.GetByIdAsync(command.OrderId);
        if (order == null)
        {
            throw new InvalidOperationException($"Order {command.OrderId} not found.");
        }

        Money total = order.CalculateFinalTotal();
        PaymentResult result = await _paymentGateway.ProcessPaymentAsync(order.Id, total, command.PaymentToken);

        if (!result.Success)
        {
            throw new DomainException($"Payment failed for order {order.Id}: {result.ErrorMessage}");
        }

        order.MarkAsPaid(result.TransactionId!);
        await _repository.SaveAsync(order);
        await _notificationService.SendPaymentReceiptAsync(order.CustomerId, order.Id, total);

        return order;
    }
}
