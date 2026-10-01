namespace OrderBillingSystem.Core.ValueObjects;

public sealed record TaxRate
{
    public string CountryCode { get; init; }
    public decimal RatePercentage { get; init; }

    public TaxRate(string countryCode, decimal ratePercentage)
    {
        if (string.IsNullOrWhiteSpace(countryCode))
        {
            throw new ArgumentException("Country code is required.", nameof(countryCode));
        }

        if (ratePercentage < 0 || ratePercentage > 100)
        {
            throw new ArgumentOutOfRangeException(nameof(ratePercentage), "Tax rate must be between 0 and 100.");
        }

        CountryCode = countryCode.ToUpperInvariant();
        RatePercentage = ratePercentage;
    }

    public Money CalculateTax(Money subtotal)
    {
        decimal taxAmount = subtotal.Amount * (RatePercentage / 100m);
        return new Money(taxAmount, subtotal.Currency);
    }
}
