import React from 'react';
import { Outlet } from 'react-router';
import { Header } from './components/Header';
import { AuthModal } from './components/AuthModal';
import { AuthProvider } from '../context/AuthContext';
import { CartProvider } from '../context/CartContext';

export function Layout() {
  return (
    <AuthProvider>
      <CartProvider>
        <div className="min-h-screen bg-white font-sans text-gray-900 flex flex-col">
          <Header />
          <main className="flex-grow">
            <Outlet />
          </main>
          
          {/* Simple Footer */}
          <footer className="bg-gray-900 text-white py-12 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <div className="text-2xl font-bold mb-4">AuraShop Demo</div>
              <p className="text-gray-400 text-sm">
                Demonstrating AI Recommendation UI Patterns (Cold-start & Warm-start).
              </p>
            </div>
          </footer>

          <AuthModal />
        </div>
      </CartProvider>
    </AuthProvider>
  );
}
