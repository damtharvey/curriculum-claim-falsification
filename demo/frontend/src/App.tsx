import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Items } from "./pages/Items";
import { ItemPage } from "./pages/ItemPage";
import { AdminRules } from "./pages/AdminRules";
import { AdminClaims } from "./pages/AdminClaims";
import { AdminData } from "./pages/AdminData";

export function App() {
  return (
    <>
      <header className="app-header">
        <NavLink to="/items" className="brand">CCF</NavLink>
        <span className="tagline">Does the assessment require the skill?</span>
        <nav>
          <NavLink to="/items">Items</NavLink>
          <NavLink to="/admin/rules">Rules</NavLink>
          <NavLink to="/admin/claims">Claims</NavLink>
          <NavLink to="/admin/data">Data</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/items" replace />} />
          <Route path="/items" element={<Items />} />
          <Route path="/items/:itemId" element={<ItemPage />} />
          <Route path="/admin/rules" element={<AdminRules />} />
          <Route path="/admin/claims" element={<AdminClaims />} />
          <Route path="/admin/data" element={<AdminData />} />
          <Route path="*" element={<Navigate to="/items" replace />} />
        </Routes>
      </main>
    </>
  );
}
