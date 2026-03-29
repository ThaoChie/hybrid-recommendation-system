import apiClient from './apiClient';

export const checkoutService = {
  // Fake Checkout: Gửi danh sách ID sản phẩm muốn mua
  fakeCheckout: async (productIds: string[]) => {
    // Interceptor tự động check và gắn Header Authorization: Bearer <Token>
    const response = await apiClient.post('/checkout', productIds);
    return response.data;
  }
};