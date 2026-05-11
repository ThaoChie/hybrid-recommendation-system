using AuraShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;
using AuraShop.Core.DTOs;
using Microsoft.AspNetCore.Http;

namespace AuraShop.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;
    private readonly IRecommendationService _recommendationService;

    public ProductsController(IProductService productService, IRecommendationService recommendationService)
    {
        _productService = productService;
        _recommendationService = recommendationService;
    }

    // GET: api/v1/products
    // Hợp nhất GetAll và GetProducts vào một hàm duy nhất để tránh lỗi trùng Route
    [HttpGet]
    public async Task<IActionResult> GetProducts(
        [FromQuery] int page = 1, 
        [FromQuery] int pageSize = 20, 
        [FromQuery] string? categoryId = null, 
        [FromQuery] string? keyword = null, 
        [FromQuery] decimal? minPrice = null, 
        [FromQuery] decimal? maxPrice = null, 
        [FromQuery] double? minRating = null,
        [FromQuery] string? sessionId = null, 
        [FromQuery] string? userId = null)
    {
        page = page < 1 ? 1 : page;
        pageSize = pageSize < 1 ? 20 : pageSize;

        // ƯU TIÊN 1: Nếu có từ khóa -> Gọi AI Search thông minh (SearchProductsAsync)
        if (!string.IsNullOrEmpty(keyword))
        {
            // Truyền đủ 3 tham số để tránh lỗi CS7036
            var aiResult = await _productService.SearchProductsAsync(keyword, page, pageSize);
            return Ok(aiResult);
        }

        // ƯU TIÊN 2: Nếu không có từ khóa -> Gọi GetProductsAsync với các bộ lọc (Price, Category...)
        var result = await _productService.GetProductsAsync(
            page, pageSize, categoryId, keyword, minPrice, maxPrice, minRating, sessionId, userId);

        return Ok(result);
    }

    // GET: api/v1/products/{id}
    [HttpGet("{id}")]
    public async Task<IActionResult> GetProductById(string id)
    {
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null) return NotFound(new { message = "Product not found" });
        return Ok(product);
    }

    // GET: api/v1/products/{id}/recommendations
    [HttpGet("{id}/recommendations")]
    public async Task<IActionResult> GetRecommendations(string id)
    {
        var recommendations = await _recommendationService.GetRecommendationsAsync(id, 8);
        return Ok(recommendations);
    }

    // POST: api/v1/products/import-csv/{categoryId}
    [HttpPost("import-csv/{categoryId}")]
    public async Task<IActionResult> ImportCsv(int categoryId, IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("Vui lòng chọn file CSV.");

        try
        {
            using var stream = file.OpenReadStream();
            var count = await _productService.ImportFromCsvAsync(stream, categoryId);
            return Ok(new { message = $"Đã import thành công {count} sản phẩm vào Database cho Danh mục {categoryId}!" });
        }
        catch (Exception ex)
        {
            var actualError = ex.InnerException != null ? ex.InnerException.Message : ex.Message;
            return StatusCode(500, new { message = "Lỗi khi Import CSV", details = actualError });
        }
    }

    // POST: api/v1/products/force-create-categories
    [HttpPost("force-create-categories")]
    public async Task<IActionResult> ForceCreateCategories([FromServices] AuraShop.Data.Context.AppDbContext dbContext)
    {
        if (!dbContext.Categories.Any())
        {
            dbContext.Categories.AddRange(
                new AuraShop.Data.Entities.Category { Id = 1, Name = "Chăm sóc da mặt", Description = "Map AI Beauty" },
                new AuraShop.Data.Entities.Category { Id = 2, Name = "Điện gia dụng", Description = "Map AI Electronic" },
                new AuraShop.Data.Entities.Category { Id = 3, Name = "Bách hóa online", Description = "Map AI Grocery" },
                new AuraShop.Data.Entities.Category { Id = 4, Name = "Thời trang", Description = "Map AI Fashion" }
            );
            await dbContext.SaveChangesAsync();
            return Ok(new { message = "Đã tạo cứng 4 danh mục chuẩn!" });
        }
        var list = dbContext.Categories.Select(c => new { c.Id, c.Name }).ToList();
        return Ok(new { message = "Danh mục đã tồn tại!", data = list });
    }
}