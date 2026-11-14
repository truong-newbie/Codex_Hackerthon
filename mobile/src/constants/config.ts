import { Platform } from 'react-native';

// Default host: 10.0.2.2 for Android emulator, localhost for web/iOS, or replace with local LAN IP for physical device
export const DEFAULT_API_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});
