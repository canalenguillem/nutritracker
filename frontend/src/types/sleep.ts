import type { z } from "zod";

import type { sleepFormSchema, sleptNightResponseSchema } from "../schemas/sleepSchema";

export type SleptNightResponse = z.infer<typeof sleptNightResponseSchema>;

export type SleepFormValues = z.infer<typeof sleepFormSchema>;

export type SleepQuality = NonNullable<SleptNightResponse["quality"]>;

export interface SleptNight {
  readonly id: string;
  readonly startedAt: string;
  readonly endedAt: string;
  readonly quality: SleepQuality | null;
  readonly notes: string | null;
  readonly hours: number;
}
