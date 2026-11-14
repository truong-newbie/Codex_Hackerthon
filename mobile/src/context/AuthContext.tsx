import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserInfo } from '../api/types';
import { api } from '../api/client';
import { DEFAULT_API_URL } from '../constants/config';
import { storage } from '../utils/storage';

const STORAGE_KEYS = {
  SERVER_URL: '@shiftlens_server_url',
  TOKEN: '@shiftlens_token',
  USER: '@shiftlens_user',
  ACTIVE_SESSION_ID: '@shiftlens_active_session_id',
};

interface AuthContextType {
  user: UserInfo | null;
  token: string | null;
  serverUrl: string;
  setServerUrl: (url: string) => void;
  login: (usernameOrEmail: string, pass: string) => Promise<void>;
  logout: () => void;
  aiMode: string;
  setAiMode: (mode: string) => void;
  isHydrating: boolean;
  activeSessionId: string | null;
  setActiveSessionId: (sessionId: string | null) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [serverUrl, setServerUrlState] = useState<string>(DEFAULT_API_URL || 'http://10.0.2.2:8000');
  const [aiMode, setAiMode] = useState<string>('stub');
  const [isHydrating, setIsHydrating] = useState<boolean>(true);
  const [activeSessionId, setActiveSessionIdState] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const savedUrl = await storage.getItem(STORAGE_KEYS.SERVER_URL);
        if (savedUrl) {
          setServerUrlState(savedUrl);
          api.setBaseUrl(savedUrl);
        }
        const savedToken = await storage.getItem(STORAGE_KEYS.TOKEN);
        const savedUser = await storage.getItem(STORAGE_KEYS.USER);
        const savedSessionId = await storage.getItem(STORAGE_KEYS.ACTIVE_SESSION_ID);
        if (savedToken && savedUser) {
          api.setToken(savedToken);
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        }
        if (savedSessionId) {
          setActiveSessionIdState(savedSessionId);
        }
        const health = await api.checkHealth().catch(() => null);
        if (health) {
          setAiMode(health.ai_mode);
        }
      } catch (_) {
      } finally {
        setIsHydrating(false);
      }
    })();
  }, []);

  const setServerUrl = (url: string) => {
    setServerUrlState(url);
    api.setBaseUrl(url);
    storage.setItem(STORAGE_KEYS.SERVER_URL, url);
  };

  const setActiveSessionId = async (sessionId: string | null) => {
    setActiveSessionIdState(sessionId);
    if (sessionId) {
      await storage.setItem(STORAGE_KEYS.ACTIVE_SESSION_ID, sessionId);
    } else {
      await storage.removeItem(STORAGE_KEYS.ACTIVE_SESSION_ID);
    }
  };

  const login = async (usernameOrEmail: string, pass: string) => {
    const res = await api.login(usernameOrEmail, pass);
    setToken(res.access_token);
    setUser(res.user);
    api.setToken(res.access_token);
    await storage.setItem(STORAGE_KEYS.TOKEN, res.access_token);
    await storage.setItem(STORAGE_KEYS.USER, JSON.stringify(res.user));
    
    try {
      const health = await api.checkHealth();
      setAiMode(health.ai_mode);
    } catch (_) {}
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setActiveSessionIdState(null);
    api.setToken(null);
    storage.removeItem(STORAGE_KEYS.TOKEN);
    storage.removeItem(STORAGE_KEYS.USER);
    storage.removeItem(STORAGE_KEYS.ACTIVE_SESSION_ID);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      serverUrl,
      setServerUrl,
      login,
      logout,
      aiMode,
      setAiMode,
      isHydrating,
      activeSessionId,
      setActiveSessionId,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
