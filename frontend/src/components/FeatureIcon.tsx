type FeatureIconName = "camera" | "edit" | "progress";

interface FeatureIconProps {
  readonly name: FeatureIconName;
}

export const FeatureIcon = ({ name }: FeatureIconProps) => {
  if (name === "camera") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 7.75h3.05l1.2-2h7.5l1.2 2H20a1.75 1.75 0 0 1 1.75 1.75v8.75A1.75 1.75 0 0 1 20 20H4a1.75 1.75 0 0 1-1.75-1.75V9.5A1.75 1.75 0 0 1 4 7.75Z" />
        <circle cx="12" cy="13.5" r="3.25" />
      </svg>
    );
  }

  if (name === "edit") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="m14.75 5.25 4 4M5 19l2.1-5.1L16.75 4.25a1.41 1.41 0 0 1 2 0l1 1a1.41 1.41 0 0 1 0 2L10.1 16.9 5 19Z" />
        <path d="m7.1 13.9 3 3" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 19.5h16" />
      <path d="m5.5 16 4-4 3 2.5 5.75-7" />
      <path d="M15.5 7.5h2.75v2.75" />
    </svg>
  );
};
