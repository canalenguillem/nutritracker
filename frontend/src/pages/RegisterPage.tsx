import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { GoogleSignInButton } from "../components/GoogleSignInButton";
import { getAuthErrorMessage } from "../features/auth/authErrors";
import { useAuth } from "../features/auth/useAuth";
import { registerFormSchema } from "../schemas/authSchema";
import type { RegisterFormValues } from "../types/auth";

export const RegisterPage = () => {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerFormSchema),
    defaultValues: { displayName: "", email: "", password: "", passwordConfirmation: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      await signUp(values);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmissionError(getAuthErrorMessage(error));
    }
  });

  return (
    <section className="auth-card">
      <div className="auth-card__heading">
        <p className="eyebrow">
          <span aria-hidden="true">✦</span>
          Empieza hoy
        </p>
        <h1>Crea tu cuenta</h1>
        <p>Registra lo que comes y observa tu evolución con datos que tú confirmas.</p>
      </div>

      <form className="auth-form" onSubmit={(event) => void onSubmit(event)} noValidate>
        {submissionError ? (
          <p className="auth-form__error" role="alert">
            {submissionError}
          </p>
        ) : null}

        <FormField
          label="Nombre"
          type="text"
          autoComplete="name"
          placeholder="Cómo quieres que te llamemos"
          error={errors.displayName?.message}
          {...register("displayName")}
        />

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
          autoComplete="new-password"
          hint="Usa al menos 8 caracteres."
          error={errors.password?.message}
          {...register("password")}
        />

        <FormField
          label="Repite la contraseña"
          type="password"
          autoComplete="new-password"
          error={errors.passwordConfirmation?.message}
          {...register("passwordConfirmation")}
        />

        <button className="button button--primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creando cuenta…" : "Crear cuenta"}
        </button>
      </form>

      <div className="auth-card__divider">
        <span>o</span>
      </div>

      <GoogleSignInButton label="Registrarse con Google" />

      <p className="auth-card__switch">
        ¿Ya tienes cuenta? <Link to="/login">Iniciar sesión</Link>
      </p>
    </section>
  );
};
