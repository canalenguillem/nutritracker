import { Link } from "react-router-dom";

import { formatDuration, getIntensityLabel } from "../features/exercises/exerciseLabels";
import { formatEnergy, formatTime } from "../features/meals/mealLabels";
import type { Exercise } from "../types/exercise";

interface ExerciseCardProps {
  readonly exercise: Exercise;
  readonly onDelete: (exerciseId: string) => void;
  readonly isDeleting: boolean;
}

export const ExerciseCard = ({ exercise, onDelete, isDeleting }: ExerciseCardProps) => (
  <article className="meal-card">
    <header className="meal-card__header">
      <div>
        <p className="meal-card__type">{exercise.activityName}</p>
        <p className="meal-card__time">
          {formatTime(exercise.performedAt)} · {formatDuration(exercise.durationMinutes)} ·{" "}
          {getIntensityLabel(exercise.intensity)}
        </p>
      </div>
      <div className="meal-card__energy">
        {/* Nothing spent reads as "0", never as "−0". */}
        <strong>
          {exercise.countedCalories === 0
            ? "0"
            : `−${formatEnergy(exercise.countedCalories)}`}
        </strong>
        <span>kcal</span>
      </div>
    </header>

    {exercise.notes ? <p className="meal-card__notes">{exercise.notes}</p> : null}

    <footer className="meal-card__footer">
      <p className="meal-card__macros">
        {exercise.confirmedCalories !== null
          ? "Cifra tuya"
          : exercise.estimatedCalories !== null
            ? "Gasto estimado"
            : "Sin estimar: falta tu peso"}
      </p>
      <div className="meal-card__actions">
        <Link className="meal-card__edit" to={`/exercises/${exercise.id}/edit`}>
          Editar
        </Link>
        <button
          className="meal-card__delete"
          type="button"
          onClick={() => onDelete(exercise.id)}
          disabled={isDeleting}
        >
          {isDeleting ? "Borrando…" : "Borrar"}
        </button>
      </div>
    </footer>
  </article>
);
