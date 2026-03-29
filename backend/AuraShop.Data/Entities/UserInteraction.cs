namespace AuraShop.Data.Entities;

public class UserInteraction
{
    public int Id { get; set; }
    public string? UserId { get; set; } // Nullable cho Guest
    public string? SessionId { get; set; } // SessionId của Guest
    public required string ProductId { get; set; }
    public required string InteractionType { get; set; } // "View", "Cart", "Buy", "Rate"
    public double? InteractionValue { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public User? User { get; set; }
    public Product Product { get; set; } = null!;
}
