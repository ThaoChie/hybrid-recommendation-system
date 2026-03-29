import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router"; 
import { Star, ShieldCheck, Truck, RotateCcw, Cpu, ShoppingCart, CreditCard } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { productService } from "../../services/product.service";
import apiClient from "../../services/apiClient"; // Import để gọi trực tiếp các API tracking/checkout

export function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, user, openModal } = useAuth();
  const navigate = useNavigate();
  
  const [product, setProduct] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const fetchProduct = async () => {
      if (!id) return;
      try {
        setIsLoading(true);
        const data = await productService.getProductById(id);
        setProduct(data);

        // --- TRACKING: Ghi nhận hành vi XEM sản phẩm cho AI ---
        if (id) {
          apiClient.post('/tracking/view', {
            productId: id,
            userId: user?.id || "",
            sessionId: "session_temp_123" 
          }).catch(err => console.error("Tracking view error:", err));
        }
      } catch (err: any) {
        console.error("Lỗi:", err);
        setError("Không tìm thấy sản phẩm hoặc có lỗi xảy ra.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProduct();
  }, [id, user?.id]);

  // LUỒNG 1: THÊM VÀO GIỎ (Ghi nhận hành vi quan tâm cho AI)
  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      openModal();
      return;
    }

    try {
      setIsProcessing(true);
      await apiClient.post('/tracking/cart', {
        productId: product.id,
        userId: user?.id,
        sessionId: "session_temp_123"
      });
      alert("Đã thêm vào giỏ hàng! Hành vi này đã được lưu để AI gợi ý sản phẩm tốt hơn cho bạn.");
    } catch (err) {
      console.error("Lỗi tracking cart:", err);
      alert("Không thể thêm vào giỏ hàng lúc này.");
    } finally {
      setIsProcessing(false);
    }
  };

  // LUỒNG 2: MUA NGAY (Gọi API Fake Checkout của .NET)
  const handleBuyNow = async () => {
    if (!isAuthenticated) {
      openModal();
      return;
    }

    const confirmPurchase = window.confirm(`Bạn có chắc chắn muốn mua ngay sản phẩm ${product.name}?`);
    if (!confirmPurchase) return;

    try {
      setIsProcessing(true);
      // Gọi API Checkout truyền vào ID sản phẩm dưới dạng mảng
      const response = await apiClient.post('/checkout', [product.id]);
      
      if (response.data.status === "success") {
        alert("Chúc mừng! " + response.data.message);
        navigate('/'); 
      }
    } catch (err) {
      console.error("Lỗi thanh toán:", err);
      alert("Thanh toán thất bại. Vui lòng thử lại!");
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-800"></div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[60vh]">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">{error}</h2>
        <Link to="/" className="text-blue-600 hover:underline">Quay lại trang chủ</Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-blue-800">Trang chủ</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{product.name}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm flex items-center justify-center">
          <img 
            src={product.imageUrl} 
            alt={product.name} 
            className="w-full max-w-[500px] h-auto object-cover rounded-xl"
          />
        </div>

        <div className="flex flex-col">
          <div className="text-sm font-semibold text-blue-800 uppercase tracking-wider mb-2">
            {product.brand}
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {product.name}
          </h1>

          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center gap-1">
              <Star className="w-5 h-5 fill-amber-400 text-amber-400" />
              <span className="font-medium text-gray-700">{product.rating}</span>
            </div>
            <span className="text-gray-300">|</span>
            <span className="text-gray-600">{product.reviewCount} đánh giá</span>
          </div>

          <div className="mb-8">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-bold text-red-600">
                {product.price.toLocaleString('vi-VN')}đ
              </span>
              {product.discountRate > 0 && (
                <>
                  <span className="text-lg text-gray-400 line-through">
                    {product.originalPrice.toLocaleString('vi-VN')}đ
                  </span>
                  <span className="bg-red-100 text-red-700 text-sm font-bold px-2 py-1 rounded">
                    -{product.discountRate}%
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Cụm nút hành động mới */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <button 
              onClick={handleBuyNow}
              disabled={isProcessing}
              className="flex-1 bg-orange-600 text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-orange-700 transition-all shadow-lg shadow-orange-600/20 disabled:opacity-50"
            >
              <CreditCard className="w-5 h-5" />
              Mua ngay
            </button>

            <button 
              onClick={handleAddToCart}
              disabled={isProcessing}
              className="flex-1 bg-blue-50 text-blue-800 border-2 border-blue-800 font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-blue-100 transition-all disabled:opacity-50"
            >
              <ShoppingCart className="w-5 h-5" />
              Thêm vào giỏ
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 border-t border-gray-100 pt-8 mt-auto">
            <div className="flex items-start gap-3">
              <Truck className="w-6 h-6 text-blue-800 shrink-0" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Giao hàng miễn phí</div>
                <div className="text-xs text-gray-500">Đơn từ 500k</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-6 h-6 text-blue-800 shrink-0" />
              <div>
                <div className="font-medium text-gray-900 text-sm">Bảo hành chính hãng</div>
                <div className="text-xs text-gray-500">Cam kết 100% auth</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}