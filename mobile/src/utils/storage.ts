/**
 * Cross-platform lightweight key-value persistence for ShiftLens Mobile (Android & Web)
 * Ensures serverUrl, JWT token, and user context survive app restarts when supported.
 */
const memoryFallback: Record<string, string> = {};

export const storage = {
  async getItem(key: string): Promise<string | null> {
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
      if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis && globalThis.localStorage) {
        globalThis.localStorage.setItem(key, value);
      }
    } catch (_) {}
  },

  async removeItem(key: string): Promise<void> {
    delete memoryFallback[key];
    try {
      if (typeof globalThis !== 'undefined' && 'localStorage' in globalThis && globalThis.localStorage) {
        globalThis.localStorage.removeItem(key);
      }
    } catch (_) {}
  },
};
