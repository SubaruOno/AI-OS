import { StyleSheet, Text, View } from 'react-native';

import { useColors } from './theme';

export const STAGE_COLORS = ['#9aa1ac', '#2f6fed', '#b3720a', '#7a4fd0', '#1f8a52'];
export const STAGE_COUNT = 5;

export function todayISO() {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function daysBetween(iso: string, base = todayISO()) {
  const [y1, m1, d1] = iso.split('-').map(Number);
  const [y2, m2, d2] = base.split('-').map(Number);
  const a = Date.UTC(y1, m1 - 1, d1);
  const b = Date.UTC(y2, m2 - 1, d2);
  return Math.round((a - b) / 86400000);
}

export function formatDate(iso: string) {
  const [, m, d] = iso.split('-').map(Number);
  return `${m}/${d}`;
}

export function weekday(iso: string) {
  const [y, m, d] = iso.split('-').map(Number);
  return '日月火水木金土'[new Date(y, m - 1, d).getDay()];
}

export function relativeLabel(iso: string) {
  const n = daysBetween(iso);
  if (n === 0) return '今日';
  if (n === 1) return '明日';
  if (n > 0) return `あと${n}日`;
  return `${-n}日過ぎている`;
}

export function StageBar({ rank }: { rank: number }) {
  const colors = useColors();
  const active = Math.max(0, Math.min(STAGE_COUNT, rank + 1));
  const color = STAGE_COLORS[Math.max(0, Math.min(STAGE_COUNT - 1, rank))];
  return (
    <View style={styles.bar}>
      {Array.from({ length: STAGE_COUNT }).map((_, i) => (
        <View
          key={i}
          style={[styles.segment, { backgroundColor: i < active ? color : colors.line }]}
        />
      ))}
    </View>
  );
}

export function Badge({ text, tone = 'gray' }: { text: string; tone?: 'gray' | 'blue' | 'amber' | 'purple' | 'red' | 'green' }) {
  return (
    <View style={[styles.badge, badgeTones[tone]]}>
      <Text style={[styles.badgeText, badgeTextTones[tone]]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: 'row', gap: 2, width: 46 },
  segment: { height: 6, flex: 1, borderRadius: 3 },
  badge: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderWidth: StyleSheet.hairlineWidth,
  },
  badgeText: { fontSize: 11, fontWeight: '600' },
});

const badgeTones = StyleSheet.create({
  gray: { backgroundColor: '#f1f2f4', borderColor: '#dfe2e7' },
  blue: { backgroundColor: '#eef4ff', borderColor: '#cddffd' },
  amber: { backgroundColor: '#fdf6ea', borderColor: '#f0dcb4' },
  purple: { backgroundColor: '#f5f1fe', borderColor: '#ddd0f7' },
  red: { backgroundColor: '#fdf1ef', borderColor: '#f4c9c3' },
  green: { backgroundColor: '#eefaf3', borderColor: '#bfe3cf' },
});

const badgeTextTones = StyleSheet.create({
  gray: { color: '#6b7280' },
  blue: { color: '#2f6fed' },
  amber: { color: '#b3720a' },
  purple: { color: '#6a3fc4' },
  red: { color: '#cf3f30' },
  green: { color: '#1f8a52' },
});
