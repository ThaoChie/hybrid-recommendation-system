using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace AuraShop.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")] // Route sẽ tự nhận là /api/v1/checkout
public class CheckoutController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly ITrackingService _trackingService;

    public CheckoutController(AppDbContext context, ITrackingService trackingService)
    {
        _context = context;
        _trackingService = trackingService;
    }

    [HttpPost]
    public async Task<IActionResult> ProcessCheckout([FromBody] List<string> productIds)
    {
        if (productIds == null || !productIds.Any())
            return BadRequest(new { message = "Giỏ hàng trống!" });

        // Lấy User đang đăng nhập 
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        foreach (var id in productIds)
        {
            var product = await _context.Products.FindAsync(id);
            if (product != null)
            {
                product.ReviewCount += 1; 
            }
            
            await _trackingService.LogInteractionAsync(new InteractionRequestDto {
                ProductId = id,
                InteractionType = "buy",
                InteractionValue = 5, 
                UserId = userId,
                SessionId = "session_temp_123" 
            });
        }

        await _context.SaveChangesAsync();
        return Ok(new { status = "success", message = "Thanh toán thành công! Hệ thống đã ghi nhận đơn hàng." });
    }
}