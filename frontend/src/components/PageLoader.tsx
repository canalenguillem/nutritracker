interface PageLoaderProps {
  readonly message: string;
}

export const PageLoader = ({ message }: PageLoaderProps) => (
  <div className="page-loader" role="status" aria-live="polite">
    <span className="page-loader__spinner" aria-hidden="true" />
    <p>{message}</p>
  </div>
);
