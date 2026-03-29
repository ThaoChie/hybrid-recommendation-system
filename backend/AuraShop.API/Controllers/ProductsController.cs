using AuraShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace AuraShop.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;

    public ProductsController(IProductService productService)
    {
        _productService = productService;
    }

    // GET: api/v1/products
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
        // Đảm bảo page >= 1
        page = page < 1 ? 1 : page;
        pageSize = pageSize < 1 ? 20 : pageSize;

        var result = await _productService.GetProductsAsync(
            page, pageSize, categoryId, keyword, minPrice, maxPrice, minRating, sessionId, userId);

        return Ok(result);
    }

    // GET: api/v1/products/{id}
    [HttpGet("{id}")]
    public async Task<IActionResult> GetProductById(string id)
    {
        var product = await _productService.GetProductByIdAsync(id);
        
        if (product == null)
            return NotFound(new { message = "Product not found" });

        return Ok(product);
    }

    [HttpPost("import")]
    public async Task<IActionResult> ImportCsv(IFormFile file)
    {
        // 1. Kiểm tra file có tồn tại không
        if (file == null || file.Length == 0)
            return BadRequest(new { message = "Vui lòng đính kèm một file CSV." });

        // 2. Kiểm tra đúng đuôi .csv không
        if (!file.FileName.EndsWith(".csv", StringComparison.OrdinalIgnoreCase))
            return BadRequest(new { message = "Hệ thống chỉ chấp nhận định dạng file .csv" });

        try
        {
            using var stream = file.OpenReadStream();
            var importedCount = await _productService.ImportFromCsvAsync(stream);

            return Ok(new 
            { 
                message = "Import thành công!", 
                itemsAdded = importedCount 
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = "Lỗi trong quá trình đọc file CSV.", details = ex.Message });
        }
    }
}