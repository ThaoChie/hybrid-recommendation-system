using System.Text.Json.Serialization;

namespace AuraShop.Core.DTOs;

public class AiRecommendationResponse
{
    [JsonPropertyName("source_product_id")]
    public object SourceProductId { get; set; } // Dùng object vì ID có thể là số hoặc chuỗi

    [JsonPropertyName("category_matched")]
    public string CategoryMatched { get; set; }

    [JsonPropertyName("recommendations")]
    public List<AiProductDto> Recommendations { get; set; }
}

public class AiProductDto
{
    [JsonPropertyName("product_id")]
    public object ProductId { get; set; } 
    
    [JsonPropertyName("name")]
    public string Name { get; set; }
    
    [JsonPropertyName("price")]
    public decimal Price { get; set; }
    
    [JsonPropertyName("rating")]
    public double Rating { get; set; }
}

// LỚP MAP DỮ LIỆU TỪ PYTHON TRẢ VỀ CHO CHỨC NĂNG SEARCH
public class AiSearchResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; }

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("rating")]
    public double Rating { get; set; }

    [JsonPropertyName("image_url")]
    public string ImageUrl { get; set; }

    [JsonPropertyName("score")]
    public double Score { get; set; }

    [JsonPropertyName("category_matched")]
    public string CategoryMatched { get; set; }
}