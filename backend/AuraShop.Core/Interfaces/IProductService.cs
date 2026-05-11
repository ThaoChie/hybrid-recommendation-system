using AuraShop.Core.DTOs;
using AuraShop.Data.Entities;
using System.IO;
using System.Threading.Tasks;

namespace AuraShop.Core.Interfaces;

public interface IProductService
{
    // Hàm search dành riêng cho AI
    Task<PagedResponseDto<ProductDto>> SearchProductsAsync(string keyword, int page, int pageSize);

    // Hàm lấy danh sách chung và lọc
    Task<PagedResponseDto<ProductDto>> GetProductsAsync(
        int page, int pageSize, string? categoryId, string? keyword, 
        decimal? minPrice, decimal? maxPrice, double? minRating,
        string? sessionId, string? userId);

    Task<ProductDto?> GetProductByIdAsync(string id);
    Task<int> ImportFromCsvAsync(Stream csvStream, int categoryId);
}