import type { z } from "zod";

import type { readinessResponseSchema } from "../schemas/healthSchema";

export type ReadinessResponse = z.infer<typeof readinessResponseSchema>;

export type Availability = "available" | "unavailable";

export interface ServiceHealth {
  readonly id: string;
  readonly label: string;
  readonly availability: Availability;
}

export interface ReadinessReport {
  readonly availability: Availability;
  readonly appName: string;
  readonly environment: string;
  readonly version: string;
  readonly checkedAt: string;
  readonly services: readonly ServiceHealth[];
}
