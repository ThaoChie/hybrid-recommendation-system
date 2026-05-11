using AuraShop.Core.DTOs;

namespace AuraShop.Core.Interfaces;

public interface IRecommendationService
{
    Task<List<ProductDto>> GetRecommendationsAsync(string productId, int topK = 8);
}