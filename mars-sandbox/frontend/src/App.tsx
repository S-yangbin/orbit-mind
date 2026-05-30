import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { Layout } from "./components/Layout";
import { Spin } from "antd";

const LoginPage = lazy(() => import("./components/LoginPage").then(m => ({ default: m.LoginPage })));
const CardGrid = lazy(() => import("./components/CardGrid").then(m => ({ default: m.CardGrid })));
const PagePreview = lazy(() => import("./components/PagePreview").then(m => ({ default: m.PagePreview })));
const NodeManagement = lazy(() => import("./components/NodeManagement").then(m => ({ default: m.NodeManagement })));
const VideoList = lazy(() => import("./components/VideoList").then(m => ({ default: m.VideoList })));
const VideoPlayer = lazy(() => import("./components/VideoPlayer").then(m => ({ default: m.VideoPlayer })));
const MealManagement = lazy(() => import("./components/MealManagement").then(m => ({ default: m.MealManagement })));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
      } />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<CardGrid />} />
        <Route path="nodes" element={<NodeManagement />} />
        <Route path="preview/:id" element={<PagePreview />} />
        <Route path="videos" element={<VideoList />} />
        <Route path="videos/:id" element={<VideoPlayer />} />
        <Route path="meals" element={<MealManagement />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
            background: '#f8fafc',
          }}>
            <Spin size="large" />
          </div>
        }>
          <AppRoutes />
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
