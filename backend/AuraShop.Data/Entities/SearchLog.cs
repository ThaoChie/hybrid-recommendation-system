namespace AuraShop.Data.Entities;

public class SearchLog
{
    public int Id { get; set; }
    public string? UserId { get; set; }
    public string? SessionId { get; set; }
    public required string Keyword { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}