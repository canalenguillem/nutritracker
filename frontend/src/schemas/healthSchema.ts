import { z } from "zod";

export const healthStatusSchema = z.enum(["healthy", "unhealthy"]);

export const readinessResponseSchema = z
  .object({
    status: healthStatusSchema,
    app_name: z.string().min(1),
    environment: z.string().min(1),
    version: z.string().min(1),
    timestamp: z.string().datetime({ offset: true }),
    services: z.record(z.string(), healthStatusSchema),
  })
  .passthrough();
