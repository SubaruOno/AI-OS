import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Feed, loadFeed } from '@/lib/feed';
import { useColors } from '@/lib/theme';
import { Badge } from '@/lib/ui';

export default function InfoScreen() {
  const colors = useColors();
  const [feed, setFeed] = useState<Feed | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setFeed((await loadFeed()).feed);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!feed) {
    return (
      <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
        <ActivityIndicator style={{ marginTop: 80 }} />
      </SafeAreaView>
    );
  }

  const mails = feed.companies.flatMap((c) => c.mails);
  mails.sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={refresh} />}>
        <Text style={[styles.title, { color: colors.text }]}>情報</Text>
        <Text style={[styles.meta, { color: colors.muted }]}>
          メール {feed.mail_count}件 ・ 解析 {feed.generated_at.replace('T', ' ').slice(0, 16)}
        </Text>

        <Section title="併願制限・前提条件" colors={colors}>
          {feed.rules.map((rule) => (
            <Text key={rule} style={[styles.line, { color: colors.text }]}>
              ・{rule.replace(/\*\*/g, '')}
            </Text>
          ))}
        </Section>

        <Section title="応募済み・関係がある企業" colors={colors}>
          {feed.applied.map((entry) => (
            <Text key={entry} style={[styles.line, { color: colors.text }]}>
              ・{entry}
            </Text>
          ))}
        </Section>

        <Section title="メールから拾った動き" colors={colors}>
          {mails.length === 0 && (
            <Text style={[styles.line, { color: colors.muted }]}>
              まだありません。`python3 sync_gmail.py` で取り込みます。
            </Text>
          )}
          {mails.slice(0, 25).map((mail) => (
            <View key={`${mail.date}-${mail.subject}`} style={styles.mail}>
              <View style={styles.mailHead}>
                <Text style={[styles.mailDate, { color: colors.muted }]}>{mail.date}</Text>
                <Badge
                  text={mail.signal ?? '案内'}
                  tone={mail.signal_rank === -1 ? 'red' : mail.signal_rank === null ? 'gray' : 'blue'}
                />
              </View>
              <Text style={[styles.mailSubject, { color: colors.text }]} numberOfLines={2}>
                {mail.subject}
              </Text>
              <Text style={[styles.mailSender, { color: colors.muted }]} numberOfLines={1}>
                {mail.sender}
              </Text>
            </View>
          ))}
        </Section>

        <Section title="読み方" colors={colors}>
          {feed.legend.map((line) => (
            <Text key={line} style={[styles.line, { color: colors.text }]}>
              ・{line.replace(/\*\*/g, '')}
            </Text>
          ))}
          <Text style={[styles.line, { color: colors.muted }]}>
            元データ: {feed.sources.map((s) => s.split('/').pop()).join(' ・ ')}
          </Text>
        </Section>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, colors, children }: { title: string; colors: any; children: React.ReactNode }) {
  return (
    <View style={[styles.section, { backgroundColor: colors.card, borderColor: colors.line }]}>
      <Text style={[styles.sectionTitle, { color: colors.text }]}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 16, paddingBottom: 40, gap: 10 },
  title: { fontSize: 26, fontWeight: '700' },
  meta: { fontSize: 12 },
  section: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 14, padding: 12, gap: 4, marginTop: 6 },
  sectionTitle: { fontSize: 14, fontWeight: '700', marginBottom: 4 },
  line: { fontSize: 13, lineHeight: 19 },
  mail: { gap: 3, paddingVertical: 6, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: '#00000010' },
  mailHead: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  mailDate: { fontSize: 11 },
  mailSubject: { fontSize: 13 },
  mailSender: { fontSize: 11 },
});
