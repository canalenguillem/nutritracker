import { useState } from "react";

import { formatEnergy, getMealTypeLabel } from "../features/meals/mealLabels";
import { useRecentMeals } from "../features/meals/useMeals";
import type { Meal } from "../types/meal";

interface RecentMealsProps {
  readonly onPick: (meal: Meal) => void;
  readonly disabled: boolean;
  /** What was last added to the form, so the click has a visible answer. */
  readonly addedNotice: string | null;
}

export const RecentMeals = ({ onPick, disabled, addedNotice }: RecentMealsProps) => {
  const [query, setQuery] = useState("");
  const recentMeals = useRecentMeals(query);
  const meals = recentMeals.data ?? [];

  return (
    <section className="recent" aria-label="Comidas anteriores">
      <label className="form-field__label" htmlFor="recent-search">
        ¿Repites algo que ya comiste?
      </label>
      <p className="recent__hint">
        Búscalo por alimento y añádelo tal cual. Luego puedes ajustar las cantidades.
      </p>
      <input
        className="form-field__input"
        id="recent-search"
        type="search"
        value={query}
        placeholder="mascarpone"
        onChange={(event) => setQuery(event.target.value)}
      />

      {addedNotice ? (
        <p className="recent__added" role="status">
          Añadido al formulario: {addedNotice}. Ya está más abajo, en Alimentos.
        </p>
      ) : null}

      {recentMeals.isPending ? <p className="recent__empty">Buscando…</p> : null}

      {!recentMeals.isPending && meals.length === 0 ? (
        <p className="recent__empty">
          {query.trim()
            ? "No encontramos nada con ese nombre."
            : "Aquí aparecerán las comidas que vayas guardando."}
        </p>
      ) : null}

      <ul className="recent__list">
        {meals.map((meal) => (
          <li key={meal.id}>
            <button type="button" onClick={() => onPick(meal)} disabled={disabled}>
              <span className="recent__names">
                {meal.items.map((item) => item.name).join(" + ")}
              </span>
              <span className="recent__meta">
                {getMealTypeLabel(meal.mealType)} · {formatEnergy(meal.kcal)} kcal
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
};
