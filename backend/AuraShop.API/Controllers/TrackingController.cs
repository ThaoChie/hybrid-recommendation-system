using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace AuraShop.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class TrackingController : ControllerBase
{
    private readonly ITrackingService _trackingService;

    public TrackingController(ITrackingService trackingService)
    {
        _trackingService = trackingService;
    }

    //hành vi: 'view', 'buy', 'rate'
    [HttpPost("{type}")]
    public async Task<IActionResult> LogAction(string type, [FromBody] InteractionRequestDto request)
    {
        var actionType = type.ToLower();

        if (actionType != "view" && actionType != "buy" && actionType != "rate")
        {
            return BadRequest(new { message = "Hệ thống AI chỉ hỗ trợ tracking: view, buy, rate" });
        }

        request.InteractionType = actionType;

        if (actionType == "rate") 
        {
            if (request.InteractionValue < 1 || request.InteractionValue > 5)
            {
                return BadRequest(new { message = "Điểm đánh giá phải từ 1 đến 5 sao." });
            }
        }
        else
        {
            request.InteractionValue = actionType == "buy" ? 5 : 1;
        }

        // 3. Lưu xuống Database
        var success = await _trackingService.LogInteractionAsync(request);
        
        if (success) 
        {
            return Ok(new { message = $"Đã ghi nhận hành vi '{actionType}' với {request.InteractionValue} điểm." });
        }
        
        return StatusCode(500, new { message = "Lỗi khi lưu dữ liệu tracking." });
    }
}