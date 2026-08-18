import { Link } from "react-router-dom";

import { formatEnergy } from "../features/meals/mealLabels";
import type { DailySummary } from "../types/meal";

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
            <dd>−{formatEnergy(summary.exerciseKcal)} kcal</dd>
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
          <dd>−{formatEnergy(summary.restingKcal ?? 0)} kcal</dd>
        </div>
        <div>
          <dt>Vida diaria, con el reposo dentro</dt>
          <dd>−{formatEnergy(summary.livingKcal ?? 0)} kcal</dd>
        </div>
        <div>
          <dt>Entrenamiento</dt>
          <dd>−{formatEnergy(summary.exerciseKcal)} kcal</dd>
        </div>
        <div className="balance__rows-total">
          <dt>Gasto total</dt>
          <dd>−{formatEnergy(summary.totalExpenditureKcal ?? 0)} kcal</dd>
        </div>
      </dl>

      <p className="balance__detail">
        Todo son estimaciones: el reposo sale de una fórmula con tu estatura, peso y edad, y el
        entrenamiento de una tabla. Un déficit calculado así puede equivocarse en varios cientos
        de kilocalorías, y no sustituye el consejo de un médico o dietista-nutricionista.
      </p>
    </div>
  );
};
