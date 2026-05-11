using System;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace AuraShop.Data.Context; // Namespace trỏ đúng vào thư mục Context

/// <summary>
/// Khởi tạo Database với cơ chế Retry chống lỗi khi MySQL chưa sẵn sàng
/// </summary>
public static class DatabaseInitializer
{
    private const int MaxRetries = 5;
    private const int DelaySeconds = 4;

    public static async Task InitializeAsync(IServiceProvider serviceProvider, ILogger logger)
    {
        using var scope = serviceProvider.CreateScope();
        
        // ĐÃ SỬA: Dùng chuẩn AppDbContext của dự án
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        for (int attempt = 1; attempt <= MaxRetries; attempt++)
        {
            try
            {
                logger.LogInformation("🔌 [DB Init] Attempt {Attempt}/{Max}: Connecting to MySQL...", attempt, MaxRetries);

                // Kiểm tra kết nối
                await context.Database.CanConnectAsync();
                logger.LogInformation("✅ [DB Init] Connection OK. Applying schema...");

                // Tạo DB + Tables nếu chưa có. 
                // Dùng EnsureCreated cực kỳ an toàn khi chạy Docker lần đầu
                var created = await context.Database.EnsureCreatedAsync();

                if (created)
                    logger.LogInformation("🆕 [DB Init] Database created successfully with schema.");
                else
                    logger.LogInformation("✅ [DB Init] Database already exists. Schema verified.");

                // Đảm bảo Charset đúng cho Tiếng Việt
                await EnsureCharsetAsync(context, logger);

                logger.LogInformation("🎉 [DB Init] Initialization complete!");
                return; // Thành công, thoát vòng lặp
            }
            catch (Exception ex) when (attempt < MaxRetries)
            {
                logger.LogWarning(
                    "⚠️  [DB Init] Attempt {Attempt} failed: {Message}. Retrying in {Delay}s...",
                    attempt, ex.Message, DelaySeconds);
                await Task.Delay(TimeSpan.FromSeconds(DelaySeconds));
            }
            catch (Exception ex)
            {
                logger.LogCritical(
                    ex,
                    "💥 [DB Init] All {Max} attempts failed. Application cannot start without database.",
                    MaxRetries);
                throw; // Re-throw để crash app có log rõ ràng
            }
        }
    }

    /// <summary>
    /// Đảm bảo MySQL dùng utf8mb4 để hỗ trợ tiếng Việt đầy đủ (NFD/NFC)
    /// </summary>
    private static async Task EnsureCharsetAsync(AppDbContext context, ILogger logger)
    {
        try
        {
            // Ép MySQL dùng bảng mã utf8mb4 chuẩn Unicode
            await context.Database.ExecuteSqlRawAsync(
                "ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            logger.LogInformation("✅ [DB Init] Charset set to utf8mb4_unicode_ci");
        }
        catch (Exception ex)
        {
            // Lỗi này không nghiêm trọng (có thể do user MySQL không có quyền ALTER), chỉ log lại
            logger.LogDebug("[DB Init] Charset alter skipped (likely already set): {Msg}", ex.Message);
        }
    }
}