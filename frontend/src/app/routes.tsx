import React from "react";
import { createBrowserRouter } from "react-router";
import { Layout } from "./Layout";
import { Home } from "./pages/Home";
import { Catalog } from "./pages/Catalog";
import { ProductDetail } from "./pages/ProductDetail";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: "search", element: <Catalog /> },
      { path: "product/:id", element: <ProductDetail /> },
      { path: "*", element: <Home /> },
    ],
  },
]);
