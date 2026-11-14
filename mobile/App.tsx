import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { SopListScreen } from './src/screens/SopListScreen';
import { SimulationScreen } from './src/screens/SimulationScreen';
import { ResultScreen } from './src/screens/ResultScreen';
import { api } from './src/api/client';
import { TrainingSessionResponse, FinalResultResponse, TurnDetail } from './src/api/types';

const MainNavigator: React.FC = () => {
  const { user } = useAuth();
  const [currentSession, setCurrentSession] = useState<TrainingSessionResponse | null>(null);
  const [initialTurns, setInitialTurns] = useState<TurnDetail[]>([]);
  const [currentResult, setCurrentResult] = useState<FinalResultResponse | null>(null);
  const [busy, setBusy] = useState(false);

  if (!user) {
    return <LoginScreen />;
  }

  if (currentResult) {
    return (
      <ResultScreen
        result={currentResult}
        onDone={() => {
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
        onFinish={(result) => setCurrentResult(result)}
        onBack={() => {
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
      setInitialTurns([]);
      setCurrentSession(session);
    } catch (err: any) {
      Alert.alert('Không thể bắt đầu phiên học', err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleOpenExistingSession = async (sessionId: string) => {
    setBusy(true);
    try {
      const detail = await api.getSessionDetail(sessionId);
      if (detail.completed && detail.result) {
        setCurrentResult(detail.result);
      } else {
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
    } catch (err: any) {
      Alert.alert('Lỗi mở phiên học', err.message);
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
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15, 23, 42, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 999,
  },
});
