import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { ProductCard } from "../components/ProductCard";
import { productService } from "../../services/product.service";
import { Filter, ChevronDown } from "lucide-react";

export function Catalog() {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const keyword = searchParams.get("q") || "";

  useEffect(() => {
    const fetchCatalog = async () => {
      setIsLoading(true);
      try {
        const res = await productService.getProducts(1, 20, keyword);
        setProducts(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCatalog();
  }, [keyword]);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">
        {keyword ? `Kết quả tìm kiếm cho "${keyword}"` : "Tất cả sản phẩm"}
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {products.map((product: any) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}