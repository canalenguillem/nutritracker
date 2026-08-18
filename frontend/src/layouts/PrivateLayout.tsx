import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Brand } from "../components/Brand";
import { useAuth } from "../features/auth/useAuth";

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
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
};
