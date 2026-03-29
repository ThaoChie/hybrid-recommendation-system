using AuraShop.Core.DTOs;

namespace AuraShop.Core.Interfaces;

public interface IAuthService
{
    Task<AuthResponseDto?> LoginAsync(LoginRequestDto request);
    Task<bool> RegisterAsync(RegisterRequestDto request);
}