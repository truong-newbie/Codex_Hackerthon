import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { SopListScreen } from './src/screens/SopListScreen';
import { SimulationScreen } from './src/screens/SimulationScreen';
import { ResultScreen } from './src/screens/ResultScreen';
import { api, ApiError } from './src/api/client';
import { TrainingSessionResponse, FinalResultResponse, TurnDetail } from './src/api/types';

const MainNavigator: React.FC = () => {
  const { user, isHydrating, activeSessionId, setActiveSessionId } = useAuth();
  const [currentSession, setCurrentSession] = useState<TrainingSessionResponse | null>(null);
  const [initialTurns, setInitialTurns] = useState<TurnDetail[]>([]);
  const [currentResult, setCurrentResult] = useState<FinalResultResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const handleOpenExistingSession = async (sessionId: string) => {
    setBusy(true);
    try {
      const detail = await api.getSessionDetail(sessionId);
      if (detail.completed && detail.result) {
        await setActiveSessionId(null);
        setCurrentResult(detail.result);
      } else {
        await setActiveSessionId(detail.session_id);
        setInitialTurns(detail.turns || []);
        setCurrentSession({
          session_id: detail.session_id,
          tenant_id: detail.tenant_id,
          sop_id: detail.sop_id,
          sop_version_id: detail.sop_version_id,
          sop_version_no: detail.sop_version_no,
          sop_title: detail.sop_title,
          module: detail.module,
          completed: detail.completed,
          turns_count: detail.turns?.length || 0,
          ai_mode: detail.ai_mode,
        });
      }
    } catch (error) {
      if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
        await setActiveSessionId(null);
      } else {
        Alert.alert('Chưa thể khôi phục phiên', 'Không tải được phiên học lúc này. Phiên vẫn được lưu; hãy kiểm tra kết nối rồi mở lại từ lịch sử.');
      }
    } finally {
      setBusy(false);
    }
  };

  // Auto-resume active session after Android Force-Stop & Relaunch (Gate G1 / AT-11)
  useEffect(() => {
    if (!isHydrating && user && activeSessionId && !currentSession && !currentResult) {
      handleOpenExistingSession(activeSessionId);
    }
  }, [isHydrating, user]);

  if (isHydrating) {
    return (
      <View style={styles.hydratingContainer}>
        <ActivityIndicator size="large" color="#38BDF8" />
        <Text style={styles.hydratingText}>Đang khôi phục trạng thái phiên ShiftLens...</Text>
      </View>
    );
  }

  if (!user) {
    return <LoginScreen />;
  }

  if (currentResult) {
    return (
      <ResultScreen
        result={currentResult}
        onDone={() => {
          setActiveSessionId(null);
          setCurrentResult(null);
          setCurrentSession(null);
          setInitialTurns([]);
        }}
      />
    );
  }

  if (currentSession) {
    return (
      <SimulationScreen
        session={currentSession}
        initialTurns={initialTurns}
        onFinish={(result) => {
          setActiveSessionId(null);
          setCurrentResult(result);
        }}
        onBack={() => {
          setActiveSessionId(null);
          setCurrentSession(null);
          setInitialTurns([]);
        }}
      />
    );
  }

  const handleStartTraining = async (sopId: string, _sopTitle: string) => {
    setBusy(true);
    try {
      const session = await api.startTraining(sopId);
      await setActiveSessionId(session.session_id);
      setInitialTurns([]);
      setCurrentSession(session);
    } catch (err: any) {
      Alert.alert('Không thể bắt đầu phiên học', err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {busy && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#38BDF8" />
        </View>
      )}
      <SopListScreen
        onStartTraining={handleStartTraining}
        onOpenSession={handleOpenExistingSession}
      />
    </View>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <MainNavigator />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  hydratingContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
    justifyContent: 'center',
    alignItems: 'center',
  },
  hydratingText: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 12,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 999,
  },
});
