using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using Microsoft.EntityFrameworkCore;
using AuraShop.Data.Entities;
using CsvHelper;
using CsvHelper.Configuration;
using System.Globalization;

namespace AuraShop.Core.Services;

public class ProductService : IProductService
{
    private readonly AppDbContext _context;
    private readonly ITrackingService _trackingService;

    // Inject DbContext và TrackingService vào đây
    public ProductService(AppDbContext context, ITrackingService trackingService)
    {
        _context = context;
        _trackingService = trackingService;
    }

    public async Task<PagedResponseDto<ProductDto>> GetProductsAsync(
        int page, int pageSize, string? categoryId, string? keyword, 
        decimal? minPrice, decimal? maxPrice, double? minRating,
        string? sessionId, string? userId)
    {
        var query = _context.Products.Include(p => p.Category).AsQueryable();

        // Lọc theo Category
        if (!string.IsNullOrEmpty(categoryId) && int.TryParse(categoryId, out int catId))
        {
            query = query.Where(p => p.CategoryId == catId);
        }

        // Lọc theo Keyword & Tự động ghi Log
        if (!string.IsNullOrEmpty(keyword))
        {
            query = query.Where(p => p.Name.Contains(keyword) || (p.CleanName != null && p.CleanName.Contains(keyword)));
            
            // Ghi log tìm kiếm chạy ngầm (Không cần await để tránh block luồng get data)
            _ = _trackingService.LogSearchAsync(new SearchLogRequestDto 
            { 
                Keyword = keyword, 
                SessionId = sessionId, 
                UserId = userId 
            });
        }

        // Lọc theo Giá và Rating
        if (minPrice.HasValue) query = query.Where(p => p.Price >= minPrice.Value);
        if (maxPrice.HasValue) query = query.Where(p => p.Price <= maxPrice.Value);
        if (minRating.HasValue) query = query.Where(p => p.Rating >= minRating.Value);

        // Tính toán phân trang
        var totalItems = await query.CountAsync();
        var totalPages = (int)Math.Ceiling(totalItems / (double)pageSize);

        var products = await query
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
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
                ImageUrl = p.ImageUrl,
                CategoryName = p.Category.Name
            })
            .ToListAsync();

        return new PagedResponseDto<ProductDto>
        {
            Page = page,
            TotalPages = totalPages > 0 ? totalPages : 1,
            Data = products
        };
    }

    public async Task<ProductDto?> GetProductByIdAsync(string id)
    {
        var p = await _context.Products
            .Include(prod => prod.Category)
            .FirstOrDefaultAsync(prod => prod.Id == id);

        if (p == null) return null;

        return new ProductDto
        {
            Id = p.Id,
            Name = p.Name,
            Brand = p.Brand,
            Price = p.Price,
            OriginalPrice = p.OriginalPrice,
            DiscountRate = p.DiscountRate,
            Rating = p.Rating,
            ReviewCount = p.ReviewCount,
            ImageUrl = p.ImageUrl,
            CategoryName = p.Category.Name
        };
    }

    public async Task<int> ImportFromCsvAsync(Stream csvStream)
    {
        // Cấu hình CsvHelper: Dùng chuẩn quốc tế, tự động bỏ qua cột trống nếu có
        var config = new CsvConfiguration(CultureInfo.InvariantCulture)
        {
            HasHeaderRecord = true,
            MissingFieldFound = null,
            HeaderValidated = null
        };

        using var reader = new StreamReader(csvStream);
        using var csv = new CsvReader(reader, config);

        // Đọc toàn bộ dữ liệu từ file CSV ép sang List
        var records = csv.GetRecords<ProductCsvRecord>().ToList();
        var productsToInsert = new List<Product>();

        foreach (var record in records)
        {
            // Kiểm tra xem Id sản phẩm đã tồn tại trong DB chưa để tránh lỗi trùng lặp (Duplicate Key)
            if (!await _context.Products.AnyAsync(p => p.Id == record.Id))
            {
                // Tính toán tự động phần trăm giảm giá
                double discount = record.OriginalPrice > 0 
                    ? (double)((record.OriginalPrice - record.Price) / record.OriginalPrice * 100) 
                    : 0;

                productsToInsert.Add(new Product
                {
                    Id = record.Id,
                    CategoryId = record.CategoryId,
                    Name = record.Name,
                    CleanName = record.Name.ToLower(), // Xử lý tạm tên để dễ tìm kiếm
                    Brand = record.Brand,
                    Price = record.Price,
                    OriginalPrice = record.OriginalPrice,
                    DiscountRate = Math.Round(discount, 1),
                    Rating = 5.0, // Sản phẩm mới mặc định 5 sao
                    ReviewCount = 0,
                    ImageUrl = record.ImageUrl
                });
            }
        }

        // Lưu hàng loạt (Bulk Insert) vào MySQL
        if (productsToInsert.Any())
        {
            await _context.Products.AddRangeAsync(productsToInsert);
            await _context.SaveChangesAsync();
        }

        return productsToInsert.Count; // Trả về số lượng đã import thành công
    }
}