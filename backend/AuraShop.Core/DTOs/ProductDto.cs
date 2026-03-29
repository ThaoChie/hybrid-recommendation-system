namespace AuraShop.Core.DTOs;

public class ProductDto
{
    public required string Id { get; set; }
    public required string Name { get; set; }
    public string? Brand { get; set; }
    public decimal Price { get; set; }
    public decimal OriginalPrice { get; set; }
    public double DiscountRate { get; set; }
    public double Rating { get; set; }
    public int ReviewCount { get; set; }
    public string? ImageUrl { get; set; }
    public string? CategoryName { get; set; }
}

// Class bọc data trả về có phân trang
public class PagedResponseDto<T>
{
    public int Page { get; set; }
    public int TotalPages { get; set; }
    public IEnumerable<T> Data { get; set; } = new List<T>();
}