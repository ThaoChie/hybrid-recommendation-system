import apiClient from './apiClient';

// Các loại hành vi được phép lưu
type InteractionType = 'View' | 'Cart' | 'Buy' | 'Rate';

export const trackingService = {
  // Ghi nhận tương tác: View, Add to Cart, Buy, Rate
  trackInteraction: async (
    productId: string, 
    interactionType: InteractionType, 
    interactionValue: number | null = null,
    userId: string | null = null // Truyền null nếu là Guest
  ) => {
    const payload = {
      userId, // Cột này cho phép null trong DB
      productId,
      interactionType,
      interactionValue
    };
  
    const response = await apiClient.post('/tracking/interaction', payload);
    return response.data;
  },

  // Ghi nhận lịch sử tìm kiếm khi User/Guest gõ từ khóa
  trackSearch: async (keyword: string, userId: string | null = null) => {
    const payload = {
      userId,
      keyword
    };
    // apiClient tự động nhét "sessionId" vào payload
    const response = await apiClient.post('/tracking/search', payload);
    return response.data;
  }
};