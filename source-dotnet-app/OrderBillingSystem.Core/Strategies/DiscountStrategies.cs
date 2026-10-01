using OrderBillingSystem.Core.ValueObjects;

namespace OrderBillingSystem.Core.Strategies;

public interface IDiscountStrategy
{
    string StrategyName { get; }
    Money ApplyDiscount(Money currentSubtotal);
}

public sealed class VipDiscountStrategy : IDiscountStrategy
{
    private readonly decimal _discountRate;

    public string StrategyName => "VIP Customer Discount";

    public VipDiscountStrategy(decimal discountRate = 15m)
    {
        _discountRate = discountRate;
    }

    public Money ApplyDiscount(Money currentSubtotal)
    {
        decimal discountAmount = currentSubtotal.Amount * (_discountRate / 100m);
        return new Money(discountAmount, currentSubtotal.Currency);
    }
}

public sealed class CouponDiscountStrategy : IDiscountStrategy
{
    private readonly string _couponCode;
    private readonly Money _fixedDiscount;

    public string StrategyName => $"Coupon: {_couponCode}";

    public CouponDiscountStrategy(string couponCode, Money fixedDiscount)
    {
        _couponCode = couponCode;
        _fixedDiscount = fixedDiscount;
    }

    public Money ApplyDiscount(Money currentSubtotal)
    {
        if (currentSubtotal.Amount <= _fixedDiscount.Amount)
        {
            return currentSubtotal;
        }

        return _fixedDiscount;
    }
}
