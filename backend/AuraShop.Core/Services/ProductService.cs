using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using Microsoft.EntityFrameworkCore;
using AuraShop.Data.Entities;
using CsvHelper;
using CsvHelper.Configuration;
using System.Globalization;
using System.Net.Http.Json;

namespace AuraShop.Core.Services;

public class ProductService : IProductService
{
    private readonly AppDbContext _context;
    private readonly ITrackingService _trackingService;
    private readonly HttpClient _httpClient;

    public ProductService(AppDbContext context, ITrackingService trackingService, HttpClient httpClient)
    {
        _context = context;
        _trackingService = trackingService;
        _httpClient = httpClient;
    }

    public async Task<PagedResponseDto<ProductDto>> SearchProductsAsync(string keyword, int page, int pageSize)
    {
        // 1. Gọi sang Python FastAPI - Lấy top 50 sản phẩm tốt nhất
        var aiSearchUrl = $"http://ai-service:8000/search?query={Uri.EscapeDataString(keyword)}&top_k=50";
        
        try 
        {
            var aiResults = await _httpClient.GetFromJsonAsync<List<AiSearchResponse>>(aiSearchUrl);
            if (aiResults == null || !aiResults.Any()) 
                return new PagedResponseDto<ProductDto> { Data = new List<ProductDto>() };

            // 2. Lấy danh sách ID
            var productIds = aiResults.Select(r => r.Id).ToList();

            // 3. Query Database lấy dữ liệu thật
            var productsFromDb = await _context.Products
                .Include(p => p.Category)
                .Where(p => productIds.Contains(p.Id))
                .ToListAsync();

            // 4. Sắp xếp lại theo đúng thứ tự AI trả về
            var sortedProducts = productsFromDb
                .OrderBy(p => productIds.IndexOf(p.Id))
                .ToList();

            // 5. Map sang DTO
            var allData = sortedProducts.Select(p => new ProductDto {
                Id = p.Id,
                Name = p.Name,
                Brand = p.Brand ?? "Đang cập nhật",
                Price = p.Price,
                OriginalPrice = p.OriginalPrice,
                DiscountRate = p.DiscountRate,
                ImageUrl = p.ImageUrl ?? "",
                Rating = p.Rating,
                ReviewCount = p.ReviewCount,
                CategoryName = p.Category?.Name
            }).ToList();

            return new PagedResponseDto<ProductDto> {
                Page = page,
                TotalPages = (int)Math.Ceiling(allData.Count / (double)pageSize),
                Data = allData.Skip((page - 1) * pageSize).Take(pageSize).ToList()
            };
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Lỗi gọi AI Service: {ex.Message}");
            return new PagedResponseDto<ProductDto> { Data = new List<ProductDto>() };
        }
    }

    public async Task<PagedResponseDto<ProductDto>> GetProductsAsync(
        int page, int pageSize, string? categoryId, string? keyword, 
        decimal? minPrice, decimal? maxPrice, double? minRating,
        string? sessionId, string? userId)
    {
        if (!string.IsNullOrEmpty(keyword)) 
            return await SearchProductsAsync(keyword, page, pageSize);

        var query = _context.Products.Include(p => p.Category).AsQueryable();

        if (!string.IsNullOrEmpty(categoryId))
            query = query.Where(p => p.CategoryId.ToString() == categoryId);

        if (minPrice.HasValue)
            query = query.Where(p => p.Price >= minPrice.Value);

        if (maxPrice.HasValue)
            query = query.Where(p => p.Price <= maxPrice.Value);

        if (minRating.HasValue)
            query = query.Where(p => p.Rating >= minRating.Value);

        var totalItems = await query.CountAsync();
        var data = await query.Skip((page - 1) * pageSize).Take(pageSize)
            .Select(p => new ProductDto {
                Id = p.Id, 
                Name = p.Name, 
                Brand = p.Brand, 
                Price = p.Price,
                OriginalPrice = p.OriginalPrice,
                DiscountRate = p.DiscountRate,
                ImageUrl = p.ImageUrl, 
                Rating = p.Rating, 
                ReviewCount = p.ReviewCount,
                CategoryName = p.Category!.Name
            }).ToListAsync();

        return new PagedResponseDto<ProductDto> { 
            Page = page, 
            Data = data, 
            TotalPages = (int)Math.Ceiling(totalItems / (double)pageSize) 
        };
    }

    public async Task<ProductDto?> GetProductByIdAsync(string id) 
    {
        var p = await _context.Products.Include(p => p.Category).FirstOrDefaultAsync(x => x.Id == id);
        return p == null ? null : new ProductDto { 
            Id = p.Id, 
            Name = p.Name, 
            Price = p.Price,
            OriginalPrice = p.OriginalPrice,
            DiscountRate = p.DiscountRate,
            ImageUrl = p.ImageUrl,
            Rating = p.Rating,
            ReviewCount = p.ReviewCount,
            Brand = p.Brand,
            CategoryName = p.Category?.Name
        };
    }

    public async Task<int> ImportFromCsvAsync(Stream csvStream, int categoryId) 
    {
        int importedCount = 0;
        try
        {
            // 1. Cấu hình đọc file CSV bỏ qua các lỗi lặt vặt
            using var reader = new StreamReader(csvStream);
            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                HasHeaderRecord = true,
                HeaderValidated = null,
                MissingFieldFound = null,
                BadDataFound = null
            };
            using var csv = new CsvReader(reader, config);
            
            // Map với DTO ProductCsvRecord của bạn
            var records = csv.GetRecords<ProductCsvRecord>().ToList();
            var newProducts = new List<Product>();

            // 2. Chuyển đổi dữ liệu từ CSV sang Entity
            foreach (var record in records)
            {
                var product = new Product
                {
                    Id = Guid.NewGuid().ToString(),
                    CategoryId = categoryId,
                    Name = record.Name,
                    Brand = record.Brand ?? "",
                    Price = record.Price,
                    OriginalPrice = record.OriginalPrice,
                    DiscountRate = record.DiscountRate,
                    Rating = record.Rating,
                    ReviewCount = record.ReviewCount,
                    ImageUrl = record.ImageUrl ?? ""
                };
                newProducts.Add(product);
            }

            // 3. Lưu toàn bộ vào Database
            await _context.Products.AddRangeAsync(newProducts);
            importedCount = await _context.SaveChangesAsync();
            Console.WriteLine($"Đã import thành công {importedCount} sản phẩm vào Database.");

            // 4. 🚀 TỰ ĐỘNG GỌI AI SERVICE ĐỂ HỌC LẠI DỮ LIỆU MỚI
            if (importedCount > 0)
            {
                try 
                {
                    Console.WriteLine("Đang gửi lệnh yêu cầu AI Service cập nhật model...");
                    var response = await _httpClient.PostAsync("http://ai-service:8000/rebuild", null);
                    
                    if (response.IsSuccessStatusCode)
                        Console.WriteLine("✅ AI Service đã học xong dữ liệu mới!");
                    else
                        Console.WriteLine($"⚠️ AI Service phản hồi lỗi: {response.StatusCode}");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Không thể kết nối đến AI Service để rebuild: {ex.Message}");
                }
            }

            return importedCount;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Lỗi nghiêm trọng khi import CSV: {ex.Message}");
            return 0;
        }
    }
}