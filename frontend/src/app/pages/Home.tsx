import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { ProductCard } from "../components/ProductCard";
import { productService } from "../../services/product.service";
import { ChevronLeft, ChevronRight } from "lucide-react"; // Thêm icon mũi tên

export function Home() {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const keyword = searchParams.get("q") || "";

  // 1. Khai báo State quản lý phân trang
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 8; 

  useEffect(() => {
    const fetchCatalog = async () => {
      setIsLoading(true);
      try {
        const res = await productService.getProducts(currentPage, pageSize, keyword);
        
        setProducts(res.data);
        
        // Cập nhật tổng số trang từ Backend trả về
        // (Lưu ý: Nếu Backend của bạn đặt tên khác như totalPage, hãy sửa lại cho khớp nhé)
        setTotalPages(res.totalPages || 1); 
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchCatalog();
  }, [keyword, currentPage]); // 2. Thêm currentPage vào mảng để khi đổi trang API sẽ gọi lại

  // Hàm xử lý khi bấm nút chuyển trang
  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      // Cuộn mượt mà lên đầu trang để khách dễ xem
      window.scrollTo({ top: 0, behavior: 'smooth' }); 
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6 text-gray-800">
        {keyword ? `Kết quả tìm kiếm cho "${keyword}"` : "Tất cả sản phẩm"}
      </h1>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-800"></div>
        </div>
      ) : (
        <>
          {/* Lưới sản phẩm */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {products.map((product: any) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {/* 3. GIAO DIỆN NÚT PHÂN TRANG */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8">
              {/* Nút Prev */}
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>

              {/* Các nút số trang */}
              {[...Array(totalPages)].map((_, index) => {
                const page = index + 1;
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`w-10 h-10 rounded-lg font-medium transition-colors shadow-sm ${
                      currentPage === page
                        ? 'bg-blue-800 text-white border-blue-800'
                        : 'border border-gray-200 hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}

              {/* Nút Next */}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}