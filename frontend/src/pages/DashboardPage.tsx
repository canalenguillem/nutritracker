import { Link } from "react-router-dom";

import { MacroTotals } from "../components/MacroTotals";
import { MealCard } from "../components/MealCard";
import { PageLoader } from "../components/PageLoader";
import { getAuthErrorMessage } from "../features/auth/authErrors";
import { useAuth } from "../features/auth/useAuth";
import { formatDay } from "../features/meals/mealLabels";
import { useDailySummary, useDayMeals, useDeleteMeal } from "../features/meals/useMeals";

export const DashboardPage = () => {
  const { user } = useAuth();
  const summaryQuery = useDailySummary();
  const mealsQuery = useDayMeals(summaryQuery.data?.logDate);
  const deleteMeal = useDeleteMeal();

  if (summaryQuery.isPending) {
    return <PageLoader message="Cargando tu día…" />;
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <section className="dashboard">
        <div className="container">
          <p className="auth-form__error" role="alert">
            {getAuthErrorMessage(summaryQuery.error)}
          </p>
        </div>
      </section>
    );
  }

  const summary = summaryQuery.data;
  const meals = mealsQuery.data ?? [];

  return (
    <section className="dashboard">
      <div className="container dashboard__content">
        <div className="dashboard__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            {formatDay(summary.logDate)}
          </p>
          <h1>Hola, {user?.displayName}.</h1>
          <p>
            {summary.mealCount === 0
              ? "Todavía no has registrado nada hoy."
              : `Llevas ${summary.mealCount} ${
                  summary.mealCount === 1 ? "registro" : "registros"
                } hoy.`}
          </p>
        </div>

        <article className="dashboard__card">
          <div className="dashboard__card-head">
            <h2>Resumen de hoy</h2>
            <Link className="button button--primary button--small" to="/meals/new">
              Añadir comida
            </Link>
          </div>
          <MacroTotals macros={summary} />
          <p className="dashboard__disclaimer">
            Los valores son estimaciones a partir de lo que has introducido.
          </p>
        </article>

        <div className="dashboard__meals">
          <h2>Lo que has comido</h2>
          {mealsQuery.isPending ? (
            <p className="dashboard__placeholder">Cargando tus comidas…</p>
          ) : null}
          {mealsQuery.isError ? (
            <p className="auth-form__error" role="alert">
              {getAuthErrorMessage(mealsQuery.error)}
            </p>
          ) : null}
          {!mealsQuery.isPending && meals.length === 0 ? (
            <p className="dashboard__placeholder">
              Cuando añadas tu primera comida aparecerá aquí, con su desglose.
            </p>
          ) : null}
          {meals.map((meal) => (
            <MealCard
              key={meal.id}
              meal={meal}
              onDelete={(mealId) => deleteMeal.mutate(mealId)}
              isDeleting={deleteMeal.isPending && deleteMeal.variables === meal.id}
            />
          ))}
        </div>
      </div>
    </section>
  );
};
