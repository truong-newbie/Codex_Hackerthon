import React from 'react';
import { 
  View, Text, TouchableOpacity, StyleSheet, 
  ScrollView, SafeAreaView 
} from 'react-native';
import { FinalResultResponse } from '../api/types';

interface ResultScreenProps {
  result: FinalResultResponse;
  onDone: () => void;
}

export const ResultScreen: React.FC<ResultScreenProps> = ({ result, onDone }) => {
  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Báo Cáo Đánh Giá Kỹ Năng</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Score Overview Card */}
        <View style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>TỔNG ĐIỂM NĂNG LỰC</Text>
          <View style={styles.scoreRow}>
            <Text style={[styles.scoreNumber, result.passed ? styles.scoreGreen : styles.scoreRed]}>
              {result.score}
            </Text>
            <Text style={styles.scoreTotal}>/100</Text>
          </View>

          <View style={[styles.outcomeBadge, result.passed ? styles.passedBadge : styles.failedBadge]}>
            <Text style={styles.outcomeBadgeText}>
              {result.passed ? '✓ ĐẠT YÊU CẦU' : '✗ CHƯA ĐẠT'}
            </Text>
          </View>

          {result.critical_failure && (
            <View style={styles.criticalAlert}>
              <Text style={styles.criticalAlertText}>
                ⚠️ CẢNH BÁO: Không vượt qua bài thi do vi phạm Tiêu chí Chí tử (Critical Rule)!
              </Text>
            </View>
          )}
        </View>

        {/* Coaching Tip */}
        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>💡 Lời khuyên rèn luyện tiếp theo:</Text>
          <Text style={styles.tipBody}>{result.coaching_tip}</Text>
        </View>

        {/* Evidence Breakdown */}
        <Text style={styles.breakdownHeading}>Chi tiết minh chứng theo Rubric:</Text>
        
        {result.evidence.map((item, idx) => (
          <View key={item.criterion_id || idx} style={styles.evidenceCard}>
            <View style={styles.evidenceHeader}>
              <View style={styles.critInfo}>
                <Text style={styles.critId}>{item.criterion_id}</Text>
                <Text style={styles.critLabel}>{item.label}</Text>
              </View>
              <View style={styles.badgeRow}>
                {item.critical && (
                  <View style={styles.criticalTag}>
                    <Text style={styles.criticalTagText}>Bắt buộc</Text>
                  </View>
                )}
                <View style={[styles.critScoreTag, item.passed ? styles.greenTag : styles.redTag]}>
                  <Text style={styles.critScoreText}>
                    {item.passed ? `+${item.weight}đ` : '0đ'}
                  </Text>
                </View>
              </View>
            </View>

            {item.exact_quote ? (
              <View style={styles.quoteBox}>
                <Text style={styles.quoteLabel}>
                  {item.quote_verified ? '🔍 Bằng chứng trích dẫn thực tế:' : '⚠️ Bằng chứng không khớp:'}
                </Text>
                <Text style={styles.quoteText}>"{item.exact_quote}"</Text>
              </View>
            ) : (
              <View style={[styles.quoteBox, { backgroundColor: '#1E293B' }]}>
                <Text style={styles.missingQuoteText}>Không tìm thấy bằng chứng phát ngôn phù hợp trong cuộc đối thoại.</Text>
              </View>
            )}

            <Text style={styles.explanationText}>📝 {item.explanation}</Text>
          </View>
        ))}

        {/* Disclaimer */}
        <View style={styles.disclaimerBox}>
          <Text style={styles.disclaimerText}>{result.disclaimer}</Text>
        </View>

        {/* Done / Continue Button */}
        <TouchableOpacity style={styles.finishBtn} onPress={onDone}>
          <Text style={styles.finishBtnText}>Hoàn tất bài luyện tập</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: '#1E293B',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
    alignItems: 'center',
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  scoreCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  scoreLabel: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginVertical: 10,
  },
  scoreNumber: {
    fontSize: 54,
    fontWeight: '900',
  },
  scoreGreen: {
    color: '#10B981',
  },
  scoreRed: {
    color: '#EF4444',
  },
  scoreTotal: {
    fontSize: 20,
    color: '#64748B',
    fontWeight: '600',
    marginLeft: 4,
  },
  outcomeBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
  },
  passedBadge: {
    backgroundColor: '#065F46',
  },
  failedBadge: {
    backgroundColor: '#7F1D1D',
  },
  outcomeBadgeText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 13,
  },
  criticalAlert: {
    backgroundColor: '#450A0A',
    padding: 10,
    borderRadius: 8,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#DC2626',
    width: '100%',
  },
  criticalAlertText: {
    color: '#FCA5A5',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  tipCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#38BDF8',
  },
  tipTitle: {
    color: '#38BDF8',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 4,
  },
  tipBody: {
    color: '#E2E8F0',
    fontSize: 13,
    lineHeight: 18,
  },
  breakdownHeading: {
    color: '#F1F5F9',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  evidenceCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  evidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  critInfo: {
    flex: 1,
    marginRight: 8,
  },
  critId: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '700',
  },
  critLabel: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  criticalTag: {
    backgroundColor: '#7F1D1D',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  criticalTagText: {
    color: '#FECACA',
    fontSize: 10,
    fontWeight: '700',
  },
  critScoreTag: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  greenTag: {
    backgroundColor: '#065F46',
  },
  redTag: {
    backgroundColor: '#374151',
  },
  critScoreText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  quoteBox: {
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  quoteLabel: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 2,
  },
  quoteText: {
    color: '#E2E8F0',
    fontSize: 13,
    fontStyle: 'italic',
  },
  missingQuoteText: {
    color: '#64748B',
    fontSize: 12,
  },
  explanationText: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 16,
  },
  disclaimerBox: {
    padding: 12,
    marginVertical: 12,
    alignItems: 'center',
  },
  disclaimerText: {
    color: '#64748B',
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 16,
  },
  finishBtn: {
    backgroundColor: '#2563EB',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  finishBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
