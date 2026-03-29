import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { Search, ShoppingCart, User, Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';

export function Header() {
  const { isAuthenticated, user, openModal, logout } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-800 rounded-lg flex items-center justify-center text-white font-bold text-xl">
                A
              </div>
              <span className="text-xl font-bold tracking-tight text-gray-900 hidden sm:block">
                AuraShop
              </span>
            </Link>
          </div>

          {/* Search Bar - Desktop */}
          <div className="flex-1 max-w-2xl mx-8 hidden md:block">
            <form onSubmit={handleSearch} className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-full leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-800 focus:border-blue-800 sm:text-sm transition-all"
                placeholder="Search products, brands and categories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
          </div>

          {/* Right Nav Icons */}
          <div className="flex items-center gap-4 sm:gap-6">
            <button className="md:hidden text-gray-600 hover:text-blue-800">
              <Search className="h-6 w-6" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}/>
            </button>
            
            <div className="relative group">
              <button 
                onClick={isAuthenticated ? undefined : openModal}
                className="flex items-center gap-2 text-gray-600 hover:text-blue-800 transition-colors"
              >
                <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-blue-50 transition-colors">
                  <User className="h-5 w-5" />
                </div>
                <span className="text-sm font-medium hidden lg:block">
                  {isAuthenticated ? user?.name : 'Sign In'}
                </span>
              </button>

              {/* Profile Dropdown (Simple) */}
              {isAuthenticated && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right">
                  <div className="px-4 py-2 border-b border-gray-50">
                    <p className="text-sm font-medium text-gray-900 truncate">{user?.name}</p>
                    <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                  </div>
                  <button onClick={logout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 transition-colors">
                    Sign Out
                  </button>
                </div>
              )}
            </div>

            <Link to="/cart" className="flex items-center text-gray-600 hover:text-blue-800 transition-colors relative">
              <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center hover:bg-blue-50 transition-colors">
                <ShoppingCart className="h-5 w-5" />
              </div>
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full border-2 border-white">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </Link>
          </div>
        </div>
      </div>

      {/* Mobile Search & Menu Expand */}
      {isMobileMenuOpen && (
        <div className="md:hidden p-4 border-t border-gray-100 bg-white">
          <form onSubmit={handleSearch} className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-800"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
        </div>
      )}
    </header>
  );
}
