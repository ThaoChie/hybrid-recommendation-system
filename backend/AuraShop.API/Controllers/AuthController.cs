using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace AuraShop.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequestDto request)
    {
        var result = await _authService.LoginAsync(request);
        if (result == null) return Unauthorized(new { message = "Invalid email or password" });
        return Ok(result);
    }

    [HttpPost("register")]
    public async Task<IActionResult> Register([FromBody] RegisterRequestDto request)
    {
        var success = await _authService.RegisterAsync(request);
        if (!success) return BadRequest(new { message = "Email already exists or invalid data" });
        return Ok(new { message = "User registered successfully" });
    }
}