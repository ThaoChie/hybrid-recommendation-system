namespace AuraShop.Core.DTOs;

public class InteractionRequestDto
{
    public string ProductId { get; set; } = null!;
    public string? SessionId { get; set; }
    public string? UserId { get; set; }
    public string? InteractionType { get; set; }
    public int InteractionValue { get; set; }
}