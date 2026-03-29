namespace AuraShop.Data.Entities;

public class Category
{
    public int Id { get; set; }
    public required string Name { get; set; }
    public string? Description { get; set; }

    // Navigation property
    public ICollection<Product> Products { get; set; } = new List<Product>();
}