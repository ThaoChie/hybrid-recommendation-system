using System.Text.Json;
using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;

namespace AuraShop.Core.Services;

public class RecommendationService : IRecommendationService
{
    private readonly HttpClient _httpClient;
    private readonly AppDbContext _context;
    private readonly string _aiBaseUrl;

    public RecommendationService(HttpClient httpClient, AppDbContext context, IConfiguration config)
    {
        _httpClient = httpClient;
        _context = context;
        _aiBaseUrl = config["AIService:BaseUrl"] ?? "http://localhost:8000";
    }

    public async Task<List<ProductDto>> GetRecommendationsAsync(string productId, int topK = 8)
    {
        try
        {
            // 1. Gọi sang Python FastAPI
            var response = await _httpClient.GetAsync($"{_aiBaseUrl}/recommend/{productId}?top_k={topK}");
            
            if (!response.IsSuccessStatusCode)
                return new List<ProductDto>(); // Trả về list rỗng nếu lỗi (để UI không bị sập)

            var jsonString = await response.Content.ReadAsStringAsync();
            var aiData = JsonSerializer.Deserialize<AiRecommendationResponse>(jsonString);

            if (aiData?.Recommendations == null || !aiData.Recommendations.Any())
                return new List<ProductDto>();

            // 2. Trích xuất danh sách ID sản phẩm do AI gợi ý
            var recommendedIds = aiData.Recommendations.Select(r => r.ProductId.ToString()).ToList();

            // 3. Query xuống MySQL để lấy TÊN THẬT, ẢNH THẬT của các sản phẩm này
            var productsFromDb = await _context.Products
                .Where(p => recommendedIds.Contains(p.Id))
                .ToListAsync();

            // 4. Map sang DTO trả về cho ReactJS
            // (Sắp xếp lại theo đúng thứ tự AI trả về)
            var result = recommendedIds
                .Select(id => productsFromDb.FirstOrDefault(p => p.Id == id))
                .Where(p => p != null)
                .Select(p => new ProductDto
                {
                    Id = p.Id,
                    Name = p.Name,
                    Brand = p.Brand,
                    Price = p.Price,
                    OriginalPrice = p.OriginalPrice,
                    DiscountRate = p.DiscountRate,
                    Rating = p.Rating,
                    ReviewCount = p.ReviewCount,
                    ImageUrl = p.ImageUrl
                })
                .ToList();

            return result;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Lỗi gọi AI Service: {ex.Message}");
            return new List<ProductDto>();
        }
    }
}