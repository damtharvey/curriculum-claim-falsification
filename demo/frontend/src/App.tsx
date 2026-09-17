import { NavLink, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { ItemBrowser } from "./pages/ItemBrowser";
import { ItemDetail } from "./pages/ItemDetail";
import { WitnessBrowser } from "./pages/WitnessBrowser";
import { InteractiveRunner } from "./pages/InteractiveRunner";
import { About } from "./pages/About";

export function App() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>CCF Demo</h1>
        <nav>
          <NavLink to="/" end className={({ isActive }) => isActive ? "active" : ""}>
            Dashboard
          </NavLink>
          <NavLink to="/items" className={({ isActive }) => isActive ? "active" : ""}>
            Items
          </NavLink>
          <NavLink to="/witnesses" className={({ isActive }) => isActive ? "active" : ""}>
            Witnesses
          </NavLink>
          <NavLink to="/runner" className={({ isActive }) => isActive ? "active" : ""}>
            Run Rules
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => isActive ? "active" : ""}>
            About
          </NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/items" element={<ItemBrowser />} />
          <Route path="/items/:itemId" element={<ItemDetail />} />
          <Route path="/witnesses" element={<WitnessBrowser />} />
          <Route path="/runner" element={<InteractiveRunner />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
    </div>
  );
}
