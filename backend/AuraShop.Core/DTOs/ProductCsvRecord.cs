using CsvHelper.Configuration.Attributes;

namespace AuraShop.Core.DTOs;

public class ProductCsvRecord
{
    [Name("name", "Name")]
    public string Name { get; set; }

    [Name("brand", "Brand")]
    public string? Brand { get; set; }

    [Name("price", "Price")]
    public decimal Price { get; set; }

    [Name("original_price", "originalprice", "OriginalPrice")]
    public decimal OriginalPrice { get; set; }

    [Name("discount_rate", "discountrate", "DiscountRate")]
    public double DiscountRate { get; set; }

    [Name("rating", "Rating")]
    public double Rating { get; set; }

    [Name("review_count", "reviewcount", "ReviewCount")]
    public int ReviewCount { get; set; }

    [Name("image_url", "imageurl", "ImageUrl")]
    public string? ImageUrl { get; set; }
}