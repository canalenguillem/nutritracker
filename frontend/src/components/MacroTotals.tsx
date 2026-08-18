import { formatEnergy, formatGrams } from "../features/meals/mealLabels";
import type { Macros } from "../types/meal";

interface MacroTotalsProps {
  readonly macros: Macros;
  readonly compact?: boolean;
}

export const MacroTotals = ({ macros, compact = false }: MacroTotalsProps) => (
  <dl className={compact ? "macros macros--compact" : "macros"}>
    <div className="macros__energy">
      <dt>Calorías</dt>
      <dd>
        {formatEnergy(macros.kcal)} <span>kcal</span>
      </dd>
    </div>
    <div>
      <dt>
        <i className="metric-dot metric-dot--protein" aria-hidden="true" />
        Proteínas
      </dt>
      <dd>{formatGrams(macros.proteinG)} g</dd>
    </div>
    <div>
      <dt>
        <i className="metric-dot metric-dot--carbs" aria-hidden="true" />
        Carbohidratos
      </dt>
      <dd>{formatGrams(macros.carbohydratesG)} g</dd>
    </div>
    <div>
      <dt>
        <i className="metric-dot metric-dot--fat" aria-hidden="true" />
        Grasas
      </dt>
      <dd>{formatGrams(macros.fatG)} g</dd>
    </div>
  </dl>
);
