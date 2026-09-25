import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Feed, FeedItem, loadFeed } from '@/lib/feed';
import { useColors } from '@/lib/theme';
import { Badge, formatDate, relativeLabel, todayISO, weekday } from '@/lib/ui';

type Filter = 'today' | 'week' | 'overdue' | 'all';

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: 'week', label: '7日以内' },
  { key: 'overdue', label: '期限切れ' },
  { key: 'all', label: 'すべて' },
];

export default function DeadlinesScreen() {
  const colors = useColors();
  const [feed, setFeed] = useState<Feed | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>('week');

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

  const today = todayISO();
  const visible = feed.items.filter((item) => {
    if (item.status === 'done' || item.status === 'declined') return false;
    if (filter === 'all') return true;
    if (!item.date) return false;
    if (filter === 'today') return item.date === today;
    if (filter === 'overdue') return item.date < today;
    const diff = Math.round(
      (Date.parse(`${item.date}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86400000,
    );
    return diff >= 0 && diff <= 6;
  });

  const groups = new Map<string, FeedItem[]>();
  for (const item of visible) {
    const key = item.date ?? 'none';
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  const keys = [...groups.keys()].sort((a, b) => (a === 'none' ? 1 : b === 'none' ? -1 : a < b ? -1 : 1));

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={refresh} />}>
        <Text style={[styles.title, { color: colors.text }]}>締切</Text>
        <Text style={[styles.meta, { color: colors.muted }]}>
          {visible.length}件 ・ 期限切れは赤で表示
        </Text>

        <View style={styles.filters}>
          {FILTERS.map((f) => (
            <Pressable
              key={f.key}
              onPress={() => setFilter(f.key)}
              style={[
                styles.chip,
                {
                  backgroundColor: filter === f.key ? colors.accent : colors.card,
                  borderColor: filter === f.key ? colors.accent : colors.line,
                },
              ]}>
              <Text style={{ color: filter === f.key ? '#fff' : colors.muted, fontSize: 13, fontWeight: '600' }}>
                {f.label}
              </Text>
            </Pressable>
          ))}
        </View>

        {keys.length === 0 && (
          <Text style={[styles.empty, { color: colors.muted }]}>条件に合う締切はありません。</Text>
        )}

        {keys.map((key) => (
          <View key={key} style={styles.group}>
            <View style={styles.groupHead}>
              <Text style={[styles.groupDate, { color: colors.text }]}>
                {key === 'none' ? '日付未確定' : `${formatDate(key)}（${weekday(key)}）`}
              </Text>
              {key !== 'none' && (
                <Text
                  style={[
                    styles.groupRel,
                    { color: key < today ? colors.danger : key === today ? colors.accent : colors.muted },
                  ]}>
                  {relativeLabel(key)}
                </Text>
              )}
            </View>
            {groups.get(key)!.map((item) => (
              <View key={item.id} style={[styles.item, { backgroundColor: colors.card, borderColor: colors.line }]}>
                <Text style={[styles.time, { color: colors.muted }]}>{item.time || '終日'}</Text>
                <View style={styles.itemBody}>
                  <Text style={[styles.itemTitle, { color: colors.text }]}>{item.title}</Text>
                  <View style={styles.badges}>
                    <Badge
                      text={item.source_label}
                      tone={item.source === 'email' ? 'blue' : item.source === 'navi' ? 'amber' : 'purple'}
                    />
                    {item.bucket === 'candidate' && <Badge text="追加候補" tone="gray" />}
                    {item.important && <Badge text="重要" tone="red" />}
                    {item.conflict && <Badge text={`ナビ ${formatDate(item.conflict.navi)}`} tone="amber" />}
                  </View>
                  {!!item.notes && (
                    <Text style={[styles.note, { color: colors.muted }]}>{item.notes}</Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 16, paddingBottom: 40, gap: 8 },
  title: { fontSize: 26, fontWeight: '700' },
  meta: { fontSize: 12 },
  filters: { flexDirection: 'row', gap: 6, marginTop: 6, marginBottom: 4 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999, borderWidth: StyleSheet.hairlineWidth },
  empty: { fontSize: 13, marginTop: 20, textAlign: 'center' },
  group: { gap: 6, marginTop: 8 },
  groupHead: { flexDirection: 'row', alignItems: 'baseline', gap: 8 },
  groupDate: { fontSize: 15, fontWeight: '700' },
  groupRel: { fontSize: 12 },
  item: { flexDirection: 'row', gap: 10, borderWidth: StyleSheet.hairlineWidth, borderRadius: 12, padding: 11 },
  time: { fontSize: 12, width: 46, paddingTop: 2 },
  itemBody: { flex: 1, gap: 4 },
  itemTitle: { fontSize: 14.5, fontWeight: '600' },
  badges: { flexDirection: 'row', gap: 5, flexWrap: 'wrap' },
  note: { fontSize: 12 },
});
