import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  AUTH_TOKEN_STORAGE_KEY,
  REFRESH_TOKEN_STORAGE_KEY,
  fetchAuthMe,
  getRefreshToken,
  loginUser,
  logoutUser,
  refreshAuthToken,
  registerUser,
  setAuthRefreshHandler,
  setAccessToken,
  setRefreshToken as setApiRefreshToken
} from "../api/catalog";

const AuthContext = createContext(null);

function readStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

function readStoredRefreshToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
}

function persistToken(token) {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  }
}

function persistRefreshToken(token) {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => readStoredToken());
  const [refreshToken, setRefreshTokenState] = useState(() => readStoredRefreshToken());
  const [user, setUser] = useState(null);
  const [isReady, setIsReady] = useState(false);

  const refreshSession = useCallback(async () => {
    const currentRefreshToken = refreshToken || getRefreshToken();
    if (!currentRefreshToken) {
      return false;
    }
    try {
      const refreshed = await refreshAuthToken({ refresh_token: currentRefreshToken });
      persistToken(refreshed.access_token);
      persistRefreshToken(refreshed.refresh_token);
      setToken(refreshed.access_token);
      setRefreshTokenState(refreshed.refresh_token);
      setAccessToken(refreshed.access_token);
      setApiRefreshToken(refreshed.refresh_token);
      setUser(refreshed.user);
      return true;
    } catch {
      persistToken(null);
      persistRefreshToken(null);
      setToken(null);
      setRefreshTokenState(null);
      setAccessToken(null);
      setApiRefreshToken(null);
      setUser(null);
      return false;
    }
  }, [refreshToken]);

  useEffect(() => {
    let isCancelled = false;
    setAccessToken(token);
    setApiRefreshToken(refreshToken);
    if (refreshToken) {
      setAuthRefreshHandler(refreshSession);
    }
    if (!token) {
      setUser(null);
      setIsReady(true);
      return () => {
        isCancelled = true;
      };
    }

    fetchAuthMe()
      .then((payload) => {
        if (!isCancelled) {
          setUser(payload);
        }
      })
      .catch(() => {
        if (isCancelled) {
          return;
        }
        refreshSession().then((isRefreshed) => {
          if (!isCancelled && !isRefreshed) {
            setUser(null);
            setToken(null);
            setRefreshTokenState(null);
            persistToken(null);
            persistRefreshToken(null);
            setAccessToken(null);
            setApiRefreshToken(null);
          }
        });
      })
      .finally(() => {
        if (!isCancelled) {
          setIsReady(true);
        }
      });

    return () => {
      isCancelled = true;
      setAuthRefreshHandler(null);
    };
  }, [refreshSession, refreshToken, token]);

  const value = useMemo(
    () => ({
      isReady,
      isAuthenticated: Boolean(user && token),
      user,
      token,
      refreshToken,
      async login(credentials) {
        const payload = await loginUser(credentials);
        persistToken(payload.access_token);
        persistRefreshToken(payload.refresh_token);
        setToken(payload.access_token);
        setRefreshTokenState(payload.refresh_token);
        setAccessToken(payload.access_token);
        setApiRefreshToken(payload.refresh_token);
        setUser(payload.user);
        setIsReady(true);
        return payload;
      },
      async register(details) {
        const payload = await registerUser(details);
        persistToken(payload.access_token);
        persistRefreshToken(payload.refresh_token);
        setToken(payload.access_token);
        setRefreshTokenState(payload.refresh_token);
        setAccessToken(payload.access_token);
        setApiRefreshToken(payload.refresh_token);
        setUser(payload.user);
        setIsReady(true);
        return payload;
      },
      async logout() {
        try {
          const tokenToRevoke = refreshToken || readStoredRefreshToken();
          if (tokenToRevoke) {
            await logoutUser({ refresh_token: tokenToRevoke });
          }
        } catch {
          // local logout should still complete
        }
        persistToken(null);
        persistRefreshToken(null);
        setToken(null);
        setRefreshTokenState(null);
        setAccessToken(null);
        setApiRefreshToken(null);
        setUser(null);
        setIsReady(true);
      }
    }),
    [isReady, refreshToken, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
