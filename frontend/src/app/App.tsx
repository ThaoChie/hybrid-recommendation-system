import React from 'react';
import { RouterProvider } from 'react-router';
import { router } from './routes';

export default function App() {
  // App entry point
  return <RouterProvider router={router} />;
}
