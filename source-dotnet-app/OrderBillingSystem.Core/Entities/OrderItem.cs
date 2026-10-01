using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.Entities;

public sealed class OrderItem
{
    public string Sku { get; }
    public string Name { get; }
    public Money UnitPrice { get; }
    public int Quantity { get; private set; }
    public decimal DiscountPercent { get; private set; }

    public OrderItem(string sku, string name, Money unitPrice, int quantity, decimal discountPercent = 0m)
    {
        if (string.IsNullOrWhiteSpace(sku))
        {
            throw new ArgumentException("SKU is required.", nameof(sku));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Item name is required.", nameof(name));
        }

        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(quantity), "Quantity must be greater than zero.");
        }

        if (discountPercent < 0 || discountPercent > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(discountPercent), "Discount must be between 0 and 100.");
        }

        Sku = sku;
        Name = name;
        UnitPrice = unitPrice;
        Quantity = quantity;
        DiscountPercent = discountPercent;
    }

    public Money CalculateGrossTotal()
    {
        return UnitPrice * Quantity;
    }

    public Money CalculateDiscountAmount()
    {
        if (DiscountPercent == 0m)
        {
            return Money.Zero(UnitPrice.Currency);
        }

        decimal discount = (UnitPrice.Amount * Quantity) * (DiscountPercent / 100m);
        return new Money(discount, UnitPrice.Currency);
    }

    public Money CalculateNetTotal()
    {
        return CalculateGrossTotal() - CalculateDiscountAmount();
    }

    public void UpdateQuantity(int newQuantity)
    {
        if (newQuantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(newQuantity), "Quantity must be greater than zero.");
        }
        Quantity = newQuantity;
    }
}
