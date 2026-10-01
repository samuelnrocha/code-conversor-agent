using OrderBillingSystem.App.Infrastructure;
using OrderBillingSystem.Core.Aggregates;
using OrderBillingSystem.Core.Entities;
using OrderBillingSystem.Core.Strategies;
using OrderBillingSystem.Core.UseCases;
using OrderBillingSystem.Core.ValueObjects;

Console.WriteLine("=================================================");
Console.WriteLine("  .NET Order & Billing Processing System (Source)");
Console.WriteLine("=================================================");

var repo = new InMemoryOrderRepository();
var paymentGateway = new MockPaymentGateway();
var notifications = new ConsoleNotificationService();
var service = new OrderProcessingService(repo, paymentGateway, notifications);

// 1. Create order
var order = await service.CreateOrderAsync(new CreateOrderCommand("ORD-2026-001", "CUST-99", "BR", 12.0m, "BRL"));
Console.WriteLine($"Created order {order.Id} with status: {order.Status}");

// 2. Add items
await service.AddItemToOrderAsync(new AddItemCommand("ORD-2026-001", "SKU-TECH-01", "Enterprise Cloud Server", 1200.00m, 2, 5.0m));
await service.AddItemToOrderAsync(new AddItemCommand("ORD-2026-001", "SKU-TECH-02", "SSD NVMe 2TB Enterprise", 450.00m, 4, 0m));

// 3. Apply VIP discount
order.ApplyDiscount(new VipDiscountStrategy(10m));

Console.WriteLine($"Gross Subtotal: {order.CalculateGrossSubtotal()}");
Console.WriteLine($"Total Discount: {order.CalculateTotalDiscount()}");
Console.WriteLine($"Subtotal After Discount: {order.CalculateSubtotalAfterDiscounts()}");
Console.WriteLine($"Tax Amount (12%): {order.CalculateTaxAmount()}");
Console.WriteLine($"Final Total: {order.CalculateFinalTotal()}");

// 4. Confirm order
await service.ConfirmOrderAsync("ORD-2026-001");
Console.WriteLine($"Confirmed order status: {order.Status}");

// 5. Pay order
await service.ProcessPaymentAsync(new ProcessOrderPaymentCommand("ORD-2026-001", "valid_token_abc"));
Console.WriteLine($"Final order status: {order.Status} (PaidAt: {order.PaidAt})");
Console.WriteLine($"Domain events raised: {order.DomainEvents.Count}");

Console.WriteLine("System execution completed successfully.");
