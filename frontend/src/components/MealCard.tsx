import {
  formatEnergy,
  formatGrams,
  formatQuantity,
  formatTime,
  getMealTypeLabel,
} from "../features/meals/mealLabels";
import type { Meal } from "../types/meal";

interface MealCardProps {
  readonly meal: Meal;
  readonly onDelete: (mealId: string) => void;
  readonly isDeleting: boolean;
}

export const MealCard = ({ meal, onDelete, isDeleting }: MealCardProps) => (
  <article className="meal-card">
    <header className="meal-card__header">
      <div>
        <p className="meal-card__type">{getMealTypeLabel(meal.mealType)}</p>
        <p className="meal-card__time">{formatTime(meal.eatenAt)}</p>
      </div>
      <div className="meal-card__energy">
        <strong>{formatEnergy(meal.kcal)}</strong>
        <span>kcal</span>
      </div>
    </header>

    <ul className="meal-card__items">
      {meal.items.map((item) => (
        <li key={item.id}>
          <span className="meal-card__item-name">
            {item.name}
            {item.macrosDisagree ? (
              <span
                className="meal-card__mismatch"
                title={`Sus macros suman ${formatEnergy(item.kcalFromMacros)} kcal`}
              >
                revisar
              </span>
            ) : null}
          </span>
          <span className="meal-card__item-quantity">
            {formatQuantity(item.quantity, item.unit)}
          </span>
          <span className="meal-card__item-energy">{formatEnergy(item.kcal)} kcal</span>
        </li>
      ))}
    </ul>

    {meal.notes ? <p className="meal-card__notes">{meal.notes}</p> : null}

    <footer className="meal-card__footer">
      <p className="meal-card__macros">
        P {formatGrams(meal.proteinG)} g · C {formatGrams(meal.carbohydratesG)} g · G{" "}
        {formatGrams(meal.fatG)} g
      </p>
      <button
        className="meal-card__delete"
        type="button"
        onClick={() => onDelete(meal.id)}
        disabled={isDeleting}
      >
        {isDeleting ? "Borrando…" : "Borrar"}
      </button>
    </footer>
  </article>
);
