import { useQuery } from "@tanstack/react-query";

import { getReadiness } from "../../api/healthApi";

const READINESS_REFRESH_INTERVAL_MS = 30_000;

export const readinessQueryKey = ["health", "readiness"] as const;

export const useReadiness = () =>
  useQuery({
    queryKey: readinessQueryKey,
    queryFn: getReadiness,
    retry: 1,
    refetchInterval: READINESS_REFRESH_INTERVAL_MS,
    refetchIntervalInBackground: false,
  });
