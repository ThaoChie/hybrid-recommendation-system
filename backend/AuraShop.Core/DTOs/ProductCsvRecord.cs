namespace AuraShop.Core.DTOs;

public class ProductCsvRecord
{
    public required string Id { get; set; }
    public int CategoryId { get; set; }
    public required string Name { get; set; }
    public string? Brand { get; set; }
    public decimal Price { get; set; }
    public decimal OriginalPrice { get; set; }
    public string? ImageUrl { get; set; }
}