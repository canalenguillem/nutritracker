import { z } from "zod";

const MINIMUM_PASSWORD_LENGTH = 8;
const MAXIMUM_PASSWORD_LENGTH = 128;
const MAXIMUM_DISPLAY_NAME_LENGTH = 120;

export const userRoleSchema = z.enum(["user", "admin"]);

export const userResponseSchema = z
  .object({
    id: z.string().uuid(),
    email: z.string().email(),
    display_name: z.string().min(1),
    role: userRoleSchema,
    avatar_url: z.string().nullable().default(null),
  })
  .passthrough();

export const sessionResponseSchema = z
  .object({
    access_token: z.string().min(1),
    token_type: z.string().min(1),
    expires_in: z.number().int().positive(),
    user: userResponseSchema,
  })
  .passthrough();

export const loginFormSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Introduce tu correo electrónico.")
    .email("Introduce un correo electrónico válido."),
  password: z.string().min(1, "Introduce tu contraseña."),
});

export const registerFormSchema = z
  .object({
    displayName: z
      .string()
      .trim()
      .min(1, "Introduce tu nombre.")
      .max(MAXIMUM_DISPLAY_NAME_LENGTH, "El nombre es demasiado largo."),
    email: z
      .string()
      .trim()
      .min(1, "Introduce tu correo electrónico.")
      .email("Introduce un correo electrónico válido."),
    password: z
      .string()
      .min(MINIMUM_PASSWORD_LENGTH, "La contraseña debe tener al menos 8 caracteres.")
      .max(MAXIMUM_PASSWORD_LENGTH, "La contraseña es demasiado larga."),
    passwordConfirmation: z.string().min(1, "Repite la contraseña."),
  })
  .refine((values) => values.password === values.passwordConfirmation, {
    message: "Las contraseñas no coinciden.",
    path: ["passwordConfirmation"],
  });
