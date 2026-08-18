import type { MealFormValues } from "../../types/meal";

const DRAFT_KEY = "nutritrack.meal-draft.v1";
const DRAFT_LIFETIME_MS = 2 * 60 * 60 * 1000;
/** Beyond this a data URL risks the storage quota, so the photo is not kept. */
const MAX_STORED_PHOTO_BYTES = 1_500_000;

export interface MealDraft {
  readonly values: MealFormValues;
  readonly description: string;
  readonly photoDataUrl: string | null;
  readonly savedAt: number;
}

export const readPhotoAsDataUrl = (photo: File): Promise<string | null> =>
  new Promise((resolve) => {
    if (photo.size > MAX_STORED_PHOTO_BYTES) {
      resolve(null);
      return;
    }

    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : null);
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(photo);
  });

export const dataUrlToFile = (dataUrl: string): File | null => {
  const match = /^data:([^;]+);base64,(.*)$/.exec(dataUrl);
  if (!match) {
    return null;
  }

  const [, mediaType = "image/jpeg", encoded = ""] = match;
  try {
    const binary = atob(encoded);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return new File([bytes], "etiqueta.jpg", { type: mediaType });
  } catch {
    return null;
  }
};

/**
 * Keep what is being typed outside the page.
 *
 * A phone browser often discards the page while the camera is open and rebuilds
 * it on return, which would otherwise throw away the description and the photo.
 */
export const saveDraft = (draft: Omit<MealDraft, "savedAt">): void => {
  try {
    window.localStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({ ...draft, savedAt: Date.now() } satisfies MealDraft),
    );
  } catch {
    // A full or unavailable storage must never break the form.
  }
};

export const loadDraft = (): MealDraft | null => {
  try {
    const stored = window.localStorage.getItem(DRAFT_KEY);
    if (!stored) {
      return null;
    }

    const draft = JSON.parse(stored) as MealDraft;
    if (!draft.values || Date.now() - draft.savedAt > DRAFT_LIFETIME_MS) {
      clearDraft();
      return null;
    }

    return draft;
  } catch {
    return null;
  }
};

export const clearDraft = (): void => {
  try {
    window.localStorage.removeItem(DRAFT_KEY);
  } catch {
    // Nothing to do: the draft is a convenience, not a record.
  }
};

export const isDraftWorthKeeping = (values: MealFormValues, description: string): boolean =>
  description.trim().length > 0 ||
  values.notes.trim().length > 0 ||
  values.items.some((item) => item.name.trim().length > 0 || item.kcal.trim().length > 0);
