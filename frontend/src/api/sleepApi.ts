import { sleptNightResponseSchema } from "../schemas/sleepSchema";
import type { SleepFormValues, SleptNight, SleptNightResponse } from "../types/sleep";
import { httpClient } from "./httpClient";
import { toInstant } from "./mealsApi";

const toNight = (response: SleptNightResponse): SleptNight => ({
  id: response.id,
  startedAt: response.started_at,
  endedAt: response.ended_at,
  quality: response.quality,
  notes: response.notes,
  hours: Number(response.hours),
});

const previousDay = (isoDay: string): string => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);
  const before = new Date(year, month - 1, day - 1);
  const pad = (value: number): string => String(value).padStart(2, "0");

  return `${before.getFullYear()}-${pad(before.getMonth() + 1)}-${pad(before.getDate())}`;
};

export const getNight = async (day: string): Promise<SleptNight | null> => {
  const response = await httpClient.get<unknown>("/sleep", { params: { date: day } });
  if (response.data === null) {
    return null;
  }

  return toNight(sleptNightResponseSchema.parse(response.data));
};

export const createNight = async (values: SleepFormValues): Promise<SleptNight> => {
  // Going to bed after midnight belongs to the same night as the waking day.
  const wentToBedToday = values.bedTime < values.wakeTime;
  const bedDay = wentToBedToday ? values.day : previousDay(values.day);

  const response = await httpClient.post<unknown>("/sleep", {
    started_at: toInstant(bedDay, values.bedTime),
    ended_at: toInstant(values.day, values.wakeTime),
    quality: values.quality === "" ? null : values.quality,
    notes: values.notes.trim() || null,
  });

  return toNight(sleptNightResponseSchema.parse(response.data));
};

export const deleteNight = async (entryId: string): Promise<void> => {
  await httpClient.delete(`/sleep/${entryId}`);
};
