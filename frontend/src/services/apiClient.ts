import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// 1. Helper function: Khởi tạo & Lấy guest_session_id từ localStorage
export const getSessionId = (): string => {
  let sessionId = localStorage.getItem('guest_session_id');
  // Nếu chưa có (khởi chạy lần đầu), tự động sinh UUID mới và lưu lại
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('guest_session_id', sessionId);
  }
  return sessionId;
};

// 2. Khởi tạo Axios Instance với Base URL theo đặc tả API
const apiClient = axios.create({
  baseURL: 'http://localhost:5151/api/v1', // Base URL từ tài liệu API
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // Timeout 10s tránh treo request
});

// 3. Request Interceptor: Tự động can thiệp trước khi request gửi đi
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token'); // Lấy JWT Token từ storage
    const sessionId = getSessionId(); // Lấy hoặc tạo sessionId

    // --- XỬ LÝ AUTHENTICATION (Bearer Token) ---
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // --- XỬ LÝ TRACKING & AI (guest_session_id) ---
    // Phương pháp 1: Luôn đính kèm vào Header (Chuẩn Best Practice)
    config.headers['X-Session-Id'] = sessionId;

    // Phương pháp 2: Tự động nhúng vào Query Params hoặc Payload Body 
    
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        sessionId: sessionId
      };
    } else if (config.method === 'post' || config.method === 'put' || config.method === 'patch') {
      // Nhúng vào Request Body cho các POST request (vd: /tracking/interaction)
      // Lưu ý: Chỉ merge nếu payload là Object (tránh lỗi khi gửi FormData hoặc Array)
      if (config.data && typeof config.data === 'object' && !Array.isArray(config.data)) {
        config.data = {
          ...config.data,
          sessionId: sessionId
        };
      } else if (!config.data) {
         // Nếu request POST không có body, tự tạo body chứa sessionId
         config.data = { sessionId: sessionId };
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 4. Response Interceptor: Xử lý lỗi tập trung khi Backend trả về
apiClient.interceptors.response.use(
  (response) => {
    // Nếu gọi API thành công, trả thẳng data ra ngoài cho gọn
    return response;
  },
  (error) => {
    // Xử lý lỗi 401 Unauthorized (Token hết hạn hoặc User chưa đăng nhập mà dám mua hàng)
    if (error.response && error.response.status === 401) {
      console.warn('Unauthorized! Redirecting to login or showing modal...');
      // Xóa token cũ bị lỗi
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.dispatchEvent(new Event('auth-unauthorized'));
    }

    // Ghi log lỗi để dev dễ debug
    console.error('API Error:', error.response?.data?.message || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;