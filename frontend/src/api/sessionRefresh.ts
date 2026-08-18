type SessionRefreshHandler = () => Promise<string | null>;

let refreshHandler: SessionRefreshHandler | null = null;
let pendingRefresh: Promise<string | null> | null = null;

export const registerSessionRefreshHandler = (handler: SessionRefreshHandler | null): void => {
  refreshHandler = handler;
};

/**
 * Renew the session at most once at a time. Concurrent callers share the same
 * request because the server rotates the refresh token and treats a replayed
 * one as a leak.
 */
export const refreshSessionOnce = async (): Promise<string | null> => {
  if (refreshHandler === null) {
    return null;
  }

  if (pendingRefresh === null) {
    pendingRefresh = refreshHandler().finally(() => {
      pendingRefresh = null;
    });
  }

  return pendingRefresh;
};
