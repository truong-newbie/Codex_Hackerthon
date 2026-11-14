const { withAndroidManifest } = require('expo/config-plugins');

/**
 * Ensures android:usesCleartextTraffic="true" is set on the main <application> tag
 * so both Debug and Release standalone APKs can connect to local LAN HTTP servers
 * (e.g., http://192.168.x.x:8000) during on-device hackathon demos.
 */
module.exports = function withCleartextTraffic(config) {
  return withAndroidManifest(config, (modConfig) => {
    const mainApplication = modConfig.modResults.manifest.application?.[0];
    if (mainApplication) {
      mainApplication.$['android:usesCleartextTraffic'] = 'true';
    }
    return modConfig;
  });
};
