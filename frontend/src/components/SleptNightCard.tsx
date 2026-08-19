import { Link } from "react-router-dom";

import { formatTime } from "../features/meals/mealLabels";
import { formatSleepLength, getQualityLabel } from "../features/sleep/sleepLabels";
import { useDeleteNight, useNight } from "../features/sleep/useSleep";

interface SleptNightCardProps {
  readonly day: string;
  readonly isToday: boolean;
}

export const SleptNightCard = ({ day, isToday }: SleptNightCardProps) => {
  const night = useNight(day);
  const deleteNight = useDeleteNight();

  if (night.isPending) {
    return null;
  }

  if (!night.data) {
    return (
      <div className="sleep sleep--empty">
        <p className="sleep__label">Sueño</p>
        <p className="sleep__detail">
          {isToday
            ? "No has apuntado cuánto dormiste anoche."
            : "No apuntaste el sueño de esa noche."}{" "}
          {isToday ? <Link to="/sleep/new">Añadirlo</Link> : null}
        </p>
      </div>
    );
  }

  const slept = night.data;

  return (
    <div className="sleep">
      <div className="sleep__head">
        <div>
          <p className="sleep__label">Sueño</p>
          <p className="sleep__value">{formatSleepLength(slept.hours)}</p>
        </div>
        {slept.quality ? (
          <span className={`sleep__quality sleep__quality--${slept.quality}`}>
            {getQualityLabel(slept.quality)}
          </span>
        ) : null}
      </div>

      <p className="sleep__detail">
        De las {formatTime(slept.startedAt)} a las {formatTime(slept.endedAt)}.
      </p>

      {slept.notes ? <p className="sleep__notes">{slept.notes}</p> : null}

      <div className="sleep__actions">
        <Link className="meal-card__edit" to={`/sleep/${slept.id}/edit`}>
          Editar
        </Link>
        <button
          className="sleep__remove"
          type="button"
          onClick={() => deleteNight.mutate(slept.id)}
          disabled={deleteNight.isPending}
        >
          {deleteNight.isPending ? "Borrando…" : "Borrar"}
        </button>
      </div>
    </div>
  );
};
