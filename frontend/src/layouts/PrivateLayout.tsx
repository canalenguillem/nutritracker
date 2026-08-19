import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { Brand } from "../components/Brand";
import { useAuth } from "../features/auth/useAuth";

const SECTIONS = [
  { to: "/dashboard", label: "Hoy" },
  { to: "/weight", label: "Peso" },
  { to: "/profile", label: "Perfil" },
] as const;

export const PrivateLayout = () => {
  const { user, signOut } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);

  const handleSignOut = async () => {
    setIsSigningOut(true);

    try {
      await signOut();
    } finally {
      setIsSigningOut(false);
    }
  };

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container site-header__content">
          <Brand />

          <div className="site-header__account">
            <span className="site-header__account-name">{user?.displayName}</span>
            <button
              className="button button--secondary button--small"
              type="button"
              onClick={() => void handleSignOut()}
              disabled={isSigningOut}
            >
              {isSigningOut ? "Cerrando sesión…" : "Cerrar sesión"}
            </button>
          </div>

          {/* Last in the markup so it wraps onto its own row on a narrow screen. */}
          <nav className="site-header__links" aria-label="Secciones">
            {SECTIONS.map((section) => (
              <NavLink
                key={section.to}
                to={section.to}
                className={({ isActive }) =>
                  isActive ? "site-header__link site-header__link--current" : "site-header__link"
                }
              >
                {section.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
};
