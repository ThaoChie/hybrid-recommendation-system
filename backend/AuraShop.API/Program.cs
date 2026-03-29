using AuraShop.Data.Context;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// 1. Thêm dịch vụ Controllers
builder.Services.AddControllers();

// 2. Cấu hình kết nối MySQL
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)));

// 3. Cấu hình CORS (Cho phép React gọi API)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowReactApp", policy =>
    {
        policy.WithOrigins("http://localhost:5173")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

// 4. Cấu hình JWT Authentication
var jwtSettings = builder.Configuration.GetSection("Jwt");
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtSettings["Issuer"],
        ValidAudience = jwtSettings["Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSettings["Key"]!))
    };
});

// 5. Cấu hình Swagger truyền thống
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// 6. Đăng ký các Services (Dependency Injection)
builder.Services.AddScoped<AuraShop.Core.Interfaces.ITrackingService, AuraShop.Core.Services.TrackingService>();
builder.Services.AddScoped<AuraShop.Core.Interfaces.IProductService, AuraShop.Core.Services.ProductService>();
builder.Services.AddScoped<AuraShop.Core.Interfaces.IAuthService, AuraShop.Core.Services.AuthService>();

var app = builder.Build();

// =================================================================
// 7. KÍCH HOẠT TỰ ĐỘNG BƠM DỮ LIỆU (SEEDER) LÚC KHỞI ĐỘNG
// =================================================================
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    try
    {
        // Gọi hàm tạo Danh mục (Categories) nếu DB đang trống
        await AuraShop.Data.Context.DatabaseSeeder.SeedDataAsync(services);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Lỗi khi bơm dữ liệu: {ex.Message}");
    }
}

// 8. Cấu hình Pipeline (Thứ tự rất quan trọng)
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// Bật CORS (Bắt buộc đứng trước Authentication)
app.UseCors("AllowReactApp");

// Xác thực và phân quyền
app.UseAuthentication();
app.UseAuthorization();

// Map các endpoint
app.MapControllers();

app.Run();