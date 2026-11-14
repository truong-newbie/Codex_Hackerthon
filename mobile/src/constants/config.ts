import { Platform } from 'react-native';

// Priority:
// 1. User-saved Server URL in AsyncStorage (handled in AuthContext)
// 2. Build/runtime environment variable EXPO_PUBLIC_API_URL
// 3. Default host: 10.0.2.2 for Android emulator, localhost for web/iOS
export const DEFAULT_API_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  Platform.select({
    android: 'http://10.0.2.2:8000',
    default: 'http://localhost:8000',
  });

