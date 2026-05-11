using System.Globalization;
using System.Text;

namespace AuraShop.Core.Helpers; // Sửa thành AuraShop.Core.Helpers nếu file bạn nằm trong thư mục Helpers

public static class TextHelper
{
    /// <summary>
    /// Xóa toàn bộ dấu Tiếng Việt (Ví dụ: "Sữa Rửa Mặt" -> "sua rua mat")
    /// </summary>
    public static string RemoveDiacritics(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return text;
        
        text = text.ToLowerInvariant();
        var normalizedString = text.Normalize(NormalizationForm.FormD);
        var stringBuilder = new StringBuilder(capacity: normalizedString.Length);

        foreach (var c in normalizedString)
        {
            var unicodeCategory = CharUnicodeInfo.GetUnicodeCategory(c);
            if (unicodeCategory != UnicodeCategory.NonSpacingMark)
            {
                stringBuilder.Append(c);
            }
        }

        return stringBuilder.ToString().Normalize(NormalizationForm.FormC).Replace("đ", "d");
    }

    /// <summary>
    /// Xóa ký tự tàng hình (BOM / Zero-width space) khi đọc file CSV từ Excel
    /// </summary>
    public static string RemoveBom(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        
        return text.Replace("\xEF\xBB\xBF", "")
                   .Replace("\ufeff", "")
                   .Replace("\u200B", "") // Xóa thêm Zero-width space nếu có
                   .Trim();
    }
}