namespace AuraShop.Data.Entities;

public class Product
{
    public required string Id { get; set; } // Giữ ID gốc dạng chuỗi (vd: SP01, 275515112)
    public int CategoryId { get; set; }
    public required string Name { get; set; }
    public string? CleanName { get; set; } // Đã qua NLP
    public string? Brand { get; set; }
    public decimal Price { get; set; }
    public decimal OriginalPrice { get; set; }
    public double DiscountRate { get; set; }
    public double Rating { get; set; }
    public int ReviewCount { get; set; }
    public string? ImageUrl { get; set; }

    // Navigation properties
    public Category Category { get; set; } = null!;
}