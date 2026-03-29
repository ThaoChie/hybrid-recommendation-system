namespace AuraShop.Core.DTOs;

public class SearchLogRequestDto
{
    public string? SessionId { get; set; }
    public string? UserId { get; set; }
    public required string Keyword { get; set; }
}