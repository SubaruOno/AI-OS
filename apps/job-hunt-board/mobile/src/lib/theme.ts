import { useColorScheme } from 'react-native';

const light = {
  background: '#f4f5f7',
  card: '#ffffff',
  text: '#1d2126',
  muted: '#6b7280',
  line: '#e3e6ea',
  accent: '#2f6fed',
  danger: '#cf3f30',
  gold: '#c99700',
};

const dark = {
  background: '#101214',
  card: '#1b1e22',
  text: '#f2f4f7',
  muted: '#9aa1ac',
  line: '#2b3037',
  accent: '#5b93ff',
  danger: '#ff7a6b',
  gold: '#e0b32a',
};

export function useColors() {
  const scheme = useColorScheme();
  return scheme === 'dark' ? dark : light;
}

/** StyleSheet の外でも使える固定値。暗いテーマでは画面側で useColors を使う。 */
export const Color = light;
