import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { PageLoader } from "../components/PageLoader";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import {
  activityOptions,
  formatKilos,
  goalOptions,
  sexOptions,
} from "../features/weight/weightLabels";
import { useProfile, useUpdateProfile } from "../features/weight/useWeight";
import { profileFormSchema } from "../schemas/weightSchema";
import type { ProfileFormValues } from "../types/weight";

const decimalToField = (value: number | null): string =>
  value === null ? "" : String(value).replace(".", ",");

export const ProfilePage = () => {
  const profile = useProfile();
  const updateProfile = useUpdateProfile();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [wasSaved, setWasSaved] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      heightCm: "",
      targetWeightKg: "",
      birthDate: "",
      biologicalSex: "unspecified",
      activityLevel: "moderate",
      primaryGoal: "maintain_weight",
    },
  });

  // Fill the form once the stored profile arrives.
  useEffect(() => {
    if (!profile.data) {
      return;
    }

    reset({
      heightCm: decimalToField(profile.data.heightCm),
      targetWeightKg: decimalToField(profile.data.targetWeightKg),
      birthDate: profile.data.birthDate ?? "",
      biologicalSex: (profile.data.biologicalSex ??
        "unspecified") as ProfileFormValues["biologicalSex"],
      activityLevel: profile.data.activityLevel as ProfileFormValues["activityLevel"],
      primaryGoal: profile.data.primaryGoal as ProfileFormValues["primaryGoal"],
    });
  }, [profile.data, reset]);

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);
    setWasSaved(false);

    try {
      await updateProfile.mutateAsync(values);
      setWasSaved(true);
    } catch (error) {
      setSubmissionError(getMealErrorMessage(error));
    }
  });

  if (profile.isPending) {
    return <PageLoader message="Cargando tu perfil…" />;
  }

  return (
    <section className="add-meal">
      <div className="container add-meal__content">
        <div className="add-meal__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            Perfil
          </p>
          <h1>Tus datos</h1>
          <p>
            Con la estatura y el peso podemos calcular tu IMC, y con el resto llegaremos a estimar
            lo que gastas en reposo. Todo es opcional.
          </p>
        </div>

        {profile.data?.currentWeightKg !== null && profile.data ? (
          <p className="draft-notice" role="status">
            Tu peso actual es {formatKilos(profile.data.currentWeightKg)}, tomado de tu último
            registro.
            <Link to="/weight">Registrar peso</Link>
          </p>
        ) : null}

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          {wasSaved ? (
            <p className="profile-saved" role="status">
              Guardado.
            </p>
          ) : null}

          <div className="add-meal__when">
            <FormField
              label="Estatura (cm)"
              type="text"
              inputMode="decimal"
              placeholder="178"
              error={errors.heightCm?.message}
              {...register("heightCm")}
            />
            <FormField
              label="Peso objetivo (kg)"
              type="text"
              inputMode="decimal"
              placeholder="75"
              error={errors.targetWeightKg?.message}
              {...register("targetWeightKg")}
            />
            <FormField
              label="Fecha de nacimiento"
              type="date"
              error={errors.birthDate?.message}
              {...register("birthDate")}
            />
          </div>

          <div className="add-meal__when">
            <div className="form-field">
              <label className="form-field__label" htmlFor="profile-sex">
                Sexo para la estimación metabólica
              </label>
              <select
                className="form-field__input"
                id="profile-sex"
                {...register("biologicalSex")}
              >
                {sexOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-field__label" htmlFor="profile-activity">
                Cómo es tu día, sin contar entrenamientos
              </label>
              <select
                className="form-field__input"
                id="profile-activity"
                {...register("activityLevel")}
              >
                {activityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-field__label" htmlFor="profile-goal">
                Objetivo principal
              </label>
              <select className="form-field__input" id="profile-goal" {...register("primaryGoal")}>
                {goalOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <p className="dashboard__disclaimer">
            La actividad diaria no incluye tus entrenamientos: esos los registras uno a uno y se
            suman aparte, para no contarlos dos veces. Estos datos solo se usan para estimar, y
            nada de lo que calculemos sustituye el consejo de un médico o
            dietista-nutricionista.
          </p>

          <div className="add-meal__actions">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando…" : "Guardar perfil"}
            </button>
            <Link className="text-link" to="/dashboard">
              Volver al panel
            </Link>
          </div>
        </form>
      </div>
    </section>
  );
};
