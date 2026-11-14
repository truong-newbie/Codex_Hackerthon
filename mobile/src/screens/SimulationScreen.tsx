import React, { useState, useRef, useEffect } from 'react';
import { 
  View, Text, TextInput, TouchableOpacity, StyleSheet, 
  FlatList, ActivityIndicator, Alert, SafeAreaView, 
  KeyboardAvoidingView, Platform, ScrollView 
} from 'react-native';
import * as Speech from 'expo-speech';
import { api } from '../api/client';
import { TrainingSessionResponse, FinalResultResponse, TurnDetail } from '../api/types';

interface MessageItem {
  id: string;
  sender: 'customer' | 'employee';
  text: string;
  turnNo?: number;
}

interface SimulationScreenProps {
  session: TrainingSessionResponse;
  initialTurns?: TurnDetail[];
  onFinish: (result: FinalResultResponse) => void;
  onBack: () => void;
}

export const SimulationScreen: React.FC<SimulationScreenProps> = ({ 
  session, 
  initialTurns = [], 
  onFinish, 
  onBack 
}) => {
  const buildInitialMessages = (): MessageItem[] => {
    const base: MessageItem[] = [
      {
        id: 'msg-0',
        sender: 'customer',
        text: session.module.opening_message,
        turnNo: 0,
      }
    ];
    for (const t of initialTurns) {
      base.push({
        id: `emp-init-${t.turn_no}`,
        sender: 'employee',
        text: t.employee_text,
        turnNo: t.turn_no,
      });
      base.push({
        id: `cust-init-${t.turn_no}`,
        sender: 'customer',
        text: t.customer_text,
        turnNo: t.turn_no,
      });
    }
    return base;
  };

  const [messages, setMessages] = useState<MessageItem[]>(buildInitialMessages);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [needsSync, setNeedsSync] = useState(false);
  const [turnsCount, setTurnsCount] = useState(initialTurns.length || session.turns_count || 0);
  const [lastLatency, setLastLatency] = useState<number | undefined>(session.latency_ms);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (initialTurns.length === 0) {
      speakText(session.module.opening_message);
    }
    return () => {
      try { Speech.stop(); } catch (_) {}
    };
  }, []);

  const speakText = (text: string) => {
    try {
      Speech.stop();
      Speech.speak(text, {
        language: 'vi-VN',
        pitch: 1.0,
        rate: 0.95,
      });
    } catch (_) {}
  };

  const fillQuickReply = (type: 'pass_a' | 'pass_b' | 'critical_fail') => {
    if (type === 'pass_a') {
      setInputText(
        'Dạ em rất xin lỗi anh vì sự cố ly cà phê bị mặn ạ. Em xin phép kiểm tra lại hóa đơn và pha lại ngay một ly mới đúng chuẩn cho anh, còn việc hoàn tiền em xin phép báo quản lý hỗ trợ anh ngay nhé ạ!'
      );
    } else if (type === 'pass_b') {
      setInputText(
        'Dạ em rất xin lỗi anh về trải nghiệm chưa tốt này ạ. Để em kiểm tra lại ly nước, em xin phép pha lại ngay ly mới cho anh, gửi tặng anh thêm bánh quy và voucher 50.000đ cho lần sau ạ. Cảm ơn anh nhiều ạ!'
      );
    } else {
      setInputText(
        'Dạ em xin lỗi anh, em kiểm tra hóa đơn rồi ạ. Để em tự rút két hoàn tiền 100% lại luôn cho anh ngay bây giờ không cần hỏi ai đâu ạ!'
      );
    }
  };

  const handleSend = async () => {
    const textToSend = inputText.trim();
    if (!textToSend || loading || evaluating || needsSync) return;
    if (turnsCount >= 4) {
      Alert.alert('Thông báo', 'Đã đạt giới hạn tối đa 4 lượt. Vui lòng nhấn Chấm điểm.');
      return;
    }

    setLoading(true);

    try {
      const res = await api.sendTurn(session.session_id, textToSend);
      setMessages(previous => [
        ...previous,
        { id: `emp-${res.turn_no}`, sender: 'employee', text: res.employee_text, turnNo: res.turn_no },
        { id: `cust-${res.turn_no}`, sender: 'customer', text: res.customer_text, turnNo: res.turn_no }
      ]);
      setInputText('');
      setTurnsCount(res.turn_no);
      if (res.latency_ms !== undefined) {
        setLastLatency(res.latency_ms);
      }
      speakText(res.customer_text);
    } catch (err: any) {
      try {
        const detail = await api.getSessionDetail(session.session_id);
        const committed = detail.turns.find(
          turn => turn.turn_no === turnsCount + 1 && turn.employee_text === textToSend
        );
        if (committed) {
          setMessages(previous => [
            ...previous,
            { id: `emp-${committed.turn_no}`, sender: 'employee', text: committed.employee_text, turnNo: committed.turn_no },
            { id: `cust-${committed.turn_no}`, sender: 'customer', text: committed.customer_text, turnNo: committed.turn_no }
          ]);
          setTurnsCount(committed.turn_no);
          setInputText('');
        } else {
          setNeedsSync(true);
          Alert.alert('Chưa xác định trạng thái tin', 'Yêu cầu có thể vẫn đang xử lý. Hãy quay lại danh sách và mở lại phiên từ lịch sử trước khi gửi tiếp.');
        }
      } catch (_) {
        setNeedsSync(true);
        Alert.alert('Chưa xác định trạng thái tin', 'Mạng bị gián đoạn. Hãy mở lại phiên từ lịch sử để đồng bộ trước khi gửi lại.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (loading || evaluating || needsSync) return;
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
          <TouchableOpacity onPress={onBack} style={[styles.backBtn, (loading || evaluating) && styles.disabledBtn]} disabled={loading || evaluating}>
            <Text style={styles.backBtnText}>← SOP</Text>
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle} numberOfLines={1}>{session.sop_title}</Text>
            <Text style={styles.turnIndicator}>Lượt đối thoại: {turnsCount}/4</Text>
          </View>
          <TouchableOpacity 
            style={[styles.evalBtn, (turnsCount < 1 || loading || needsSync) && styles.disabledBtn]}
            onPress={handleEvaluate}
            disabled={evaluating || loading || needsSync || turnsCount < 1}
          >
            {evaluating ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.evalBtnText}>Chấm điểm</Text>
            )}
          </TouchableOpacity>
        </View>

        {needsSync && (
          <Text style={styles.turnIndicator}>
            Trạng thái tin chưa rõ. Quay lại danh sách và mở lại phiên từ lịch sử để đồng bộ.
          </Text>
        )}

        {/* Technical Telemetry Proof Bar (G1, G2, G3) */}
        <View style={styles.telemetryBar}>
          <Text style={styles.telemetryText}>
            {session.ai_mode === 'live' ? '🟢 AI: LIVE' : '🟠 AI: STUB'}  |  📌 Pinned: v{session.sop_version_no || 1} ({session.sop_version_id})
            {lastLatency !== undefined ? `  |  ⚡ ${lastLatency}ms` : ''}
          </Text>
        </View>

        {/* Situation / Context Card */}
        <View style={styles.situationCard}>
          <Text style={styles.situationLabel}>📌 Bối cảnh & Chính sách áp dụng:</Text>
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
                      <Text style={styles.speakerIcon}>🔊 Nghe TTS</Text>
                    </TouchableOpacity>
                  )}
                </View>
                <Text style={styles.messageText}>{item.text}</Text>
              </View>
            </View>
          )}
        />

        {/* Quick Reply Helper Chips for Smooth Live Stage Demo */}
        {turnsCount < 4 && (
          <View style={styles.quickChipsContainer}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsScroll}>
              <TouchableOpacity style={styles.chipPass} onPress={() => fillQuickReply('pass_a')}>
                <Text style={styles.chipText}>✨ Mẫu chuẩn Café A (Xin phép Quản lý)</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.chipPassB} onPress={() => fillQuickReply('pass_b')}>
                <Text style={styles.chipText}>🌿 Mẫu chuẩn Café B (Đổi ly + Bánh/Voucher)</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.chipFail} onPress={() => fillQuickReply('critical_fail')}>
                <Text style={styles.chipText}>⚠️ Thử vi phạm Critical (Tự ý hoàn tiền)</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        )}

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder={turnsCount >= 4 ? "Đã xong 4 lượt. Nhấn 'Chấm điểm' ở trên." : "Nhập câu trả lời của bạn..."}
            placeholderTextColor="#64748B"
            editable={!loading && !evaluating && turnsCount < 4}
            maxLength={1000}
            multiline
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              (!inputText.trim() || loading || evaluating || turnsCount >= 4) && styles.disabledBtn
            ]}
            onPress={handleSend}
            disabled={!inputText.trim() || loading || evaluating || needsSync || turnsCount >= 4}
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
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#1E293B',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  backBtn: {
    paddingVertical: 6,
    paddingHorizontal: 8,
    backgroundColor: '#334155',
    borderRadius: 6,
  },
  backBtnText: {
    color: '#E2E8F0',
    fontSize: 12,
    fontWeight: '700',
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
    marginHorizontal: 8,
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  turnIndicator: {
    color: '#38BDF8',
    fontSize: 11,
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
    fontSize: 12,
    fontWeight: '700',
  },
  disabledBtn: {
    opacity: 0.5,
  },
  telemetryBar: {
    backgroundColor: '#020617',
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    alignItems: 'center',
  },
  telemetryText: {
    color: '#38BDF8',
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: '600',
  },
  situationCard: {
    backgroundColor: '#1E293B',
    marginHorizontal: 12,
    marginTop: 10,
    marginBottom: 6,
    padding: 10,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#F59E0B',
  },
  situationLabel: {
    color: '#F59E0B',
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 3,
  },
  situationText: {
    color: '#F1F5F9',
    fontSize: 12,
    lineHeight: 17,
  },
  objectiveText: {
    color: '#94A3B8',
    fontSize: 11,
    marginTop: 4,
    fontStyle: 'italic',
  },
  messageList: {
    paddingHorizontal: 14,
    paddingBottom: 12,
  },
  bubbleWrapper: {
    marginVertical: 5,
    flexDirection: 'row',
  },
  custWrapper: {
    justifyContent: 'flex-start',
  },
  empWrapper: {
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '84%',
    padding: 11,
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
    marginBottom: 5,
    gap: 8,
  },
  senderName: {
    color: '#CBD5E1',
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
    fontSize: 10,
    fontWeight: '700',
  },
  messageText: {
    color: '#F8FAFC',
    fontSize: 13,
    lineHeight: 19,
  },
  quickChipsContainer: {
    backgroundColor: '#0F172A',
    paddingVertical: 6,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  chipsScroll: {
    paddingHorizontal: 12,
    gap: 8,
  },
  chipPass: {
    backgroundColor: '#1E3A8A',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#3B82F6',
  },
  chipPassB: {
    backgroundColor: '#064E3B',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#10B981',
  },
  chipFail: {
    backgroundColor: '#450A0A',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  chipText: {
    color: '#F8FAFC',
    fontSize: 11,
    fontWeight: '600',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    backgroundColor: '#1E293B',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    gap: 8,
  },
  textInput: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 8,
    color: '#F8FAFC',
    fontSize: 13,
    maxHeight: 90,
  },
  sendButton: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
});
