import { formatEnergy, formatQuantity } from "../features/meals/mealLabels";
import type { FoodEstimate } from "../types/meal";

interface EstimatePanelProps {
  readonly estimate: FoodEstimate;
}

const formatConfidence = (confidence: number | null): string | null =>
  confidence === null ? null : `${Math.round(confidence * 100)} % de confianza`;

export const EstimatePanel = ({ estimate }: EstimatePanelProps) => (
  <section className="estimate" aria-label="Estimación de la comida">
    <header className="estimate__header">
      <div>
        <p className="estimate__eyebrow">
          Estimación
          {estimate.fromCache ? <span className="estimate__reused">ya la tenías</span> : null}
        </p>
        <h2>{estimate.summary || "Comida estimada"}</h2>
      </div>
      <div className="estimate__energy">
        <strong>{formatEnergy(estimate.totalKcal)}</strong>
        <span>kcal</span>
      </div>
    </header>

    <p className="estimate__lede">
      {estimate.fromCache
        ? "Ya habías descrito esta comida, así que reutilizamos aquella estimación sin volver a consultar a la IA. "
        : ""}
      Hemos añadido estos alimentos al formulario. Puedes seguir describiendo más cosas y se
      irán sumando. Corrige lo que no encaje antes de guardar: nada se guarda hasta que lo
      confirmes.
      {formatConfidence(estimate.confidence)
        ? ` Confianza general: ${formatConfidence(estimate.confidence)}.`
        : ""}
    </p>

    <ul className="estimate__items">
      {estimate.items.map((item) => (
        <li key={`${item.name}-${item.quantity}`}>
          <div className="estimate__item-head">
            <span className="estimate__item-name">{item.name}</span>
            <span className="estimate__item-quantity">
              {formatQuantity(item.quantity, item.unit)} · {formatEnergy(item.kcal)} kcal
            </span>
          </div>
          {formatConfidence(item.confidence) ? (
            <span className="estimate__confidence">{formatConfidence(item.confidence)}</span>
          ) : null}
          {item.macrosDisagree ? (
            <p className="estimate__mismatch">
              Sus macros suman {formatEnergy(item.kcalFromMacros)} kcal, no{" "}
              {formatEnergy(item.kcal)}. Una de las dos cifras está mal; revísala antes de
              guardar.
            </p>
          ) : null}
          {item.assumptions.length > 0 ? (
            <ul className="estimate__assumptions">
              {item.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          ) : null}
        </li>
      ))}
    </ul>

    {estimate.questions.length > 0 ? (
      <div className="estimate__questions">
        <h3>Para afinarlo</h3>
        <ul>
          {estimate.questions.map((question) => (
            <li key={question.key}>
              <p>{question.question}</p>
              {question.options.length > 0 ? (
                <p className="estimate__options">{question.options.join(" · ")}</p>
              ) : null}
            </li>
          ))}
        </ul>
        <p className="estimate__questions-note">
          Si alguna respuesta cambia los valores, ajústalos abajo o vuelve a describir la comida
          con ese detalle.
        </p>
      </div>
    ) : null}

    <p className="estimate__warning">
      {estimate.warning ||
        "Los valores son una estimación y no sustituyen el consejo de un profesional sanitario."}
    </p>
  </section>
);
