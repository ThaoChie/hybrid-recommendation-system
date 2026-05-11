using AuraShop.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace AuraShop.Data.Context;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Category> Categories { get; set; }
    public DbSet<Product> Products { get; set; }
    public DbSet<User> Users { get; set; }
    public DbSet<UserInteraction> UserInteractions { get; set; }
    public DbSet<SearchLog> SearchLogs { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // 1. Tối ưu tính năng Tìm kiếm: Đánh Index cho bảng Product
        modelBuilder.Entity<Product>()
            .HasIndex(p => p.Name);
        modelBuilder.Entity<Product>()
            .HasIndex(p => p.CleanName);

        // 2. Cấu hình khóa ngoại Product -> Category
        modelBuilder.Entity<Product>()
            .HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Cascade);

        // 3. Cấu hình bảng UserInteractions (UserId cho phép NULL)
        modelBuilder.Entity<UserInteraction>()
            .HasOne(ui => ui.User)
            .WithMany()
            .HasForeignKey(ui => ui.UserId)
            .IsRequired(false) // Bắt buộc False để Guest lưu được log
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<UserInteraction>()
            .HasOne(ui => ui.Product)
            .WithMany()
            .HasForeignKey(ui => ui.ProductId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}