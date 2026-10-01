using OrderBillingSystem.Core.Aggregates;
using OrderBillingSystem.Core.Entities;
using OrderBillingSystem.Core.Enums;
using OrderBillingSystem.Core.Exceptions;
using OrderBillingSystem.Core.Strategies;
using OrderBillingSystem.Core.ValueObjects;
using Xunit;

namespace OrderBillingSystem.Tests;

public class OrderAggregateTests
{
    private readonly TaxRate _defaultTaxRate = new("BR", 10.0m);

    [Fact]
    public void Order_Creation_ShouldInitializeInDraftStatusWithCreatedEvent()
    {
        var order = new Order("ORD-001", "CUST-01", _defaultTaxRate);

        Assert.Equal("ORD-001", order.Id);
        Assert.Equal("CUST-01", order.CustomerId);
        Assert.Equal(OrderStatus.Draft, order.Status);
        Assert.Single(order.DomainEvents);
    }

    [Fact]
    public void AddItem_ShouldAccumulateQuantity_WhenSkuAlreadyExists()
    {
        var order = new Order("ORD-001", "CUST-01", _defaultTaxRate);
        var item1 = new OrderItem("SKU-1", "Laptop", new Money(1000m), 1);
        var item2 = new OrderItem("SKU-1", "Laptop", new Money(1000m), 2);

        order.AddItem(item1);
        order.AddItem(item2);

        Assert.Single(order.Items);
        Assert.Equal(3, order.Items.First().Quantity);
        Assert.Equal(3000m, order.CalculateGrossSubtotal().Amount);
    }

    [Fact]
    public void ItemDiscount_ShouldBeCalculatedCorrectly()
    {
        // 2 items @ 100 each with 10% discount => 200 - 20 = 180
        var item = new OrderItem("SKU-A", "Keyboard", new Money(100m), 2, 10m);

        Assert.Equal(200m, item.CalculateGrossTotal().Amount);
        Assert.Equal(20m, item.CalculateDiscountAmount().Amount);
        Assert.Equal(180m, item.CalculateNetTotal().Amount);
    }

    [Fact]
    public void OrderDiscountsAndTaxes_ShouldComputeExactTotals()
    {
        var order = new Order("ORD-100", "CUST-10", new TaxRate("BR", 10m));
        // Item: 2 * 500 = 1000 net
        order.AddItem(new OrderItem("SKU-X", "Monitor", new Money(500m), 2));

        // 10% VIP discount on 1000 = 100
        order.ApplyDiscount(new VipDiscountStrategy(10m));

        Assert.Equal(1000m, order.CalculateGrossSubtotal().Amount);
        Assert.Equal(100m, order.CalculateTotalDiscount().Amount);
        Assert.Equal(900m, order.CalculateSubtotalAfterDiscounts().Amount);

        // 10% tax on 900 = 90
        Assert.Equal(90m, order.CalculateTaxAmount().Amount);

        // Final total: 900 + 90 = 990
        Assert.Equal(990m, order.CalculateFinalTotal().Amount);
    }

    [Fact]
    public void Confirm_ShouldThrow_WhenOrderHasNoItems()
    {
        var order = new Order("ORD-EMPTY", "CUST-01", _defaultTaxRate);

        Assert.Throws<InvalidOrderStateException>(() => order.Confirm());
    }

    [Fact]
    public void FullOrderLifecycle_ShouldProgressStatusCorrectly()
    {
        var order = new Order("ORD-FLOW", "CUST-FLOW", _defaultTaxRate);
        order.AddItem(new OrderItem("SKU-1", "Mouse", new Money(50m), 1));

        order.Confirm();
        Assert.Equal(OrderStatus.Confirmed, order.Status);

        order.MarkAsPaid("TX-998877");
        Assert.Equal(OrderStatus.Paid, order.Status);
        Assert.NotNull(order.PaidAt);

        order.Ship();
        Assert.Equal(OrderStatus.Shipped, order.Status);
    }

    [Fact]
    public void Cancel_ShouldThrow_WhenOrderAlreadyShipped()
    {
        var order = new Order("ORD-SHIP", "CUST-01", _defaultTaxRate);
        order.AddItem(new OrderItem("SKU-1", "Mouse", new Money(50m), 1));
        order.Confirm();
        order.MarkAsPaid("TX-123");
        order.Ship();

        Assert.Throws<InvalidOrderStateException>(() => order.Cancel("Changed mind"));
    }

    [Fact]
    public void Money_Operations_ShouldPreserveInvariants()
    {
        var m1 = new Money(100.50m, "USD");
        var m2 = new Money(50.25m, "USD");

        var sum = m1 + m2;
        Assert.Equal(150.75m, sum.Amount);
        Assert.Equal("USD", sum.Currency);

        var diff = m1 - m2;
        Assert.Equal(50.25m, diff.Amount);

        var mult = m2 * 2;
        Assert.Equal(100.50m, mult.Amount);

        Assert.Throws<ArgumentException>(() => new Money(-1m));
        Assert.Throws<InvalidOperationException>(() => m1 + new Money(10m, "EUR"));
    }
}
