import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { SopListScreen } from './src/screens/SopListScreen';
import { SimulationScreen } from './src/screens/SimulationScreen';
import { ResultScreen } from './src/screens/ResultScreen';
import { api } from './src/api/client';
import { TrainingSessionResponse, FinalResultResponse } from './src/api/types';

const MainNavigator: React.FC = () => {
  const { user } = useAuth();
  const [currentSession, setCurrentSession] = useState<TrainingSessionResponse | null>(null);
  const [currentResult, setCurrentResult] = useState<FinalResultResponse | null>(null);
  const [startingSession, setStartingSession] = useState(false);

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
        }}
      />
    );
  }

  if (currentSession) {
    return (
      <SimulationScreen
        session={currentSession}
        onFinish={(result) => setCurrentResult(result)}
        onBack={() => setCurrentSession(null)}
      />
    );
  }

  const handleStartTraining = async (sopId: string, sopTitle: string) => {
    setStartingSession(true);
    try {
      const session = await api.startTraining(sopId);
      setCurrentSession(session);
    } catch (err: any) {
      alert(`Không thể bắt đầu phiên học: ${err.message}`);
    } finally {
      setStartingSession(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {startingSession && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#38BDF8" />
        </View>
      )}
      <SopListScreen onStartTraining={handleStartTraining} />
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
