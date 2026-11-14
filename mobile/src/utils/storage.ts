import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Cross-platform persistent storage for ShiftLens Mobile (Android Native APK, iOS & Web)
 * Uses native AsyncStorage on Android/iOS so auth token, serverUrl, and activeSessionId
 * survive Android OS Force-Stop and Relaunch (Gate G1 / FR-15 / AT-11).
 */
const memoryFallback: Record<string, string> = {};

export const storage = {
  async getItem(key: string): Promise<string | null> {
    try {
      const val = await AsyncStorage.getItem(key);
      if (val !== null) return val;
    } catch (_) {}
    try {
      if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis && globalThis.localStorage) {
        return globalThis.localStorage.getItem(key);
      }
    } catch (_) {}
    return memoryFallback[key] ?? null;
  },

  async setItem(key: string, value: string): Promise<void> {
    memoryFallback[key] = value;
    try {
      await AsyncStorage.setItem(key, value);
    } catch (_) {}
    try {
      if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis && globalThis.localStorage) {
        globalThis.localStorage.setItem(key, value);
      }
    } catch (_) {}
  },

  async removeItem(key: string): Promise<void> {
    delete memoryFallback[key];
    try {
      await AsyncStorage.removeItem(key);
    } catch (_) {}
    try {
      if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis && globalThis.localStorage) {
        globalThis.localStorage.removeItem(key);
      }
    } catch (_) {}
  },
};
