import { applicationConfig } from "../config/environment";

interface BrandProps {
  readonly compact?: boolean;
}

export const Brand = ({ compact = false }: BrandProps) => (
  <a className="brand" href="/" aria-label={`${applicationConfig.name}, inicio`}>
    <span className="brand__mark" aria-hidden="true">
      <svg viewBox="0 0 36 36" role="img">
        <path d="M18 4.25c7.59 0 13.75 6.16 13.75 13.75S25.59 31.75 18 31.75 4.25 25.59 4.25 18 10.41 4.25 18 4.25Z" />
        <path d="M11.25 20.15c4.9-.4 8.47-2.78 10.73-7.15 1.1 4.9-.45 8.72-4.65 11.45" />
        <path d="M12.05 15.3c1.05 3.25 3.27 5.7 6.65 7.35" />
      </svg>
    </span>
    <span className={compact ? "brand__name brand__name--compact" : "brand__name"}>
      {applicationConfig.name}
    </span>
  </a>
);
