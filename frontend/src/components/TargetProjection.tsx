import { formatChange, formatKilos } from "../features/weight/weightLabels";
import type { TrendProjection } from "../types/weight";

interface TargetProjectionProps {
  readonly projection: TrendProjection;
  readonly targetWeightKg: number | null;
}

const formatTargetDate = (isoDay: string): string => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);

  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
};

const describeWait = (days: number): string => {
  if (days < 14) {
    return `${days} días`;
  }
  if (days < 60) {
    return `unas ${Math.round(days / 7)} semanas`;
  }
  return `unos ${Math.round(days / 30)} meses`;
};

export const TargetProjection = ({ projection, targetWeightKg }: TargetProjectionProps) => {
  const rate =
    projection.kgPerWeek !== null ? `${formatChange(projection.kgPerWeek)} por semana` : null;

  if (projection.status === "reachable" && projection.reachesTargetOn && projection.daysToTarget) {
    return (
      <div className="projection">
        <p className="projection__label">A este ritmo</p>
        <p className="projection__value">{formatTargetDate(projection.reachesTargetOn)}</p>
        <p className="projection__detail">
          {targetWeightKg !== null ? `${formatKilos(targetWeightKg)} en ` : ""}
          {describeWait(projection.daysToTarget)}
          {rate ? `, a ${rate}` : ""}. Es una prolongación de tu ritmo actual, no una promesa:
          en cuanto el ritmo cambie, la fecha cambia con él.
        </p>
      </div>
    );
  }

  if (projection.status === "already_there") {
    return (
      <div className="projection projection--calm">
        <p className="projection__label">Objetivo</p>
        <p className="projection__value">Ya estás ahí</p>
        <p className="projection__detail">
          Tu tendencia está en tu peso objetivo{rate ? `, moviéndose a ${rate}` : ""}.
        </p>
      </div>
    );
  }

  if (projection.status === "wrong_way") {
    return (
      <div className="projection projection--warn">
        <p className="projection__label">A este ritmo</p>
        <p className="projection__value">No llegarías</p>
        <p className="projection__detail">
          La tendencia va en dirección contraria a tu objetivo{rate ? ` (${rate})` : ""}. No es
          un juicio: puede ser una temporada, y la tendencia tarda unos días en reflejar un
          cambio.
        </p>
      </div>
    );
  }

  if (projection.status === "too_flat") {
    return (
      <div className="projection projection--calm">
        <p className="projection__label">A este ritmo</p>
        <p className="projection__value">Sin fecha</p>
        <p className="projection__detail">
          Tu tendencia está plana, así que no hay un ritmo del que sacar una fecha.
        </p>
      </div>
    );
  }

  if (projection.status === "too_far") {
    return (
      <div className="projection projection--calm">
        <p className="projection__label">A este ritmo</p>
        <p className="projection__value">Queda muy lejos</p>
        <p className="projection__detail">
          Al ritmo actual{rate ? ` (${rate})` : ""} la fecha caería a años de distancia, y dar
          ese número sería inventar.
        </p>
      </div>
    );
  }

  return (
    <div className="projection projection--calm">
      <p className="projection__label">A este ritmo</p>
      <p className="projection__value">Aún no se puede decir</p>
      <p className="projection__detail">
        {targetWeightKg === null
          ? "Fija tu peso objetivo en el perfil y, con una semana de registros, te diremos cuándo llegarías."
          : "Con una semana de registros podremos estimar cuándo alcanzarías tu objetivo."}
      </p>
    </div>
  );
};
