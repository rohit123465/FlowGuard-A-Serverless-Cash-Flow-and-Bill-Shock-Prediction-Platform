import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LoginForm } from "./features/auth/LoginForm";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import { DashboardPage } from "./pages/DashboardPage";
import { ExpensesPage } from "./pages/ExpensesPage";
import { IncomePage } from "./pages/IncomePage";
import { CommitmentsPage } from "./pages/CommitmentsPage";
import { ForecastPage } from "./pages/ForecastPage";

function LoginPage() {
  const { user, loading } = useAuth();
  if (!loading && user) return <Navigate to="/" replace />;
  return <div className="login-page"><div className="login-visual"><p className="eyebrow">FlowGuard</p><h2>See the pressure before it becomes a problem.</h2><p>One protected view of spending today and cash-flow risk tomorrow.</p><div className="visual-stat"><span>Deterministic baseline</span><strong>Explainable by design</strong></div></div><LoginForm /></div>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="expenses" element={<ExpensesPage />} />
          <Route path="income" element={<IncomePage />} />
          <Route path="commitments" element={<CommitmentsPage />} />
          <Route path="forecast" element={<ForecastPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
