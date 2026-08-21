import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useFieldArray, useForm } from "react-hook-form";

import { EstimatePanel } from "../components/EstimatePanel";
import { FormField } from "../components/FormField";
import { PageLoader } from "../components/PageLoader";
import { RecentMeals } from "../components/RecentMeals";
import { mealTypeOptions } from "../features/meals/mealLabels";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import {
  clearDraft,
  dataUrlToFile,
  isDraftWorthKeeping,
  loadDraft,
  readPhotoAsDataUrl,
  saveDraft,
} from "../features/meals/mealDraft";
import { formatFileSize, preparePhoto } from "../features/meals/photoPreparation";
import {
  useCreateMeal,
  useDescribeMeal,
  useMeal,
  useUpdateMeal,
} from "../features/meals/useMeals";
import { mealFormSchema } from "../schemas/mealSchema";
import type { FoodEstimate, Meal, MealFormValues, MealItemFormValues } from "../types/meal";

const EMPTY_ITEM: MealItemFormValues = {
  name: "",
  quantity: "",
  unit: "g",
  kcal: "",
  protein_g: "",
  fat_g: "",
  carbohydrates_g: "",
};

/** The form accepts the comma, so write the estimate the way it reads in Spanish. */
const toFieldValue = (value: number): string => String(value).replace(".", ",");

const toFormItems = (estimate: FoodEstimate): MealItemFormValues[] =>
  estimate.items.map((item) => ({
    name: item.name,
    quantity: toFieldValue(item.quantity),
    unit: item.unit,
    kcal: toFieldValue(item.kcal),
    protein_g: toFieldValue(item.proteinG),
    fat_g: toFieldValue(item.fatG),
    carbohydrates_g: toFieldValue(item.carbohydratesG),
  }));

const pad = (value: number): string => String(value).padStart(2, "0");

