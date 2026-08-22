export interface WeekReview {
  readonly weekStart: string;
  readonly generatedAt: string;
  /** True once the week is over: a closed week keeps the summary it was given. */
  readonly isFinal: boolean;
  readonly headline: string;
  readonly observations: readonly string[];
  readonly comparison: string | null;
  readonly watchOut: string | null;
}

export interface WeekDay {
  readonly logDate: string;
  readonly kcal: number;
  readonly exerciseKcal: number;
  readonly balanceKcal: number | null;
  readonly sleepHours: number | null;
  readonly hasFood: boolean;
  readonly hasExercise: boolean;
}

export interface Week {
  readonly weekStart: string;
  readonly weekEnd: string;
  readonly isComplete: boolean;
  readonly days: readonly WeekDay[];
  readonly daysWithFood: number;
  readonly daysWithExercise: number;
  readonly daysWithSleep: number;
  readonly totalKcal: number;
  readonly averageKcal: number | null;
  readonly totalExerciseKcal: number;
  readonly averageSleepHours: number | null;
  readonly averageBalanceKcal: number | null;
  readonly weightChangeKg: number | null;
  readonly canReview: boolean;
  readonly hasPreviousReview: boolean;
  readonly review: WeekReview | null;
}
