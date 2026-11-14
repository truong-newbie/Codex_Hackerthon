import React, { useState, useEffect } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  ActivityIndicator, Alert, ScrollView 
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

export const LoginScreen: React.FC = () => {
  const { login, serverUrl, setServerUrl, setAiMode } = useAuth();
  const [username, setUsername] = useState('emp_a');
  const [password, setPassword] = useState('ShiftLens@2026');
  const [loading, setLoading] = useState(false);
  const [editingUrl, setEditingUrl] = useState(serverUrl);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);

  useEffect(() => {
    setEditingUrl(serverUrl);
  }, [serverUrl]);

  const applyUrlIfNeeded = () => {
    const cleanUrl = editingUrl.trim();
    if (cleanUrl && cleanUrl !== serverUrl) {
      setServerUrl(cleanUrl);
    }
  };

  const handleCheckConnection = async () => {
    const cleanUrl = editingUrl.trim();
    if (!cleanUrl) {
      Alert.alert('Lỗi', 'Vui lòng nhập Backend API URL');
      return;
    }
    setServerUrl(cleanUrl);
    setCheckingHealth(true);
    setHealthStatus(null);
    try {
      const health = await api.checkHealth();
      setAiMode(health.ai_mode);
      const modeLabel = health.ai_mode === 'live' ? '🟢 AI LIVE' : '🟠 AI STUB';
      setHealthStatus(`✅ Đã kết nối (${modeLabel} • v${health.version})`);
    } catch (err: any) {
      setHealthStatus(`❌ ${err.message || 'Không thể kết nối máy chủ'}`);
    } finally {
      setCheckingHealth(false);
    }
  };

  const handleLogin = async (userToLogin = username, passToLogin = password) => {
    if (!userToLogin.trim() || !passToLogin.trim()) {
      Alert.alert('Lỗi', 'Vui lòng nhập tên đăng nhập và mật khẩu');
      return;
    }
    applyUrlIfNeeded();
    setLoading(true);
    try {
      await login(userToLogin, passToLogin);
    } catch (err: any) {
      Alert.alert('Đăng nhập thất bại', err.message || 'Không thể đăng nhập');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (u: string) => {
    setUsername(u);
    setPassword('ShiftLens@2026');
    handleLogin(u, 'ShiftLens@2026');
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Codex Hackathon 2026</Text>
        </View>
        <Text style={styles.title}>ShiftLens</Text>
        <Text style={styles.subtitle}>AI Workforce Training & Simulation</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Đăng Nhập Nhân Viên</Text>
        
        <Text style={styles.label}>Tài khoản (Username / Email):</Text>
        <TextInput
          style={styles.input}
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          placeholder="emp_a hoặc emp_b"
        />

        <Text style={styles.label}>Mật khẩu:</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="ShiftLens@2026"
        />

        <TouchableOpacity 
          style={[styles.primaryButton, loading && styles.disabledButton]} 
          onPress={() => handleLogin()}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.primaryButtonText}>Đăng Nhập</Text>
          )}
        </TouchableOpacity>

        <Text style={styles.dividerText}>── Đăng nhập nhanh cho Demo ──</Text>

        <View style={styles.quickGrid}>
          <TouchableOpacity 
            style={[styles.quickButton, { borderColor: '#3B82F6' }]} 
            onPress={() => handleQuickSelect('emp_a')}
          >
            <Text style={styles.quickButtonTitle}>☕ Café A (Nhân viên: emp_a)</Text>
            <Text style={styles.quickButtonSub}>Chính sách nghiêm ngặt (Không tự hoàn tiền)</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.quickButton, { borderColor: '#10B981' }]} 
            onPress={() => handleQuickSelect('emp_b')}
          >
            <Text style={styles.quickButtonTitle}>🌿 Café B (Nhân viên: emp_b)</Text>
            <Text style={styles.quickButtonSub}>Chính sách linh hoạt (Đổi món / Voucher &lt; 50k)</Text>
          </TouchableOpacity>

          <View style={{ flexDirection: 'row', gap: 8 }}>
            <TouchableOpacity 
              style={[styles.quickButton, { flex: 1, borderColor: '#F59E0B' }]} 
              onPress={() => handleQuickSelect('manager_a')}
            >
              <Text style={styles.quickButtonTitle}>👔 Quản lý Café A</Text>
              <Text style={styles.quickButtonSub}>manager_a (Buyer View)</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.quickButton, { flex: 1, borderColor: '#8B5CF6' }]} 
              onPress={() => handleQuickSelect('manager_b')}
            >
              <Text style={styles.quickButtonTitle}>👔 Quản lý Café B</Text>
              <Text style={styles.quickButtonSub}>manager_b (Buyer View)</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.serverConfig}>
          <Text style={styles.serverConfigLabel}>Backend API URL (Emulator: 10.0.2.2 | Máy thật: IP LAN):</Text>
          <View style={styles.serverConfigRow}>
            <TextInput
              style={[styles.input, { flex: 1, marginBottom: 0 }]}
              value={editingUrl}
              onChangeText={setEditingUrl}
              autoCapitalize="none"
              placeholder="http://192.168.1.xxx:8000"
            />
            <TouchableOpacity 
              style={styles.applyButton}
              onPress={handleCheckConnection}
              disabled={checkingHealth}
            >
              {checkingHealth ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.applyButtonText}>Lưu & Test</Text>
              )}
            </TouchableOpacity>
          </View>
          {healthStatus && (
            <Text style={styles.healthStatusText}>{healthStatus}</Text>
          )}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#0F172A',
    padding: 20,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  badge: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#38BDF8',
  },
  badgeText: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '600',
  },
  title: {
    fontSize: 34,
    fontWeight: '800',
    color: '#F8FAFC',
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 16,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#CBD5E1',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#F8FAFC',
    fontSize: 14,
    marginBottom: 16,
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 4,
  },
  disabledButton: {
    opacity: 0.6,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  dividerText: {
    textAlign: 'center',
    color: '#64748B',
    fontSize: 12,
    marginVertical: 16,
  },
  quickGrid: {
    gap: 10,
  },
  quickButton: {
    backgroundColor: '#0F172A',
    borderWidth: 1.5,
    borderRadius: 8,
    padding: 12,
  },
  quickButtonTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  quickButtonSub: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  serverConfig: {
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  serverConfigLabel: {
    fontSize: 12,
    color: '#94A3B8',
    marginBottom: 6,
  },
  serverConfigRow: {
    flexDirection: 'row',
    gap: 8,
  },
  applyButton: {
    backgroundColor: '#334155',
    paddingHorizontal: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  applyButtonText: {
    color: '#F8FAFC',
    fontWeight: '600',
    fontSize: 13,
  },
  healthStatusText: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 8,
  },
});
