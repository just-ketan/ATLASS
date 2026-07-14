// Simple client-side user session store (localStorage).
// No fake persistence of paper data — only the demo user id.

import { useEffect, useState, useCallback } from "react";
import { api } from "./api";

const USER_KEY = "atlass.user";

export interface AtlassUser {
  id: string;
  email?: string;
  name?: string;
}

export function loadUser(): AtlassUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveUser(user: AtlassUser | null) {
  if (typeof window === "undefined") return;
  if (user) window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  else window.localStorage.removeItem(USER_KEY);
}

export function useAtlassUser() {
  const [user, setUser] = useState<AtlassUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    setUser(loadUser());
    setHydrated(true);
  }, []);

  const signIn = useCallback(async () => {
    try {
      const res = await api.auth.oauth();
      const u = { id: res.user.id, email: res.user.email, name: res.user.name };
      saveUser(u);
      setUser(u);
      setAuthError(null);
      return u;
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to open ATLASS workspace.");
      return null;
    }
  }, []);

  const signOut = useCallback(() => {
    saveUser(null);
    setUser(null);
  }, []);

  return { user, hydrated, authError, signIn, signOut };
}
