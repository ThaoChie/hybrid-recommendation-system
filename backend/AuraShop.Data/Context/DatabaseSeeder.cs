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

        // Xóa dữ liệu cũ nếu muốn làm mới (Tùy chọn - hữu ích khi đang test)
        await context.Database.ExecuteSqlRawAsync("DELETE FROM Categories");
        //await context.Database.ExecuteSqlRawAsync("ALTER TABLE Categories AUTO_INCREMENT = 1");

        // Tạo Danh mục gốc KHỚP VỚI SCRIPT PYTHON AI
        if (!await context.Categories.AnyAsync())
        {
            var categories = new List<Category>
            {
                new Category { Name = "Chăm sóc da mặt", Description = "Mỹ phẩm, sữa rửa mặt, kem dưỡng (Map với AI Beauty)" }, // ID 1
                new Category { Name = "Điện gia dụng", Description = "Thiết bị điện tử, gia dụng (Map với AI Electronic)" }, // ID 2
                new Category { Name = "Bách hóa online", Description = "Thực phẩm, hàng tiêu dùng (Map với AI Grocery)" }, // ID 3
                new Category { Name = "Phụ kiện Decor", Description = "Sản phẩm công nghệ, decor góc máy" } // ID 4 
            };
            
            await context.Categories.AddRangeAsync(categories);
            await context.SaveChangesAsync();
            
            Console.WriteLine("Đã tạo thành công các danh mục gốc khớp với AI Model!");
        }
    }
}