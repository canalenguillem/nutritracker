import { Link, useSearchParams } from "react-router-dom";

import { DailyBalance } from "../components/DailyBalance";
import { DayPicker } from "../components/DayPicker";
import { DayStrip } from "../components/DayStrip";
import { ExerciseCard } from "../components/ExerciseCard";
import { FastingWindow } from "../components/FastingWindow";
import { SleptNightCard } from "../components/SleptNightCard";
import { MacroTotals } from "../components/MacroTotals";
import { MealCard } from "../components/MealCard";
import { PageLoader } from "../components/PageLoader";
import { useAuth } from "../features/auth/useAuth";
import { formatDay } from "../features/meals/mealLabels";
import {
  useDayExercises,
  useDeleteExercise,
} from "../features/exercises/useExercises";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import { useDailySummary, useDayMeals, useDeleteMeal } from "../features/meals/useMeals";

export const DashboardPage = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  // The day being read lives in the address, so it survives a reload and can
  // be shared or bookmarked.
  const requestedDay = searchParams.get("date");
  const summaryQuery = useDailySummary(requestedDay ?? undefined);
  const todayQuery = useDailySummary();
  const mealsQuery = useDayMeals(summaryQuery.data?.logDate);
  const exercisesQuery = useDayExercises(summaryQuery.data?.logDate);
  const deleteMeal = useDeleteMeal();
  const deleteExercise = useDeleteExercise();

  if (summaryQuery.isPending) {
    return <PageLoader message="Cargando tu día…" />;
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <section className="dashboard">
        <div className="container">
          <p className="auth-form__error" role="alert">
            {getMealErrorMessage(summaryQuery.error)}
          </p>
        </div>
      </section>
    );
  }

  const summary = summaryQuery.data;
  const meals = mealsQuery.data ?? [];
  const exercises = exercisesQuery.data ?? [];
  const today = todayQuery.data?.logDate ?? summary.logDate;
  const isToday = summary.logDate === today;
  const selectDay = (day: string) => {
    setSearchParams(day === today ? {} : { date: day }, { replace: true });
  };

  return (
    <section className="dashboard">
      <div className="container dashboard__content">
        <div className="dashboard__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            {formatDay(summary.logDate)}
          </p>
          <h1>{isToday ? `Hola, ${user?.displayName}.` : "Lo que registraste"}</h1>
          <p>
            {summary.mealCount === 0
              ? isToday
                ? "Todavía no has registrado nada hoy."
                : "Ese día no registraste ninguna comida."
              : `${summary.mealCount} ${
                  summary.mealCount === 1 ? "registro" : "registros"
                }${isToday ? " hoy" : " ese día"}.`}
          </p>
        </div>

        <DayPicker selectedDay={summary.logDate} today={today} onSelect={selectDay} />

        <DayStrip selectedDay={summary.logDate} today={today} onSelect={selectDay} />

        <article className="dashboard__card">
          <div className="dashboard__card-head">
            <h2>{isToday ? "Resumen de hoy" : "Resumen del día"}</h2>
            <div className="dashboard__actions">
              <Link className="button button--primary button--small" to="/meals/new">
                Añadir comida
              </Link>
              <Link className="button button--secondary button--small" to="/exercises/new">
                Añadir ejercicio
              </Link>
              <Link className="button button--secondary button--small" to="/sleep/new">
                Añadir sueño
              </Link>
            </div>
          </div>
          <MacroTotals macros={summary} />
          <p className="dashboard__disclaimer">
            Los valores son estimaciones a partir de lo que has introducido.
          </p>
        </article>

        <DailyBalance summary={summary} />

        <div className="dashboard__rhythm">
          <FastingWindow summary={summary} />
          <SleptNightCard day={summary.logDate} isToday={isToday} />
        </div>

        <div className="dashboard__meals">
          <h2>Lo que has comido</h2>
          {mealsQuery.isPending ? (
            <p className="dashboard__placeholder">Cargando tus comidas…</p>
          ) : null}
          {mealsQuery.isError ? (
            <p className="auth-form__error" role="alert">
              {getMealErrorMessage(mealsQuery.error)}
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

        <div className="dashboard__meals">
          <h2>Lo que has movido</h2>
          {exercises.length === 0 ? (
            <p className="dashboard__placeholder">
              Cuando añadas una sesión aparecerá aquí, con su gasto estimado.
            </p>
          ) : null}
          {exercises.map((exercise) => (
            <ExerciseCard
              key={exercise.id}
              exercise={exercise}
              onDelete={(exerciseId) => deleteExercise.mutate(exerciseId)}
              isDeleting={deleteExercise.isPending && deleteExercise.variables === exercise.id}
            />
          ))}
        </div>
      </div>
    </section>
  );
};
