using AuraShop.Core.DTOs;

namespace AuraShop.Core.Interfaces;

public interface ITrackingService
{
    Task<bool> LogInteractionAsync(InteractionRequestDto request);
    Task<bool> LogSearchAsync(SearchLogRequestDto request);
}