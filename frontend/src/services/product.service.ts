import apiClient from './apiClient';

export const productService = {
  // 1. Lấy danh sách sản phẩm (Trang chủ/Catalog)
  getProducts: async (page = 1, pageSize = 20, keyword = '') => {
    const response = await apiClient.get('/products', {
      params: { page, pageSize, keyword }
    });
    return response.data;
  },

  // 2. Lấy chi tiết 1 sản phẩm
  getProductById: async (id: string) => {
    const response = await apiClient.get(`/products/${id}`);
    return response.data;
  },

  // 3. API Mua ngay (Fake Checkout)
  // Truyền vào mảng các ID sản phẩm
  checkout: async (productIds: string[]) => {
    const response = await apiClient.post('/checkout', productIds);
    return response.data;
  },

  // 4. API Tracking (Gửi dữ liệu hành vi cho AI)
  // Type có thể là: 'view' (xem), 'cart' (thêm giỏ), 'search' (tìm kiếm)
  trackAction: async (type: 'view' | 'cart' | 'search', data: any) => {
    const response = await apiClient.post(`/tracking/${type}`, data);
    return response.data;
  }
};