using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using AuraShop.Data.Entities;

namespace AuraShop.Core.Services;

public class TrackingService : ITrackingService
{
    private readonly AppDbContext _context;

    public TrackingService(AppDbContext context)
    {
        _context = context;
    }

    public async Task<bool> LogInteractionAsync(InteractionRequestDto request)
    {
        var interaction = new UserInteraction
        {
            SessionId = request.SessionId,
            UserId = string.IsNullOrWhiteSpace(request.UserId) ? null : request.UserId,
            ProductId = request.ProductId,
            InteractionType = request.InteractionType,
            InteractionValue = request.InteractionValue,
            CreatedAt = DateTime.UtcNow
        };

        _context.UserInteractions.Add(interaction);
        var result = await _context.SaveChangesAsync();
        return result > 0;
    }

    public async Task<bool> LogSearchAsync(SearchLogRequestDto request)
    {
        var searchLog = new SearchLog
        {
            SessionId = request.SessionId,
            UserId = string.IsNullOrWhiteSpace(request.UserId) ? null : request.UserId,
            Keyword = request.Keyword,
            CreatedAt = DateTime.UtcNow
        };

        _context.SearchLogs.Add(searchLog);
        var result = await _context.SaveChangesAsync();
        return result > 0;
    }
}