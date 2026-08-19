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
  const headline = isDeficit
    ? `Déficit de ${formatEnergy(Math.abs(balance))} kcal`
    : balance > 0
      ? `Superávit de ${formatEnergy(balance)} kcal`
      : "En equilibrio";

  return (
    <div className={isDeficit ? "balance balance--deficit" : "balance balance--surplus"}>
      <p className="balance__label">Balance estimado del día</p>
      <p className="balance__value">{headline}</p>

      <dl className="balance__rows">
        <div>
          <dt>Comida</dt>
          <dd>{formatEnergy(summary.kcal)} kcal</dd>
        </div>
        <div>
          <dt>En reposo</dt>
          <dd>{formatSpent(summary.restingKcal ?? 0)}</dd>
        </div>
        <div>
          <dt>Vida diaria, con el reposo dentro</dt>
          <dd>{formatSpent(summary.livingKcal ?? 0)}</dd>
        </div>
        <div>
          <dt>Entrenamiento, por encima del reposo</dt>
          <dd>{formatSpent(summary.exerciseAboveRestingKcal ?? 0)}</dd>
        </div>
        <div className="balance__rows-total">
          <dt>Gasto total</dt>
          <dd>{formatSpent(summary.totalExpenditureKcal ?? 0)}</dd>
        </div>
      </dl>

      <p className="balance__detail">
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
