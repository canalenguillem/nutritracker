import { Link } from "react-router-dom";

import { formatEnergy } from "../features/meals/mealLabels";
import type { DailySummary } from "../types/meal";

/** Nothing spent reads as "0 kcal", never as "−0 kcal". */
const formatSpent = (kcal: number): string =>
  kcal === 0 ? "0 kcal" : `−${formatEnergy(kcal)} kcal`;

interface DailyBalanceProps {
  readonly summary: DailySummary;
}

export const DailyBalance = ({ summary }: DailyBalanceProps) => {
  if (summary.balanceStatus === "needs_profile") {
    return (
      <div className="balance balance--pending">
        <p className="balance__label">Balance del día</p>
        <p className="balance__value">Aún no se puede decir</p>
        <p className="balance__detail">
          Para saber si hay déficit hace falta lo que gastas en reposo, y eso necesita tu
          estatura, tu peso y tu fecha de nacimiento. <Link to="/profile">Completa tu perfil</Link>{" "}
          y aparecerá aquí.
        </p>
        <dl className="balance__rows">
          <div>
            <dt>Comida</dt>
            <dd>{formatEnergy(summary.kcal)} kcal</dd>
          </div>
          <div>
            <dt>Ejercicio</dt>
            <dd>{formatSpent(summary.exerciseKcal)}</dd>
          </div>
        </dl>
      </div>
    );
  }

  const balance = summary.balanceKcal ?? 0;
  const isDeficit = balance < 0;

  // A day still running has spent a whole day's energy but only eaten part of
  // its food, so calling that difference a deficit at breakfast is nonsense.
  // While it runs, what matters is how much is left to eat.
  const heading = summary.isComplete
    ? "Balance estimado del día"
    : summary.remainingKcal !== null
      ? "Te queda por comer"
      : "Lo que va de día";

  const headline = summary.isComplete
    ? isDeficit
      ? `Déficit de ${formatEnergy(Math.abs(balance))} kcal`
      : balance > 0
        ? `Superávit de ${formatEnergy(balance)} kcal`
        : "En equilibrio"
    : summary.remainingKcal !== null
      ? summary.remainingKcal >= 0
        ? `${formatEnergy(summary.remainingKcal)} kcal`
        : `Te has pasado ${formatEnergy(Math.abs(summary.remainingKcal))} kcal`
      : `${formatEnergy(summary.kcal)} kcal comidas`;

  const isGood = summary.isComplete ? isDeficit : (summary.remainingKcal ?? 0) >= 0;

  return (
    <div className={isGood ? "balance balance--deficit" : "balance balance--surplus"}>
      <p className="balance__label">{heading}</p>
      <p className="balance__value">{headline}</p>

      {!summary.isComplete && summary.remainingKcal !== null ? (
        <p className="balance__detail balance__detail--lead">
          Sobre tu objetivo de {formatEnergy(summary.dailyTargetKcal ?? 0)} kcal, más las{" "}
          {formatEnergy(summary.exerciseAboveRestingKcal ?? 0)} que has ganado entrenando.
        </p>
      ) : null}

      {!summary.isComplete && summary.remainingKcal === null ? (
        <p className="balance__detail balance__detail--lead">
          El día no ha terminado, así que todavía no hay un balance que dar: has gastado un día
          entero y comido solo una parte. <Link to="/profile">Fija un objetivo diario</Link> y
          aquí verás cuánto te queda.
        </p>
      ) : null}

      <dl className="balance__rows">
        <div>
          <dt>Comida {summary.isComplete ? "" : "hasta ahora"}</dt>
          <dd>{formatEnergy(summary.kcal)} kcal</dd>
        </div>
        {/* Only the rows that add up carry a sign: a column of signed figures
            ending in a total reads as a sum, so resting cannot sit among them
            when it is already inside daily living. */}
        <div>
          <dt>
            Vida diaria
            <span className="balance__aside">
              incluye {formatEnergy(summary.restingKcal ?? 0)} kcal en reposo
            </span>
          </dt>
          <dd>{formatSpent(summary.livingKcal ?? 0)}</dd>
        </div>
        <div>
          <dt>
            Entrenamiento
            <span className="balance__aside">por encima del reposo</span>
          </dt>
          <dd>{formatSpent(summary.exerciseAboveRestingKcal ?? 0)}</dd>
        </div>
        <div className="balance__rows-total">
          <dt>Gasto total</dt>
          <dd>{formatSpent(summary.totalExpenditureKcal ?? 0)}</dd>
        </div>
      </dl>

      <p className="balance__detail">
        {summary.isComplete
          ? ""
          : "El gasto es el de un día completo, así que compararlo con lo comido hasta ahora no da un déficit todavía. "}
        El entrenamiento se cuenta solo por encima del reposo: durante esos minutos tu cuerpo
        habría gastado algo de todos modos, y la vida diaria ya lo incluye.
        {summary.exerciseKcal > (summary.exerciseAboveRestingKcal ?? 0)
          ? ` La sesión costó ${formatEnergy(summary.exerciseKcal)} kcal en total.`
          : ""}{" "}
        Todo son estimaciones: el reposo sale de una fórmula con tu estatura, peso y edad, y el
        gasto del ejercicio de una tabla. Un déficit calculado así puede equivocarse en varios
        cientos de kilocalorías, y no sustituye el consejo de un médico o
        dietista-nutricionista.
      </p>
    </div>
  );
};
