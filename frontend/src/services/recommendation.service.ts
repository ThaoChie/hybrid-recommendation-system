import apiClient from './apiClient';

export const recommendationService = {
  // Gợi ý trang chủ (Xử lý cả Cold-start & Warm-start ngầm ở Backend)
  getHomepageRecommendations: async (userId: string | null = null) => {
    const response = await apiClient.get('/recommendations/homepage', {
      params: { userId } // apiClient tự động nhét thêm sessionId vào params
    });
    return response.data;
  },

  // Gợi ý sản phẩm tương tự (Content-based ở trang chi tiết)
  getSimilarProducts: async (productId: string, limit: number = 5) => {
    const response = await apiClient.get(`/recommendations/product/${productId}`, {
      params: { limit }
    });
    return response.data;
  }
};