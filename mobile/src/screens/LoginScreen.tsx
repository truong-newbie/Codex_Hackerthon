import React, { useState } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  ActivityIndicator, Alert, ScrollView 
} from 'react-native';
import { useAuth } from '../context/AuthContext';

export const LoginScreen: React.FC = () => {
  const { login, serverUrl, setServerUrl } = useAuth();
  const [username, setUsername] = useState('emp_a');
  const [password, setPassword] = useState('ShiftLens@2026');
  const [loading, setLoading] = useState(false);
  const [editingUrl, setEditingUrl] = useState(serverUrl);

  const handleLogin = async (userToLogin = username, passToLogin = password) => {
    if (!userToLogin.trim() || !passToLogin.trim()) {
      Alert.alert('Lỗi', 'Vui lòng nhập tên đăng nhập và mật khẩu');
      return;
    }
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
            <Text style={styles.quickButtonTitle}>☕ Café A (Nhân viên)</Text>
            <Text style={styles.quickButtonSub}>emp_a (Chính sách nghiêm ngặt)</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.quickButton, { borderColor: '#10B981' }]} 
            onPress={() => handleQuickSelect('emp_b')}
          >
            <Text style={styles.quickButtonTitle}>🌿 Café B (Nhân viên)</Text>
            <Text style={styles.quickButtonSub}>emp_b (Linh hoạt đổi món/voucher)</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.serverConfig}>
          <Text style={styles.serverConfigLabel}>Backend API URL:</Text>
          <View style={styles.serverConfigRow}>
            <TextInput
              style={[styles.input, { flex: 1, marginBottom: 0 }]}
              value={editingUrl}
              onChangeText={setEditingUrl}
              autoCapitalize="none"
            />
            <TouchableOpacity 
              style={styles.applyButton}
              onPress={() => {
                setServerUrl(editingUrl);
                Alert.alert('Thành công', `Đã lưu URL: ${editingUrl}`);
              }}
            >
              <Text style={styles.applyButtonText}>Lưu</Text>
            </TouchableOpacity>
          </View>
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
});
