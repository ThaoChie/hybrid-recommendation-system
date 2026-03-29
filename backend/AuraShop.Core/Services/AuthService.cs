using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using AuraShop.Core.DTOs;
using AuraShop.Core.Interfaces;
using AuraShop.Data.Context;
using AuraShop.Data.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace AuraShop.Core.Services;

public class AuthService : IAuthService
{
    private readonly AppDbContext _context;
    private readonly IConfiguration _configuration;

    public AuthService(AppDbContext context, IConfiguration configuration)
    {
        _context = context;
        _configuration = configuration;
    }

    public async Task<bool> RegisterAsync(RegisterRequestDto request)
    {
        // Kiểm tra email tồn tại chưa
        if (await _context.Users.AnyAsync(u => u.Email == request.Email))
            return false;

        var user = new User
        {
            Id = Guid.NewGuid().ToString(),
            Username = request.Username,
            Email = request.Email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password) // Băm mật khẩu
        };

        _context.Users.Add(user);
        return await _context.SaveChangesAsync() > 0;
    }

    public async Task<AuthResponseDto?> LoginAsync(LoginRequestDto request)
    {
        var user = await _context.Users.FirstOrDefaultAsync(u => u.Email == request.Email);
        
        // Check user tồn tại và mật khẩu khớp không
        if (user == null || !BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash))
            return null;

        var token = GenerateJwtToken(user);

        return new AuthResponseDto
        {
            Token = token,
            UserId = user.Id,
            Username = user.Username
        };
    }

    private string GenerateJwtToken(User user)
    {
        // Lấy Secret Key từ appsettings.json
        var jwtSettings = _configuration.GetSection("Jwt");
        var key = Encoding.ASCII.GetBytes(jwtSettings["Key"]!);

        var tokenHandler = new JwtSecurityTokenHandler();
        var tokenDescriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity(new[]
            {
                new Claim(ClaimTypes.NameIdentifier, user.Id),
                new Claim(ClaimTypes.Email, user.Email),
                new Claim(ClaimTypes.Name, user.Username)
            }),
            Expires = DateTime.UtcNow.AddDays(7), // Token sống 7 ngày
            SigningCredentials = new SigningCredentials(new SymmetricSecurityKey(key), SecurityAlgorithms.HmacSha256Signature),
            Issuer = jwtSettings["Issuer"],
            Audience = jwtSettings["Audience"]
        };

        var token = tokenHandler.CreateToken(tokenDescriptor);
        return tokenHandler.WriteToken(token);
    }
}