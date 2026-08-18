import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import { getAuthErrorMessage } from "../features/auth/authErrors";
import { useAuth } from "../features/auth/useAuth";
import { loginFormSchema } from "../schemas/authSchema";
import type { LoginFormValues } from "../types/auth";

interface LocationState {
  readonly from?: string;
}

export const LoginPage = () => {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      await signIn(values);
      const destination = (location.state as LocationState | null)?.from ?? "/dashboard";
      navigate(destination, { replace: true });
    } catch (error) {
      setSubmissionError(getAuthErrorMessage(error));
    }
  });

  return (
    <section className="auth-card">
      <div className="auth-card__heading">
        <p className="eyebrow">
          <span aria-hidden="true">✦</span>
          Bienvenido de nuevo
        </p>
        <h1>Inicia sesión</h1>
        <p>Accede para seguir registrando tus comidas, tu actividad y tu peso.</p>
      </div>

      <form className="auth-form" onSubmit={(event) => void onSubmit(event)} noValidate>
        {submissionError ? (
          <p className="auth-form__error" role="alert">
            {submissionError}
          </p>
        ) : null}

        <FormField
          label="Correo electrónico"
          type="email"
          autoComplete="email"
          placeholder="tu@correo.com"
          error={errors.email?.message}
          {...register("email")}
        />

        <FormField
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />

        <button className="button button--primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Accediendo…" : "Entrar"}
        </button>
      </form>

      <div className="auth-card__divider">
        <span>o</span>
      </div>

      <GoogleSignInButton label="Continuar con Google" />

    </section>
  );
};
