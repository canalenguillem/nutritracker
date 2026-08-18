import { useAuth } from "../features/auth/useAuth";

export const DashboardPage = () => {
  const { user } = useAuth();

  return (
    <section className="dashboard">
      <div className="container dashboard__content">
        <div className="dashboard__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            Tu panel
          </p>
          <h1>Hola, {user?.displayName}.</h1>
          <p>
            Tu cuenta ya está activa. El registro de comidas, actividad y peso llegará en las
            siguientes fases.
          </p>
        </div>

        <article className="dashboard__card">
          <h2>Resumen de hoy</h2>
          <p className="dashboard__placeholder">
            Todavía no hay registros. Cuando empieces a añadir comidas, aquí verás tu balance
            calórico diario.
          </p>
        </article>
      </div>
    </section>
  );
};
