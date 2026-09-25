import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Company, Feed, loadFeed } from '@/lib/feed';
import { useColors } from '@/lib/theme';
import { Badge, StageBar, formatDate, relativeLabel, todayISO } from '@/lib/ui';

const MEDALS = ['🥇', '🥈', '🥉'];

export default function LeaderboardScreen() {
  const colors = useColors();
  const [feed, setFeed] = useState<Feed | null>(null);
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  const refresh = useCallback(async () => {
    setLoading(true);
    const result = await loadFeed();
    setFeed(result.feed);
    setLive(result.live);
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

  const today = todayISO();
  const items = feed.items;
  const todayItems = items.filter((i) => i.date === today && i.status === 'open');
  const overdue = items.filter((i) => i.date && i.date < today && i.status === 'open');
  const active = feed.companies.filter((c) => c.stage_rank > 0);

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={refresh} />}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>就活リーダーボード</Text>
          <Text style={[styles.meta, { color: colors.muted }]}>
            {live ? 'サーバーから取得' : '同梱データ'} ・ 更新 {feed.generated_at.replace('T', ' ').slice(5, 16)}
          </Text>
        </View>

        <View style={styles.tiles}>
          <Tile label="今日" value={todayItems.length} colors={colors} />
          <Tile label="期限切れ" value={overdue.length} colors={colors} tone="danger" />
          <Tile label="進行中" value={active.length} colors={colors} tone="good" />
          <Tile label="メール" value={feed.mail_count} colors={colors} />
        </View>

        {feed.warnings.length > 0 && (
          <View style={[styles.warn, { borderColor: colors.line, backgroundColor: colors.card }]}>
            <Text style={{ color: colors.muted, fontSize: 12 }}>{feed.warnings.join(' / ')}</Text>
          </View>
        )}

        {feed.companies.map((company) => (
          <CompanyRow
            key={company.name}
            company={company}
            colors={colors}
            expanded={!!open[company.name]}
            onToggle={() => setOpen((prev) => ({ ...prev, [company.name]: !prev[company.name] }))}
          />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

function Tile({ label, value, colors, tone }: { label: string; value: number; colors: any; tone?: 'danger' | 'good' }) {
  const color = tone === 'danger' ? colors.danger : tone === 'good' ? '#1f8a52' : colors.text;
  return (
    <View style={[styles.tile, { backgroundColor: colors.card, borderColor: colors.line }]}>
      <Text style={[styles.tileValue, { color }]}>{value}</Text>
      <Text style={[styles.tileLabel, { color: colors.muted }]}>{label}</Text>
    </View>
  );
}

function CompanyRow({
  company,
  colors,
  expanded,
  onToggle,
}: {
  company: Company;
  colors: any;
  expanded: boolean;
  onToggle: () => void;
}) {
  const medal = MEDALS[company.rank - 1];
  const next = company.next;
  const overdue = next ? next.days_left < 0 : false;

  return (
    <Pressable
      onPress={onToggle}
      style={[styles.card, { backgroundColor: colors.card, borderColor: colors.line }]}>
      <View style={styles.rowTop}>
        <View style={[styles.rankBox, { borderColor: colors.line }]}>
          <Text style={[styles.rankText, { color: company.rank <= 3 ? colors.gold : colors.muted }]}>
            {medal ?? company.rank}
          </Text>
        </View>
        <View style={styles.rowMain}>
          <Text style={[styles.rowName, { color: colors.text }]} numberOfLines={1}>
            {company.name}
          </Text>
          <View style={styles.rowSub}>
            <StageBar rank={company.stage_rank} />
            <Text style={[styles.rowStage, { color: colors.muted }]}>{company.stage}</Text>
          </View>
        </View>
        <View style={styles.scoreBox}>
          <Text style={[styles.score, { color: colors.accent }]}>{company.score}</Text>
          <Text style={[styles.scoreLabel, { color: colors.muted }]}>pt</Text>
        </View>
      </View>

      {next && (
        <View style={styles.rowBottom}>
          <Badge text={next.source === 'email' ? 'メール' : next.source === 'navi' ? 'ナビ' : 'メール＋ナビ'}
            tone={next.source === 'email' ? 'blue' : next.source === 'navi' ? 'amber' : 'purple'} />
          <Badge text={overdue ? relativeLabel(next.date) : `${formatDate(next.date)} ${relativeLabel(next.date)}`}
            tone={overdue ? 'red' : 'gray'} />
          <Text style={[styles.rowNext, { color: colors.muted }]} numberOfLines={1}>
            {next.title}
          </Text>
        </View>
      )}

      {expanded && (
        <View style={[styles.detail, { borderTopColor: colors.line }]}>
          {company.mails.length > 0 && (
            <>
              <Text style={[styles.detailHead, { color: colors.muted }]}>メール</Text>
              {company.mails.map((mail) => (
                <Text key={`${mail.date}-${mail.subject}`} style={[styles.detailLine, { color: colors.text }]}>
                  {mail.date} {mail.signal ? `[${mail.signal}] ` : ''}
                  {mail.subject}
                </Text>
              ))}
            </>
          )}
          <Text style={[styles.detailHead, { color: colors.muted }]}>
            締切 {company.open_count}件{company.overdue_count > 0 ? `（期限切れ ${company.overdue_count}件）` : ''}
          </Text>
          <Text style={[styles.detailHint, { color: colors.muted }]}>
            詳しい締切は「締切」タブで確認できます。
          </Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 16, paddingBottom: 40, gap: 10 },
  header: { marginBottom: 2 },
  title: { fontSize: 26, fontWeight: '700' },
  meta: { fontSize: 12, marginTop: 2 },
  tiles: { flexDirection: 'row', gap: 8 },
  tile: { flex: 1, borderWidth: StyleSheet.hairlineWidth, borderRadius: 12, paddingVertical: 10, alignItems: 'center' },
  tileValue: { fontSize: 20, fontWeight: '700' },
  tileLabel: { fontSize: 11, marginTop: 1 },
  warn: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 10, padding: 10 },
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 14, padding: 12, gap: 8 },
  rowTop: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  rankBox: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankText: { fontSize: 15, fontWeight: '700' },
  rowMain: { flex: 1, gap: 3 },
  rowName: { fontSize: 16, fontWeight: '600' },
  rowSub: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  rowStage: { fontSize: 12 },
  scoreBox: { flexDirection: 'row', alignItems: 'baseline', gap: 1 },
  score: { fontSize: 19, fontWeight: '700' },
  scoreLabel: { fontSize: 11 },
  rowBottom: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  rowNext: { fontSize: 12, flexShrink: 1 },
  detail: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 8, gap: 3 },
  detailHead: { fontSize: 11, fontWeight: '600', marginTop: 4 },
  detailLine: { fontSize: 12.5 },
  detailHint: { fontSize: 12 },
});
