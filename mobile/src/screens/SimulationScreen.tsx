import React, { useState, useRef, useEffect } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  FlatList, ActivityIndicator, Alert, SafeAreaView, 
  KeyboardAvoidingView, Platform 
} from 'react-native';
import * as Speech from 'expo-speech';
import { api } from '../api/client';
import { TrainingSessionResponse, FinalResultResponse } from '../api/types';

interface MessageItem {
  id: string;
  sender: 'customer' | 'employee';
  text: string;
  turnNo?: number;
}

interface SimulationScreenProps {
  session: TrainingSessionResponse;
  onFinish: (result: FinalResultResponse) => void;
  onBack: () => void;
}

export const SimulationScreen: React.FC<SimulationScreenProps> = ({ session, onFinish, onBack }) => {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'msg-0',
      sender: 'customer',
      text: session.module.opening_message,
      turnNo: 0,
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [turnsCount, setTurnsCount] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // Auto speak customer opening message
  useEffect(() => {
    speakText(session.module.opening_message);
  }, []);

  const speakText = (text: string) => {
    try {
      Speech.stop();
      setIsPlayingAudio(true);
      Speech.speak(text, {
        language: 'vi-VN',
        pitch: 1.0,
        rate: 0.95,
        onDone: () => setIsPlayingAudio(false),
        onError: () => setIsPlayingAudio(false),
      });
    } catch (_) {
      setIsPlayingAudio(false);
    }
  };

  const handleSend = async () => {
    const textToSend = inputText.trim();
    if (!textToSend) return;
    if (turnsCount >= 4) {
      Alert.alert('Thông báo', 'Đã đạt giới hạn tối đa 4 lượt. Vui lòng nhấn Nhận đánh giá.');
      return;
    }

    // Add employee message to local list immediately
    const empMsgId = `emp-${Date.now()}`;
    const newMessages: MessageItem[] = [
      ...messages,
      { id: empMsgId, sender: 'employee', text: textToSend, turnNo: turnsCount + 1 }
    ];
    setMessages(newMessages);
    setInputText('');
    setLoading(true);

    try {
      const res = await api.sendTurn(session.session_id, textToSend);
      const custMsgId = `cust-${Date.now()}`;
      setMessages([
        ...newMessages,
        { id: custMsgId, sender: 'customer', text: res.customer_text, turnNo: res.turn_no }
      ]);
      setTurnsCount(res.turn_no);
      speakText(res.customer_text);
    } catch (err: any) {
      Alert.alert('Lỗi gửi tin', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (turnsCount < 1) {
      Alert.alert('Chưa thể đánh giá', 'Vui lòng thực hiện ít nhất 1 lượt đối thoại với khách trước khi nhận đánh giá.');
      return;
    }
    setEvaluating(true);
    try {
      Speech.stop();
      const result = await api.evaluateSession(session.session_id);
      onFinish(result);
    } catch (err: any) {
      Alert.alert('Lỗi đánh giá', err.message);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack} style={styles.backBtn}>
            <Text style={styles.backBtnText}>✕ Thoát</Text>
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle} numberOfLines={1}>{session.sop_title}</Text>
            <Text style={styles.turnIndicator}>Lượt đối thoại: {turnsCount}/4</Text>
          </View>
          <TouchableOpacity 
            style={[styles.evalBtn, turnsCount < 1 && styles.disabledBtn]} 
            onPress={handleEvaluate}
            disabled={evaluating || turnsCount < 1}
          >
            {evaluating ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.evalBtnText}>Chấm điểm</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Situation / Context Card */}
        <View style={styles.situationCard}>
          <Text style={styles.situationLabel}>📌 Bối cảnh tình huống:</Text>
          <Text style={styles.situationText}>{session.module.situation}</Text>
          <Text style={styles.objectiveText}>🎯 Mục tiêu: {session.module.learning_objective}</Text>
        </View>

        {/* Conversation List */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => (
            <View style={[
              styles.bubbleWrapper, 
              item.sender === 'employee' ? styles.empWrapper : styles.custWrapper
            ]}>
              <View style={[
                styles.bubble, 
                item.sender === 'employee' ? styles.empBubble : styles.custBubble
              ]}>
                <View style={styles.senderHeader}>
                  <Text style={styles.senderName}>
                    {item.sender === 'customer' ? '👤 Khách hàng' : '🧑‍🍳 Bạn (Nhân viên)'}
                  </Text>
                  {item.sender === 'customer' && (
                    <TouchableOpacity 
                      style={styles.speakerBtn} 
                      onPress={() => speakText(item.text)}
                    >
                      <Text style={styles.speakerIcon}>🔊 Nghe</Text>
                    </TouchableOpacity>
                  )}
                </View>
                <Text style={styles.messageText}>{item.text}</Text>
              </View>
            </View>
          )}
        />

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder={turnsCount >= 4 ? "Đã xong 4 lượt. Nhấn 'Chấm điểm' ở trên." : "Nhập câu trả lời của bạn..."}
            placeholderTextColor="#64748B"
            editable={!loading && !evaluating && turnsCount < 4}
            multiline
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              (!inputText.trim() || loading || turnsCount >= 4) && styles.disabledBtn
            ]}
            onPress={handleSend}
            disabled={!inputText.trim() || loading || turnsCount >= 4}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.sendButtonText}>Gửi</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#1E293B',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  backBtn: {
    padding: 6,
  },
  backBtnText: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    marginHorizontal: 8,
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  turnIndicator: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
  },
  evalBtn: {
    backgroundColor: '#059669',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  evalBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  disabledBtn: {
    opacity: 0.5,
  },
  situationCard: {
    backgroundColor: '#1E293B',
    margin: 12,
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#F59E0B',
  },
  situationLabel: {
    color: '#F59E0B',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },
  situationText: {
    color: '#F1F5F9',
    fontSize: 13,
    lineHeight: 18,
  },
  objectiveText: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 6,
    fontStyle: 'italic',
  },
  messageList: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  bubbleWrapper: {
    marginVertical: 6,
    flexDirection: 'row',
  },
  custWrapper: {
    justifyContent: 'flex-start',
  },
  empWrapper: {
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '82%',
    padding: 12,
    borderRadius: 14,
  },
  custBubble: {
    backgroundColor: '#334155',
    borderBottomLeftRadius: 2,
  },
  empBubble: {
    backgroundColor: '#1D4ED8',
    borderBottomRightRadius: 2,
  },
  senderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  senderName: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '700',
  },
  speakerBtn: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  speakerIcon: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '600',
  },
  messageText: {
    color: '#F8FAFC',
    fontSize: 14,
    lineHeight: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#1E293B',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    gap: 10,
  },
  textInput: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#F8FAFC',
    fontSize: 14,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
