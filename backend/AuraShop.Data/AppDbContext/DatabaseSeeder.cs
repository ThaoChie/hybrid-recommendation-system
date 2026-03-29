using AuraShop.Data.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace AuraShop.Data.Context;

public static class DatabaseSeeder
{
    public static async Task SeedDataAsync(IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        // Tự động chạy Migration nếu chưa chạy
        await context.Database.MigrateAsync();

        // Chỉ tạo 4 Danh mục gốc nếu bảng Categories đang trống
        if (!await context.Categories.AnyAsync())
        {
            var categories = new List<Category>
            {
                new Category { Name = "Bàn phím cơ", Description = "Bàn phím cơ custom & pre-built" },
                new Category { Name = "Phụ kiện Decor", Description = "Pegboard, giá đỡ, đồ trang trí góc máy" },
                new Category { Name = "Đèn thông minh", Description = "Đèn màn hình, LED RGB" },
                new Category { Name = "Âm thanh", Description = "Loa, tai nghe, micro" }
            };
            await context.Categories.AddRangeAsync(categories);
            await context.SaveChangesAsync();
            
            Console.WriteLine("Đã tạo thành công 4 danh mục gốc!");
        }
    }
}