const todayValue = (now: Date): string =>
  `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

const timeValue = (now: Date): string => `${pad(now.getHours())}:${pad(now.getMinutes())}`;

export const AddMealPage = () => {
  const navigate = useNavigate();
  const { mealId } = useParams();
  const isEditing = Boolean(mealId);
  const existingMeal = useMeal(mealId);
  const createMeal = useCreateMeal();
  const updateMeal = useUpdateMeal();
  const describeMeal = useDescribeMeal();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [estimateError, setEstimateError] = useState<string | null>(null);
  const [estimates, setEstimates] = useState<FoodEstimate[]>([]);
  const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [addedNotice, setAddedNotice] = useState<string | null>(null);
  const itemsRef = useRef<HTMLDivElement>(null);
  const [isPreparingPhoto, setIsPreparingPhoto] = useState(false);
  const cameraInput = useRef<HTMLInputElement>(null);
  const galleryInput = useRef<HTMLInputElement>(null);
  const [restoredDraft] = useState(() => (mealId ? null : loadDraft()));
  const [wasRestored, setWasRestored] = useState(false);
  const photoDataUrl = useRef<string | null>(null);
  const [now] = useState(() => new Date());

  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<MealFormValues>({
    resolver: zodResolver(mealFormSchema),
    defaultValues: restoredDraft?.values ?? {
      mealType: "lunch",
      day: todayValue(now),
      time: timeValue(now),
      notes: "",
      items: [EMPTY_ITEM],
    },
  });

  const { fields, append, remove, replace } = useFieldArray({ control, name: "items" });

  /** Add to what is already there, dropping the blank row the form starts with. */
  const addItems = (incoming: MealItemFormValues[], label: string) => {
    const filled = getValues("items").filter(
      (item) => item.name.trim().length > 0 || item.kcal.trim().length > 0,
    );
    replace([...filled, ...incoming]);
    setAddedNotice(label);
  };

  // The foods land below the fold, so without this nothing appears to happen
  // and the same dish gets added again and again.
  useEffect(() => {
    if (addedNotice === null) {
      return;
    }

    const added = itemsRef.current?.querySelector(".meal-item-fields:last-of-type");
    const prefersStill = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    added?.scrollIntoView({ behavior: prefersStill ? "auto" : "smooth", block: "center" });
  }, [addedNotice, fields.length]);

  useEffect(() => {
    const meal = existingMeal.data;
    if (!meal) {
      return;
    }

    const eatenAt = new Date(meal.eatenAt);
    const pad2 = (value: number): string => String(value).padStart(2, "0");

    reset({
      mealType: meal.mealType,
      day: `${eatenAt.getFullYear()}-${pad2(eatenAt.getMonth() + 1)}-${pad2(eatenAt.getDate())}`,
      time: `${pad2(eatenAt.getHours())}:${pad2(eatenAt.getMinutes())}`,
      notes: meal.notes ?? "",
      items: meal.items.map((item) => ({
        name: item.name,
        quantity: toFieldValue(item.quantity),
        unit: item.unit,
        kcal: toFieldValue(item.kcal),
        protein_g: toFieldValue(item.proteinG),
        fat_g: toFieldValue(item.fatG),
        carbohydrates_g: toFieldValue(item.carbohydratesG),
      })),
    });
  }, [existingMeal.data, reset]);

  // Pick the draft back up after the browser rebuilt the page.
  useEffect(() => {
    if (!restoredDraft) {
      return;
    }

    setDescription(restoredDraft.description);
    if (restoredDraft.photoDataUrl) {
      photoDataUrl.current = restoredDraft.photoDataUrl;
      setPhoto(dataUrlToFile(restoredDraft.photoDataUrl));
    }
    setWasRestored(true);
  }, [restoredDraft]);

  // Saving on every render would rewrite the stored photo each time, so this
  // only runs when something actually changed.
  const persistDraft = useCallback(() => {
    const values = getValues();
    if (!isDraftWorthKeeping(values, description)) {
      // An emptied form has to remove the stored copy, or it comes back.
      clearDraft();
      return;
    }

    saveDraft({ values, description, photoDataUrl: photoDataUrl.current });
  }, [description, getValues]);

  useEffect(() => {
    if (isEditing) {
      return;
    }

    const subscription = watch(() => persistDraft());

    return () => subscription.unsubscribe();
  }, [isEditing, persistDraft, watch]);

  useEffect(() => {
    if (isEditing) {
      return;
    }

    persistDraft();
  }, [isEditing, persistDraft, photo]);

  // The preview holds an object URL, which has to be handed back.
  useEffect(() => {
    if (!photo) {
      setPhotoPreview(null);
      return;
    }

    const url = URL.createObjectURL(photo);
    setPhotoPreview(url);

    return () => URL.revokeObjectURL(url);
  }, [photo]);

  const onPickPhoto = async (file: File | undefined) => {
    if (!file) {
      return;
    }

    setIsPreparingPhoto(true);
    try {
      const prepared = await preparePhoto(file);
      photoDataUrl.current = await readPhotoAsDataUrl(prepared);
      setPhoto(prepared);
    } finally {
      setIsPreparingPhoto(false);
    }
  };

  const startAgain = () => {
    clearDraft();
    setWasRestored(false);
    setDescription("");
    setEstimates([]);
    clearPhoto();
    reset({
      mealType: "lunch",
      day: todayValue(now),
      time: timeValue(now),
      notes: "",
      items: [EMPTY_ITEM],
    });
  };

  const clearPhoto = () => {
    setPhoto(null);
    photoDataUrl.current = null;
    if (cameraInput.current) {
      cameraInput.current.value = "";
    }
    if (galleryInput.current) {
      galleryInput.current.value = "";
    }
  };

  const onEstimate = async () => {
    setEstimateError(null);

    try {
      const result = await describeMeal.mutateAsync({ description, photo });
      setEstimates((current) => [...current, result]);
      addItems(toFormItems(result), result.summary || "Estimación añadida");
      // Clear the box so the next food can be described straight away.
      setDescription("");
      clearPhoto();
    } catch (error) {
      setEstimateError(getMealErrorMessage(error));
    }
  };

  const onPickRecent = (meal: Meal) => {
    addItems(
      meal.items.map((item) => ({
        name: item.name,
        quantity: toFieldValue(item.quantity),
        unit: item.unit,
        kcal: toFieldValue(item.kcal),
        protein_g: toFieldValue(item.proteinG),
        fat_g: toFieldValue(item.fatG),
        carbohydrates_g: toFieldValue(item.carbohydratesG),
      })),
      meal.items.map((item) => item.name).join(" + "),
    );
  };

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      if (mealId) {
        await updateMeal.mutateAsync({ mealId, values });
      } else {
        await createMeal.mutateAsync(values);
        clearDraft();
      }
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmissionError(getMealErrorMessage(error));
    }
  });

  if (isEditing && existingMeal.isPending) {
    return <PageLoader message="Cargando la comida…" />;
  }

  return (
    <section className="add-meal">
      <div className="container add-meal__content">
        {wasRestored ? (
          <p className="draft-notice" role="status">
            Hemos recuperado lo que estabas escribiendo. El móvil a veces cierra la página
            mientras haces la foto.
            <button type="button" onClick={startAgain}>
              Empezar de nuevo
            </button>
          </p>
        ) : null}

        <div className="add-meal__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            {isEditing ? "Corregir" : "Registro manual"}
          </p>
          <h1>{isEditing ? "Edita la comida" : "Añade una comida"}</h1>
          <p>
            Escribe lo que has comido y sus valores. Nada se estima por ti: los totales salen de
            lo que introduzcas.
          </p>
        </div>

        {isEditing ? null : (
          <section className="describe" aria-label="Describir la comida">
            <label className="form-field__label" htmlFor="meal-description">
              ¿No sabes los valores? Descríbelo o hazle una foto
            </label>
            <p className="describe__hint">
              Escribe «un café con nata», o fotografía el plato o su tabla nutricional. Puedes
              hacer las dos cosas: lo que cuentes ayuda a leer la foto.
            </p>
            <div className="describe__row">
              <input
                className="form-field__input"
                id="meal-description"
                type="text"
                value={description}
                placeholder="Media tarrina de mascarpone"
                onChange={(event) => setDescription(event.target.value)}
                disabled={describeMeal.isPending}
              />
              <button
                className="button button--secondary"
                type="button"
                onClick={() => void onEstimate()}
                disabled={
                describeMeal.isPending || (description.trim().length === 0 && photo === null)
              }
              >
                {describeMeal.isPending ? "Estimando…" : "Estimar valores"}
              </button>
            </div>

            <div className="describe__photo">
              <label className="describe__photo-pick" htmlFor="meal-photo-camera">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 8h3l1.5-2h7L17 8h3v11H4z" />
                  <circle cx="12" cy="13" r="3.5" />
                </svg>
                Hacer una foto
              </label>
              <input
                className="describe__photo-input"
                id="meal-photo-camera"
                ref={cameraInput}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(event) => void onPickPhoto(event.target.files?.[0])}
                disabled={describeMeal.isPending || isPreparingPhoto}
              />

              <label className="describe__photo-pick" htmlFor="meal-photo-file">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M5 19V5h9l5 5v9z" />
                  <path d="M14 5v5h5" />
                </svg>
                Elegir una imagen
              </label>
              <input
                className="describe__photo-input"
                id="meal-photo-file"
                ref={galleryInput}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => void onPickPhoto(event.target.files?.[0])}
                disabled={describeMeal.isPending || isPreparingPhoto}
              />

              {isPreparingPhoto ? (
                <span className="describe__photo-hint">Preparando la foto…</span>
              ) : null}

              {!photo && !isPreparingPhoto ? (
                <span className="describe__photo-hint">
                  Con la tabla nutricional el cálculo es mucho más fiable.
                </span>
              ) : null}
            </div>

            {photo ? (
              <div className="photo-preview">
                {photoPreview ? (
                  <img src={photoPreview} alt="La foto que vas a enviar" />
                ) : null}
                <div className="photo-preview__detail">
                  <p className="photo-preview__name">Foto lista para enviar</p>
                  <p className="photo-preview__size">{formatFileSize(photo.size)}</p>
                  <p className="photo-preview__check">
                    Comprueba que la tabla se lee antes de estimar.
                  </p>
                  <button className="photo-preview__remove" type="button" onClick={clearPhoto}>
                    Quitar la foto
                  </button>
                </div>
              </div>
            ) : null}

            <p className="describe__notice">
              La foto se envía a OpenAI para leerla y no se guarda en ningún sitio.
            </p>
            {estimateError ? (
              <p className="auth-form__error" role="alert">
                {estimateError}
              </p>
            ) : null}
          </section>
        )}

        {estimates.map((entry, index) => (
          <EstimatePanel key={`${entry.summary}-${index}`} estimate={entry} />
        ))}

        {isEditing ? null : (
          <RecentMeals
            onPick={onPickRecent}
            disabled={describeMeal.isPending}
            addedNotice={addedNotice}
          />
        )}

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          <div className="add-meal__when">
            <div className="form-field">
              <label className="form-field__label" htmlFor="meal-type">
                Tipo de comida
              </label>
              <select className="form-field__input" id="meal-type" {...register("mealType")}>
                {mealTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <FormField label="Día" type="date" error={errors.day?.message} {...register("day")} />
            <FormField
              label="Hora"
              type="time"
              error={errors.time?.message}
              {...register("time")}
            />
          </div>

          <div className="add-meal__items" ref={itemsRef}>
            <div className="add-meal__items-head">
              <h2>Alimentos ({fields.length})</h2>
              <div className="add-meal__items-actions">
                <button
                  className="button button--secondary button--small"
                  type="button"
                  onClick={() => append(EMPTY_ITEM)}
                >
                  Añadir alimento
                </button>
                {fields.length > 1 ? (
                  <button
                    className="add-meal__clear"
                    type="button"
                    onClick={() => {
                      replace([EMPTY_ITEM]);
                      setEstimates([]);
                      setAddedNotice(null);
                    }}
                  >
                    Vaciar la lista
                  </button>
                ) : null}
              </div>
            </div>

            {fields.map((field, index) => (
              <fieldset className="meal-item-fields" key={field.id}>
                <legend>Alimento {index + 1}</legend>

                <div className="meal-item-fields__identity">
                  <FormField
                    label="Alimento"
                    type="text"
                    placeholder="Arroz integral"
                    error={errors.items?.[index]?.name?.message}
                    {...register(`items.${index}.name`)}
                  />
                  <FormField
                    label="Cantidad"
                    type="text"
                    inputMode="decimal"
                    placeholder="150"
                    error={errors.items?.[index]?.quantity?.message}
                    {...register(`items.${index}.quantity`)}
                  />
                  <FormField
                    label="Unidad"
                    type="text"
                    placeholder="g"
                    error={errors.items?.[index]?.unit?.message}
                    {...register(`items.${index}.unit`)}
                  />
                </div>

                <div className="meal-item-fields__macros">
                  <FormField
                    label="Calorías (kcal)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.kcal?.message}
                    {...register(`items.${index}.kcal`)}
                  />
                  <FormField
                    label="Proteínas (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.protein_g?.message}
                    {...register(`items.${index}.protein_g`)}
                  />
                  <FormField
                    label="Carbohidratos (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.carbohydrates_g?.message}
                    {...register(`items.${index}.carbohydrates_g`)}
                  />
                  <FormField
                    label="Grasas (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.fat_g?.message}
                    {...register(`items.${index}.fat_g`)}
                  />
                </div>

                {fields.length > 1 ? (
                  <button
                    className="meal-item-fields__remove"
                    type="button"
                    onClick={() => remove(index)}
                  >
                    Quitar este alimento
                  </button>
                ) : null}
              </fieldset>
            ))}
          </div>

          <div className="form-field">
            <label className="form-field__label" htmlFor="meal-notes">
              Notas
            </label>
            <textarea
              className="form-field__input form-field__input--area"
              id="meal-notes"
              rows={3}
              placeholder="Con aceite de oliva, poca sal…"
              {...register("notes")}
            />
            {errors.notes ? (
              <p className="form-field__error" role="alert">
                {errors.notes.message}
              </p>
            ) : null}
          </div>

          <div className="add-meal__actions">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando…" : isEditing ? "Guardar cambios" : "Guardar comida"}
            </button>
            <Link className="text-link" to="/dashboard">
              Cancelar
            </Link>
          </div>
        </form>
      </div>
    </section>
  );
};
