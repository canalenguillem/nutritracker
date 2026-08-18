import { forwardRef, useId, type InputHTMLAttributes } from "react";

interface FormFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  readonly label: string;
  readonly error?: string;
  readonly hint?: string;
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, error, hint, ...inputProps }, ref) => {
    const fieldId = useId();
    const hintId = `${fieldId}-hint`;
    const errorId = `${fieldId}-error`;
    const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(" ");

    return (
      <div className="form-field">
        <label className="form-field__label" htmlFor={fieldId}>
          {label}
        </label>
        <input
          {...inputProps}
          className={error ? "form-field__input form-field__input--invalid" : "form-field__input"}
          id={fieldId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy || undefined}
        />
        {hint ? (
          <p className="form-field__hint" id={hintId}>
            {hint}
          </p>
        ) : null}
        {error ? (
          <p className="form-field__error" id={errorId} role="alert">
            {error}
          </p>
        ) : null}
      </div>
    );
  },
);

FormField.displayName = "FormField";
