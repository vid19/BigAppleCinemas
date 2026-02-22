import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  AUTH_TOKEN_STORAGE_KEY,
  fetchAuthMe,
  loginUser,
  registerUser,
  setAccessToken
} from "../api/catalog";

const AuthContext = createContext(null);

function readStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
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

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => readStoredToken());
  const [user, setUser] = useState(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isCancelled = false;
    setAccessToken(token);
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
        if (!isCancelled) {
          setUser(null);
          setToken(null);
          persistToken(null);
          setAccessToken(null);
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsReady(true);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [token]);

  const value = useMemo(
    () => ({
      isReady,
      isAuthenticated: Boolean(user && token),
      user,
      token,
      async login(credentials) {
        const payload = await loginUser(credentials);
        persistToken(payload.access_token);
        setToken(payload.access_token);
        setAccessToken(payload.access_token);
        setUser(payload.user);
        setIsReady(true);
        return payload;
      },
      async register(details) {
        const payload = await registerUser(details);
        persistToken(payload.access_token);
        setToken(payload.access_token);
        setAccessToken(payload.access_token);
        setUser(payload.user);
        setIsReady(true);
        return payload;
      },
      logout() {
        persistToken(null);
        setToken(null);
        setAccessToken(null);
        setUser(null);
        setIsReady(true);
      }
    }),
    [isReady, token, user]
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
