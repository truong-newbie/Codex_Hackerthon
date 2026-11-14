import React, { useState, useEffect } from 'react';
import { 
  View, Text, TouchableOpacity, StyleSheet, 
  ScrollView, ActivityIndicator, Alert, SafeAreaView, RefreshControl 
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { SOPDetailResponse, SessionSummaryItem } from '../api/types';

interface SopListScreenProps {
  onStartTraining: (sopId: string, sopTitle: string) => void;
  onOpenSession: (sessionId: string) => void;
}

export const SopListScreen: React.FC<SopListScreenProps> = ({ onStartTraining, onOpenSession }) => {
  const { user, logout, aiMode, setAiMode } = useAuth();
  const [sops, setSops] = useState<SOPDetailResponse[]>([]);
  const [sessions, setSessions] = useState<SessionSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [openingSessionId, setOpeningSessionId] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sopsData, sessionsData, healthData] = await Promise.all([
        api.getSops(),
        api.getSessions(),
        api.checkHealth().catch(() => null),
      ]);
      setSops(sopsData);
      setSessions(sessionsData);
      if (healthData) {
        setAiMode(healthData.ai_mode);
      }
    } catch (err: any) {
      Alert.alert('Lỗi tải dữ liệu', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStart = async (sop: SOPDetailResponse) => {
    if (!sop.active_version) {
      Alert.alert('Chưa sẵn sàng', 'Quy trình này chưa có phiên bản nào được phê duyệt.');
      return;
    }
    setStartingId(sop.id);
    try {
      await onStartTraining(sop.id, sop.title);
    } finally {
      setStartingId(null);
    }
  };

  const handleOpenExisting = async (sessionId: string) => {
    setOpeningSessionId(sessionId);
    try {
      await onOpenSession(sessionId);
    } finally {
      setOpeningSessionId(null);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <View style={{ flex: 1 }}>
          <Text style={styles.brandTitle}>ShiftLens</Text>
          <Text style={styles.tenantName} numberOfLines={1}>📍 {user?.tenant_name || 'Cửa hàng'}</Text>
        </View>

        <View style={styles.rightHeader}>
          <View style={[styles.aiBadge, aiMode === 'live' ? styles.liveBadge : styles.stubBadge]}>
            <Text style={styles.aiBadgeText}>{aiMode === 'live' ? '● AI LIVE' : '○ AI STUB'}</Text>
          </View>
          <TouchableOpacity style={styles.refreshBtn} onPress={fetchData}>
            <Text style={styles.refreshBtnText}>🔄 Làm mới</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <Text style={styles.logoutBtnText}>Thoát</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={{ paddingBottom: 36 }}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchData} tintColor="#38BDF8" />}
      >
        <View style={styles.welcomeBanner}>
          <Text style={styles.welcomeGreeting}>Xin chào, {user?.full_name || user?.username}!</Text>
          <Text style={styles.welcomeSubtitle}>
            Chọn quy trình chuẩn (SOP) bên dưới để thực hành với khách hàng AI. Mỗi phiên học sẽ ghim cố định phiên bản SOP tại thời điểm bắt đầu (Session Pinning).
          </Text>
        </View>

        <Text style={styles.listHeading}>1. Quy trình SOP đang kích hoạt (Approved Active):</Text>

        {loading && sops.length === 0 ? (
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color="#38BDF8" />
            <Text style={styles.loadingText}>Đang đồng bộ SOP và lịch sử phiên học...</Text>
          </View>
        ) : (
          sops.map((item) => (
            <View key={item.id} style={styles.sopCard}>
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
                <>
                  <Text style={styles.versionIdText}>
                    🔑 Active Version ID: {item.active_version.id}
                  </Text>
                  <View style={styles.stepsPreviewBox}>
                    {item.active_version.steps.map((s) => (
                      <Text key={s.id} style={styles.stepPreviewLine}>
                        • <Text style={{ fontWeight: '700', color: '#38BDF8' }}>{s.id}:</Text> {s.instruction}
                      </Text>
                    ))}
                  </View>
                  <View style={styles.sopMetaRow}>
                    <Text style={styles.sopMetaText}>
                      📋 {item.active_version.steps.length} bước SOP
                    </Text>
                    <Text style={styles.sopMetaText}>
                      🎯 {item.active_version.rubric.length} tiêu chí (100đ)
                    </Text>
                  </View>
                </>
              )}

              <TouchableOpacity
                style={[styles.startBtn, startingId === item.id && styles.disabledBtn]}
                onPress={() => handleStart(item)}
                disabled={startingId === item.id}
              >
                {startingId === item.id ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.startBtnText}>
                    ▶ Bắt đầu Phiên mới (Pin v{item.active_version?.version_no || 1})
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          ))
        )}

        {/* Recent Sessions Section for G1 Force-Stop Recovery & G3 Version Pinning Proof */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.listHeading}>2. Lịch sử Phiên học (Chứng minh Session Pin v1/v2):</Text>
        </View>

        {sessions.length === 0 ? (
          <View style={styles.emptySessionBox}>
            <Text style={styles.emptyText}>Chưa có phiên luyện tập nào. Hãy nhấn "Bắt đầu Phiên mới" ở trên.</Text>
          </View>
        ) : (
          sessions.map((sess) => (
            <TouchableOpacity
              key={sess.session_id}
              style={styles.sessionCard}
              onPress={() => handleOpenExisting(sess.session_id)}
              disabled={openingSessionId === sess.session_id}
            >
              <View style={styles.sessionHeaderRow}>
                <View style={styles.pinBadge}>
                  <Text style={styles.pinBadgeText}>📌 Pinned: v{sess.sop_version_no}</Text>
                </View>
                {sess.completed ? (
                  <View style={[styles.statusBadge, sess.passed ? styles.passBadge : styles.failBadge]}>
                    <Text style={styles.statusBadgeText}>
                      {sess.passed ? `✓ ĐẠT (${sess.score}/100)` : `✗ CHƯA ĐẠT (${sess.score}/100)`}
                    </Text>
                  </View>
                ) : (
                  <View style={styles.inProgressBadge}>
                    <Text style={styles.statusBadgeText}>⏳ Đang học ({sess.turns_count}/4 lượt)</Text>
                  </View>
                )}
              </View>

              <Text style={styles.sessionTitle} numberOfLines={1}>{sess.sop_title}</Text>
              <Text style={styles.sessionMeta}>
                Session: #{sess.session_id.slice(0, 8)} • SOP Version ID: {sess.sop_version_id}
              </Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
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
    paddingHorizontal: 16,
    paddingVertical: 12,
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
    gap: 6,
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
    fontSize: 10,
    fontWeight: '700',
  },
  refreshBtn: {
    backgroundColor: '#0284C7',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
  },
  refreshBtnText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  logoutBtn: {
    backgroundColor: '#334155',
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 6,
  },
  logoutBtnText: {
    color: '#CBD5E1',
    fontSize: 11,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  welcomeBanner: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#38BDF8',
  },
  welcomeGreeting: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  welcomeSubtitle: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 4,
    lineHeight: 18,
  },
  listHeading: {
    color: '#F1F5F9',
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 10,
  },
  sopCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    marginBottom: 18,
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
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 21,
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
  versionIdText: {
    color: '#38BDF8',
    fontSize: 11,
    fontFamily: 'monospace',
    marginTop: 6,
  },
  stepsPreviewBox: {
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
    gap: 4,
  },
  stepPreviewLine: {
    color: '#CBD5E1',
    fontSize: 12,
    lineHeight: 17,
  },
  sopMetaRow: {
    flexDirection: 'row',
    gap: 16,
    marginVertical: 10,
  },
  sopMetaText: {
    color: '#94A3B8',
    fontSize: 12,
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
  sectionHeaderRow: {
    marginTop: 4,
  },
  emptySessionBox: {
    backgroundColor: '#1E293B',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  sessionCard: {
    backgroundColor: '#1E293B',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sessionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  pinBadge: {
    backgroundColor: '#312E81',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#6366F1',
  },
  pinBadgeText: {
    color: '#C7D2FE',
    fontSize: 11,
    fontWeight: '700',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  passBadge: {
    backgroundColor: '#065F46',
  },
  failBadge: {
    backgroundColor: '#7F1D1D',
  },
  inProgressBadge: {
    backgroundColor: '#78350F',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  sessionTitle: {
    color: '#F1F5F9',
    fontSize: 13,
    fontWeight: '600',
  },
  sessionMeta: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 4,
    fontFamily: 'monospace',
  },
  centerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 30,
  },
  loadingText: {
    color: '#94A3B8',
    marginTop: 10,
    fontSize: 13,
  },
  emptyText: {
    color: '#64748B',
    fontSize: 13,
    textAlign: 'center',
  },
});
