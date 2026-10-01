using System.Globalization;

namespace OrderBillingSystem.Core.ValueObjects;

public sealed record Money
{
    public decimal Amount { get; init; }
    public string Currency { get; init; }

    public Money(decimal amount, string currency = "BRL")
    {
        if (amount < 0)
        {
            throw new ArgumentException("Amount cannot be negative.", nameof(amount));
        }

        if (string.IsNullOrWhiteSpace(currency))
        {
            throw new ArgumentException("Currency code cannot be empty.", nameof(currency));
        }

        Amount = Math.Round(amount, 2, MidpointRounding.AwayFromZero);
        Currency = currency.ToUpperInvariant();
    }

    public static Money Zero(string currency = "BRL") => new(0m, currency);

    public static Money operator +(Money left, Money right)
    {
        EnsureSameCurrency(left, right);
        return new Money(left.Amount + right.Amount, left.Currency);
    }

    public static Money operator -(Money left, Money right)
    {
        EnsureSameCurrency(left, right);
        if (left.Amount < right.Amount)
        {
            throw new InvalidOperationException("Resulting money cannot be negative.");
        }
        return new Money(left.Amount - right.Amount, left.Currency);
    }

    public static Money operator *(Money money, decimal multiplier)
    {
        if (multiplier < 0)
        {
            throw new ArgumentException("Multiplier cannot be negative.", nameof(multiplier));
        }
        return new Money(money.Amount * multiplier, money.Currency);
    }

    private static void EnsureSameCurrency(Money left, Money right)
    {
        if (left.Currency != right.Currency)
        {
            throw new InvalidOperationException($"Cannot operate on different currencies: {left.Currency} and {right.Currency}");
        }
    }

    public override string ToString()
    {
        return $"{Currency} {Amount.ToString("N2", CultureInfo.InvariantCulture)}";
    }
}
