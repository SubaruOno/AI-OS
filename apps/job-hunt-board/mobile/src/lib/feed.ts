import bundled from '@/assets/feed.json';
import bundledMypages from '@/assets/mypages.json';

export type Source = 'email' | 'navi' | 'mixed';

export type FeedItem = {
  id: string;
  date: string | null;
  time: string;
  title: string;
  firm: string;
  bucket: 'master' | 'candidate' | 'conflict';
  source: Source;
  source_label: string;
  notes: string;
  status: 'open' | 'done' | 'missed' | 'declined';
  status_label: string;
  important: boolean;
  conflict: { navi: string; email: string } | null;
};

export type Mail = {
  date: string;
  sender: string;
  subject: string;
  company: string;
  signal_rank: number | null;
  signal: string | null;
  url: string;
};

export type Company = {
  name: string;
  rank: number;
  score: number;
  stage: string;
  stage_rank: number;
  next: {
    date: string;
    time: string;
    title: string;
    source: Source;
    status: string;
    days_left: number;
    id: string;
  } | null;
  open_count: number;
  overdue_count: number;
  mail_count: number;
  mails: Mail[];
  items: string[];
};

export type Feed = {
  generated_at: string;
  today: string;
  mail_fetched_at: string | null;
  mail_count: number;
  companies: Company[];
  items: FeedItem[];
  rules: string[];
  applied: string[];
  legend: string[];
  warnings: string[];
  sources: string[];
};

export type MypageSite = {
  key: string;
  company: string;
  ats: string;
  ats_label: string;
  login_url: string;
  home_url: string;
  login_id: string;
  login_id_source: string;
  note: string;
  visits: number;
  last_seen: string;
};

export type Mypages = {
  collected_at: string;
  source: string;
  note: string;
  sites: MypageSite[];
};

/** 開発マシンで動いているサーバー。Simulator は Mac の 127.0.0.1 に届く。 */
export const SERVER_URL = 'http://127.0.0.1:8765/api/feed';
export const MYPAGE_SERVER_URL = 'http://127.0.0.1:8765/api/mypages';

export const bundledFeed = bundled as unknown as Feed;

export async function loadFeed(): Promise<{ feed: Feed; live: boolean }> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    const response = await fetch(SERVER_URL, { signal: controller.signal });
    clearTimeout(timer);
    if (response.ok) {
      const json = (await response.json()) as Feed;
      if (json && Array.isArray(json.companies)) return { feed: json, live: true };
    }
  } catch {
    // サーバーが無いときは同梱データを使う
  }
  return { feed: bundledFeed, live: false };
}

export const bundledMypagesData = bundledMypages as unknown as Mypages;

export async function loadMypages(): Promise<{ mypages: Mypages; live: boolean }> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    const response = await fetch(MYPAGE_SERVER_URL, { signal: controller.signal });
    clearTimeout(timer);
    if (response.ok) {
      const json = (await response.json()) as Mypages;
      if (json && Array.isArray(json.sites)) return { mypages: json, live: true };
    }
  } catch {
    // サーバーが無いときは同梱データを使う
  }
  return { mypages: bundledMypagesData, live: false };
}
