import React, { useState } from 'react';
import { Link } from 'react-router'; // Đảm bảo dùng react-router-dom cho chuẩn
import { Star, ShoppingCart } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ImageWithFallback } from './figma/ImageWithFallback';
import apiClient from '../../services/apiClient'; // Import để gọi API Tracking

export interface ProductDto {
  id: string;
  name: string;
  brand: string;
  price: number;
  originalPrice: number;
  discountRate: number;
  rating: number;
  reviewCount: number;
  imageUrl: string;
  categoryName?: string;
}

interface ProductCardProps {
  product: ProductDto;
}

export function ProductCard({ product }: ProductCardProps) {
  const { isAuthenticated, user, openModal } = useAuth();
  const [isAdding, setIsAdding] = useState(false);

  // Hàm xử lý Thêm vào giỏ nhanh từ bên ngoài
  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault(); // Ngăn việc bấm vào nút mà nó lại nhảy sang trang chi tiết
    
    if (!isAuthenticated) {
      openModal();
      return;
    }

    try {
      setIsAdding(true);
      // --- TRACKING: Gửi tín hiệu hành vi cho AI ---
      await apiClient.post('/tracking/cart', {
        productId: product.id,
        userId: user?.id,
        sessionId: "session_temp_123"
      });
      
      alert(`✅ Đã thêm ${product.name} vào giỏ hàng! AI đã ghi nhận sở thích của bạn.`);
    } catch (err) {
      console.error("Lỗi tracking giỏ hàng nhanh:", err);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <Link 
      to={`/product/${product.id}`}
      className="group bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-xl hover:border-transparent transition-all duration-300 flex flex-col h-full"
    >
      <div className="relative aspect-square overflow-hidden bg-gray-50">
        <ImageWithFallback 
          src={product.imageUrl} 
          alt={product.name}
          className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
        />
        {product.discountRate > 0 && (
          <div className="absolute top-3 left-3 bg-red-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-sm">
            -{product.discountRate}%
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col flex-grow">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          {product.brand}
        </div>
        <h3 className="text-gray-900 font-medium mb-2 line-clamp-2 min-h-[40px] group-hover:text-blue-800 transition-colors">
          {product.name}
        </h3>
        
        <div className="flex items-center gap-1 mb-3">
          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
          <span className="text-sm font-medium text-gray-700">{product.rating}</span>
          <span className="text-sm text-gray-400">({product.reviewCount})</span>
        </div>

        <div className="mt-auto flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-red-600">
                {product.price.toLocaleString('vi-VN')}đ
              </span>
            </div>
            {product.discountRate > 0 && (
              <span className="text-sm text-gray-400 line-through">
                {product.originalPrice.toLocaleString('vi-VN')}đ
              </span>
            )}
          </div>
          
          <button 
            onClick={handleAddToCart}
            disabled={isAdding}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors shadow-sm ${
              isAdding ? 'bg-gray-100 text-gray-400' : 'bg-blue-50 text-blue-800 hover:bg-blue-800 hover:text-white'
            }`}
            aria-label="Add to cart"
          >
            <ShoppingCart className={`w-5 h-5 ${isAdding ? 'animate-pulse' : ''}`} />
          </button>
        </div>
      </div>
    </Link>
  );
}