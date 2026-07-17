import { FeatureIcon } from "../components/FeatureIcon";
import { HealthStatusCard } from "../components/HealthStatusCard";

const features = [
  {
    icon: "camera" as const,
    title: "Fotografía y revisa",
    description:
      "Recibe una estimación inicial de tus comidas y revisa cada dato antes de guardarlo.",
  },
  {
    icon: "edit" as const,
    title: "Tú tienes el control",
    description:
      "Ajusta cantidades, ingredientes y valores. Ninguna estimación se confirma automáticamente.",
  },
  {
    icon: "progress" as const,
    title: "Observa tu progreso",
    description:
      "Reúne alimentación, ejercicio y peso para comprender mejor tu evolución diaria.",
  },
] as const;

export const HomePage = () => (
  <>
    <section className="hero">
      <div className="hero__glow hero__glow--one" aria-hidden="true" />
      <div className="hero__glow hero__glow--two" aria-hidden="true" />
      <div className="container hero__content">
        <div className="hero__copy">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            Tu día, más fácil de entender
          </p>
          <h1>
            Convierte tus hábitos en <em>progreso visible.</em>
          </h1>
          <p className="hero__description">
            Registra lo que comes, tu actividad y tu peso en un solo lugar. Obtén estimaciones
            útiles, revisa los detalles y decide siempre tú.
          </p>
          <div className="hero__actions">
            <a className="button button--primary" href="#estado">
              Comprobar disponibilidad
              <svg viewBox="0 0 20 20" aria-hidden="true">
                <path d="m7 4 6 6-6 6" />
              </svg>
            </a>
            <a className="text-link" href="#como-funciona">
              Descubrir cómo funciona
            </a>
          </div>
          <p className="hero__trust">
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="M10 2.5 16 5v4.25c0 3.65-2.35 6.45-6 8.25-3.65-1.8-6-4.6-6-8.25V5l6-2.5Z" />
              <path d="m7.25 10 1.8 1.8 3.8-4" />
            </svg>
            Tus estimaciones nunca se guardan sin tu confirmación.
          </p>
        </div>

        <div className="hero-preview" aria-label="Vista previa del resumen diario">
          <div className="hero-preview__header">
            <div>
              <span>Resumen de hoy</span>
              <strong>Tu progreso diario</strong>
            </div>
            <span className="hero-preview__date">Hoy</span>
          </div>
          <div className="hero-preview__ring" aria-hidden="true">
            <div className="hero-preview__ring-center">
              <strong>—</strong>
              <span>kcal registradas</span>
            </div>
          </div>
          <div className="hero-preview__message">
            <span className="hero-preview__message-icon" aria-hidden="true">✦</span>
            <div>
              <strong>Empieza con tu primer registro</strong>
              <p>Tus datos diarios aparecerán aquí.</p>
            </div>
          </div>
          <div className="hero-preview__metrics" aria-hidden="true">
            <span><i className="metric-dot metric-dot--protein" />Proteínas</span>
            <span><i className="metric-dot metric-dot--carbs" />Carbohidratos</span>
            <span><i className="metric-dot metric-dot--fat" />Grasas</span>
          </div>
        </div>
      </div>
    </section>

    <section className="features-section" id="como-funciona">
      <div className="container">
        <div className="section-heading">
          <p className="eyebrow">Pensado para el día a día</p>
          <h2>Menos fricción. Más contexto.</h2>
          <p>
            Una experiencia sencilla para registrar, revisar y comprender tus hábitos sin
            presentar estimaciones como certezas.
          </p>
        </div>
        <div className="feature-grid">
          {features.map((feature, index) => (
            <article className="feature-card" key={feature.title}>
              <div className="feature-card__topline">
                <span className="feature-card__icon">
                  <FeatureIcon name={feature.icon} />
                </span>
                <span className="feature-card__number">0{index + 1}</span>
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>

    <section className="status-section" id="estado">
      <div className="container status-section__content">
        <div className="status-section__copy">
          <p className="eyebrow">Conexión en tiempo real</p>
          <h2>Comprueba que todo está preparado.</h2>
          <p>
            Esta comprobación consulta directamente el servicio de NutriTrack y se actualiza de
            forma automática.
          </p>
        </div>
        <HealthStatusCard />
      </div>
    </section>

    <section className="disclaimer-section" aria-labelledby="disclaimer-title">
      <div className="container disclaimer">
        <span className="disclaimer__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 10.5v6M12 7.5v.25" />
          </svg>
        </span>
        <div>
          <h2 id="disclaimer-title">Información importante</h2>
          <p>
            Los valores nutricionales, el gasto calórico y el balance calórico son estimaciones.
            Esta aplicación no sustituye el consejo de un médico o dietista-nutricionista
            colegiado.
          </p>
        </div>
      </div>
    </section>
  </>
);
