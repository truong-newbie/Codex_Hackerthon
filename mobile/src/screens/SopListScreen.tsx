import React, { useState, useEffect } from 'react';
import { 
  View, Text, TouchableOpacity, StyleSheet, 
  FlatList, ActivityIndicator, Alert, SafeAreaView 
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { SOPDetailResponse } from '../api/types';

interface SopListScreenProps {
  onStartTraining: (sopId: string, sopTitle: string) => void;
}

export const SopListScreen: React.FC<SopListScreenProps> = ({ onStartTraining }) => {
  const { user, logout, aiMode } = useAuth();
  const [sops, setSops] = useState<SOPDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingId, setStartingId] = useState<string | null>(null);

  const fetchSops = async () => {
    setLoading(true);
    try {
      const data = await api.getSops();
      setSops(data);
    } catch (err: any) {
      Alert.alert('Lỗi tải SOP', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSops();
  }, []);

  const handleStart = async (sop: SOPDetailResponse) => {
    if (!sop.active_version) {
      Alert.alert('Chưa sẵn sàng', 'Quy trình này chưa có phiên bản nào được phê duyệt.');
      return;
    }
    setStartingId(sop.id);
    try {
      onStartTraining(sop.id, sop.title);
    } finally {
      setStartingId(null);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <View>
          <Text style={styles.brandTitle}>ShiftLens</Text>
          <Text style={styles.tenantName}>📍 {user?.tenant_name || 'Cửa hàng'}</Text>
        </View>

        <View style={styles.rightHeader}>
          <View style={[styles.aiBadge, aiMode === 'live' ? styles.liveBadge : styles.stubBadge]}>
            <Text style={styles.aiBadgeText}>{aiMode === 'live' ? '● AI LIVE' : '○ AI STUB'}</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <Text style={styles.logoutBtnText}>Đăng xuất</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.content}>
        <View style={styles.welcomeBanner}>
          <Text style={styles.welcomeGreeting}>Xin chào, {user?.full_name || user?.username}!</Text>
          <Text style={styles.welcomeSubtitle}>
            Chọn một quy trình chuẩn (SOP) đã được phê duyệt để bắt đầu mô phỏng hội thoại với khách hàng AI.
          </Text>
        </View>

        <Text style={styles.listHeading}>Quy trình đào tạo khả dụng:</Text>

        {loading ? (
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color="#38BDF8" />
            <Text style={styles.loadingText}>Đang tải quy trình SOP...</Text>
          </View>
        ) : (
          <FlatList
            data={sops}
            keyExtractor={(item) => item.id}
            onRefresh={fetchSops}
            refreshing={loading}
            renderItem={({ item }) => (
              <View style={styles.sopCard}>
                <View style={styles.sopHeaderRow}>
                  <Text style={styles.sopTitle}>{item.title}</Text>
                  {item.active_version ? (
                    <View style={styles.versionPill}>
                      <Text style={styles.versionPillText}>v{item.active_version.version_no} Active</Text>
                    </View>
                  ) : (
                    <View style={[styles.versionPill, { backgroundColor: '#475569' }]}>
                      <Text style={styles.versionPillText}>Chưa duyệt</Text>
                    </View>
                  )}
                </View>

                {item.active_version && (
                  <View style={styles.sopMetaRow}>
                    <Text style={styles.sopMetaText}>
                      📋 {item.active_version.steps.length} bước thực hiện
                    </Text>
                    <Text style={styles.sopMetaText}>
                      🎯 {item.active_version.rubric.length} tiêu chí chấm điểm
                    </Text>
                  </View>
                )}

                <TouchableOpacity
                  style={[styles.startBtn, startingId === item.id && styles.disabledBtn]}
                  onPress={() => handleStart(item)}
                  disabled={startingId === item.id}
                >
                  {startingId === item.id ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.startBtnText}>▶ Bắt đầu luyện tập</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}
            ListEmptyComponent={
              <View style={styles.centerContainer}>
                <Text style={styles.emptyText}>Chưa có quy trình SOP nào được phê duyệt.</Text>
              </View>
            }
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#1E293B',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  brandTitle: {
    color: '#38BDF8',
    fontSize: 20,
    fontWeight: '800',
  },
  tenantName: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
  },
  rightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  aiBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  liveBadge: {
    backgroundColor: '#065F46',
  },
  stubBadge: {
    backgroundColor: '#7C2D12',
  },
  aiBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  logoutBtn: {
    backgroundColor: '#334155',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  logoutBtnText: {
    color: '#CBD5E1',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  welcomeBanner: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#38BDF8',
  },
  welcomeGreeting: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '700',
  },
  welcomeSubtitle: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 4,
    lineHeight: 18,
  },
  listHeading: {
    color: '#F1F5F9',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  sopCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sopHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  sopTitle: {
    flex: 1,
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
  },
  versionPill: {
    backgroundColor: '#0369A1',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  versionPillText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  sopMetaRow: {
    flexDirection: 'row',
    gap: 16,
    marginVertical: 12,
  },
  sopMetaText: {
    color: '#94A3B8',
    fontSize: 13,
  },
  startBtn: {
    backgroundColor: '#2563EB',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 4,
  },
  disabledBtn: {
    opacity: 0.6,
  },
  startBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    color: '#94A3B8',
    marginTop: 10,
    fontSize: 14,
  },
  emptyText: {
    color: '#64748B',
    fontSize: 14,
  },
});
