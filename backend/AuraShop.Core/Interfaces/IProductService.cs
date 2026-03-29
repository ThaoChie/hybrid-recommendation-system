using AuraShop.Core.DTOs;

namespace AuraShop.Core.Interfaces;

public interface IProductService
{
    Task<PagedResponseDto<ProductDto>> GetProductsAsync(
        int page, int pageSize, string? categoryId, string? keyword, 
        decimal? minPrice, decimal? maxPrice, double? minRating,
        string? sessionId, string? userId);
        
    Task<ProductDto?> GetProductByIdAsync(string id);
    Task<int> ImportFromCsvAsync(Stream csvStream);
}