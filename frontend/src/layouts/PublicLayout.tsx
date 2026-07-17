import { Outlet } from "react-router-dom";

import { Brand } from "../components/Brand";
import { applicationConfig } from "../config/environment";

export const PublicLayout = () => (
  <div className="site-shell">
    <header className="site-header">
      <div className="container site-header__content">
        <Brand />
        <nav className="site-header__nav" aria-label="Navegación principal">
          <a href="#como-funciona">Cómo funciona</a>
          <a className="site-header__status-link" href="#estado">
            <span aria-hidden="true" />
            Estado
          </a>
        </nav>
      </div>
    </header>

    <main>
      <Outlet />
    </main>

    <footer className="site-footer">
      <div className="container site-footer__content">
        <Brand compact />
        <p>Una forma clara de entender tus hábitos, paso a paso.</p>
        <p>
          © {new Date().getFullYear()} {applicationConfig.name}. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  </div>
);
