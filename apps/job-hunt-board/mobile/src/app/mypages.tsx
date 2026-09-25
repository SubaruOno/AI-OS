import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { MypageSite, Mypages, loadMypages } from '@/lib/feed';
import { useColors } from '@/lib/theme';
import { Badge } from '@/lib/ui';

type Filter = 'all' | 'withId';

export default function MypagesScreen() {
  const colors = useColors();
  const [data, setData] = useState<Mypages | null>(null);
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>('all');

  const refresh = useCallback(async () => {
    setLoading(true);
    const result = await loadMypages();
    setData(result.mypages);
    setLive(result.live);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const sites = useMemo(() => {
    const list = data?.sites ?? [];
    const filtered = filter === 'withId' ? list.filter((s) => s.login_id) : list;
    return [...filtered].sort((a, b) => {
      if (!!b.login_id !== !!a.login_id) return a.login_id ? -1 : 1;
      const unknownA = /^[（(【]/.test(a.company || '');
      const unknownB = /^[（(【]/.test(b.company || '');
      if (unknownA !== unknownB) return unknownA ? 1 : -1;
      return (a.company || '').localeCompare(b.company || '', 'ja');
    });
  }, [data, filter]);

  if (!data) {
    return (
      <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
        <ActivityIndicator style={{ marginTop: 80 }} />
      </SafeAreaView>
    );
  }

  const total = data.sites.length;
  const withId = data.sites.filter((s) => s.login_id).length;

  const open = (site: MypageSite) => {
    const url = site.login_url || site.home_url;
    if (url) Linking.openURL(url);
  };

  const copyId = (site: MypageSite) => {
    Share.share({ message: site.login_id });
  };

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={refresh} />}>
        <Text style={[styles.title, { color: colors.text }]}>マイページ</Text>
        <Text style={[styles.meta, { color: colors.muted }]}>
          {total}社 ・ ID {withId}件 ・ {live ? 'サーバーから取得' : '同梱データ'} ・{' '}
          {data.collected_at.replace('T', ' ').slice(5, 16)}
        </Text>

        <View style={styles.filters}>
          {(['all', 'withId'] as Filter[]).map((key) => {
            const selected = filter === key;
            return (
              <Pressable
                key={key}
                onPress={() => setFilter(key)}
                style={[
                  styles.chip,
                  { borderColor: colors.line, backgroundColor: selected ? colors.accent : colors.card },
                ]}>
                <Text style={{ color: selected ? '#fff' : colors.text, fontSize: 12, fontWeight: '600' }}>
                  {key === 'all' ? 'すべて' : 'IDあり'}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {sites.map((site) => (
          <View key={site.key} style={[styles.card, { backgroundColor: colors.card, borderColor: colors.line }]}>
            <View style={styles.cardHead}>
              <Text style={[styles.company, { color: colors.text }]}>{site.company}</Text>
              <Badge text={site.ats_label} tone={site.login_id ? 'blue' : 'gray'} />
            </View>

            {site.login_id ? (
              <Pressable onPress={() => copyId(site)} style={styles.idRow}>
                <Text style={[styles.id, { color: colors.text }]} selectable>
                  {site.login_id}
                </Text>
                <Text style={[styles.hint, { color: colors.muted }]}>タップで共有</Text>
              </Pressable>
            ) : (
              <Text style={[styles.hint, { color: colors.muted }]}>IDは未収集</Text>
            )}

            {!!site.note && (
              <Text style={[styles.note, { color: colors.muted }]}>・{site.note}</Text>
            )}

            <Pressable onPress={() => open(site)} style={styles.openRow}>
              <Text style={[styles.openText, { color: colors.accent }]} numberOfLines={1}>
                {site.login_url || site.home_url}
              </Text>
            </Pressable>
          </View>
        ))}

        <Text style={[styles.footer, { color: colors.muted }]}>{data.note}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 16, paddingBottom: 40, gap: 8 },
  title: { fontSize: 26, fontWeight: '700' },
  meta: { fontSize: 12 },
  filters: { flexDirection: 'row', gap: 8, marginVertical: 6 },
  chip: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6 },
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 14, padding: 12, gap: 6 },
  cardHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  company: { fontSize: 15, fontWeight: '700', flexShrink: 1 },
  idRow: { flexDirection: 'row', alignItems: 'baseline', gap: 8 },
  id: { fontSize: 17, fontWeight: '600', fontVariant: ['tabular-nums'] },
  hint: { fontSize: 11 },
  note: { fontSize: 12, lineHeight: 18 },
  openRow: { paddingTop: 2 },
  openText: { fontSize: 12 },
  footer: { fontSize: 11, lineHeight: 17, marginTop: 12 },
});
