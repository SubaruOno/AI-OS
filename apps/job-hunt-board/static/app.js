const $ = (id) => document.getElementById(id);
const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

let DATA = null;
let USER = {};
let view = { bucket: 'all', source: 'all', status: 'upcoming', range: null, query: '' };

function todayISO() {
  return new Date().toLocaleDateString('sv-SE');
}
function toDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}
function formatDate(iso) {
  const d = toDate(iso);
  return `${d.getMonth() + 1}/${d.getDate()}（${WEEKDAYS[d.getDay()]}）`;
}
function diffDays(iso) {
  return Math.round((toDate(iso) - toDate(todayISO())) / 86400000);
}
function relative(iso) {
  const n = diffDays(iso);
  if (n === 0) return { text: '今日', cls: 'today' };
  if (n === 1) return { text: '明日', cls: 'today' };
  if (n > 0) return { text: `あと${n}日`, cls: '' };
  return { text: `${-n}日過ぎている`, cls: 'overdue' };
}

function eff(item) {
  const u = USER[item.id];
  return u && u.status ? u.status : item.status;
}
function closed(status) {
  return status === 'done' || status === 'dismissed';
}
function isOverdue(item) {
  return !!item.date && diffDays(item.date) < 0 && !closed(eff(item));
}

function matches(item) {
  const st = eff(item);
  if (view.bucket === 'candidate' && item.bucket !== 'candidate') return false;
  if (view.source !== 'all' && item.source !== view.source) return false;
  if (view.query) {
    const hay = `${item.title} ${item.firm} ${item.notes}`.toLowerCase();
    if (!hay.includes(view.query.toLowerCase())) return false;
  }
  if (view.range === 'today') return item.date === todayISO() && !closed(st);
  if (view.range === 'week') {
    const d = item.date ? diffDays(item.date) : null;
    return d !== null && d >= 0 && d <= 6 && !closed(st);
  }
  if (view.range === 'overdue') return isOverdue(item);
  if (view.status === 'upcoming') {
    const d = item.date ? diffDays(item.date) : null;
    return d !== null && d >= 0 && !closed(st);
  }
  if (view.status === 'pending') return st === 'open' || st === 'missed';
  if (view.status === 'done') return st === 'done';
  if (view.status === 'dismissed') return st === 'dismissed';
  if (view.status === 'due') {
    const d = item.date ? diffDays(item.date) : null;
    return d !== null && d <= 0 && !closed(st);
  }
  return true;
}

async function setStatus(id, value) {
  USER[id] = { status: value };
  render();
  try {
    const res = await fetch('/api/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, value }),
    });
    const state = await res.json();
    if (state && state.items) USER = state.items;
  } catch (e) {
    console.warn('保存できませんでした', e);
  }
  render();
}

function badge(text, cls) {
  const span = document.createElement('span');
  span.className = 'badge' + (cls ? ' ' + cls : '');
  span.textContent = text;
  return span;
}

function renderItem(item) {
  const st = eff(item);
  const box = document.createElement('div');
  box.className = 'item s-' + item.source;
  if (st === 'done') box.classList.add('is-done');
  if (st === 'dismissed') box.classList.add('is-dismissed');
  if (isOverdue(item)) box.classList.add('is-overdue');

  const time = document.createElement('div');
  time.className = 'time';
  time.textContent = item.time || '終日';
  box.appendChild(time);

  const body = document.createElement('div');

  const title = document.createElement('div');
  title.className = 'title';
  title.textContent = item.title;
  body.appendChild(title);

  const badges = document.createElement('div');
  badges.className = 'badges';
  badges.appendChild(badge(item.source_label, 'b-' + item.source));
  if (item.bucket === 'candidate') badges.appendChild(badge('追加候補', 'b-candidate'));
  if (item.important) badges.appendChild(badge('重要', 'b-important'));
  if (item.conflict) {
    badges.appendChild(badge(`日付違い: ナビ ${formatDate(item.conflict.navi)}`, 'b-conflict'));
  }
  if (st === 'done') badges.appendChild(badge('対応済み', 'b-done'));
  if (st === 'missed') badges.appendChild(badge('未提出', 'b-missed'));
  if (st === 'declined') badges.appendChild(badge('不参加', 'b-declined'));
  if (st === 'dismissed') badges.appendChild(badge('見送り', 'b-declined'));
  body.appendChild(badges);

  if (item.notes) {
    const note = document.createElement('div');
    note.className = 'note';
    note.textContent = item.notes;
    body.appendChild(note);
  }
  box.appendChild(body);

  const actions = document.createElement('div');
  actions.className = 'actions';
  const doneBtn = document.createElement('button');
  doneBtn.type = 'button';
  doneBtn.textContent = '対応済み';
  if (st === 'done') doneBtn.classList.add('on');
  doneBtn.addEventListener('click', () => setStatus(item.id, st === 'done' ? 'open' : 'done'));
  const skipBtn = document.createElement('button');
  skipBtn.type = 'button';
  skipBtn.textContent = '見送り';
  if (st === 'dismissed') skipBtn.classList.add('on');
  skipBtn.addEventListener('click', () => setStatus(item.id, st === 'dismissed' ? 'open' : 'dismissed'));
  actions.appendChild(doneBtn);
  actions.appendChild(skipBtn);
  box.appendChild(actions);

  return box;
}

function renderSummary() {
  const items = DATA.items;
  let today = 0, week = 0, overdue = 0, done = 0;
  for (const item of items) {
    const st = eff(item);
    if (item.date === todayISO() && !closed(st)) today++;
    if (item.date) {
      const d = diffDays(item.date);
      if (d >= 0 && d <= 6 && !closed(st)) week++;
    }
    if (isOverdue(item)) overdue++;
    if (st === 'done') done++;
  }
  const tiles = [
    { key: 'today', label: '今日', n: today },
    { key: 'week', label: '7日以内', n: week },
    { key: 'overdue', label: '期限切れ・未対応', n: overdue, cls: overdue ? 'danger' : '' },
    { key: 'done', label: '対応済み', n: done, cls: 'ok' },
  ];
  const box = $('summary');
  box.textContent = '';
  for (const t of tiles) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'tile' + (t.cls ? ' ' + t.cls : '') + (view.range === t.key ? ' active' : '');
    const n = document.createElement('div');
    n.className = 'n';
    n.textContent = t.n;
    const l = document.createElement('div');
    l.className = 'l';
    l.textContent = t.label;
    btn.appendChild(n);
    btn.appendChild(l);
    btn.addEventListener('click', () => {
      if (view.range === t.key) {
        view.range = null;
      } else {
        view.range = t.key;
        view.status = 'all';
        $('f-status').value = view.status;
      }
      render();
    });
    box.appendChild(btn);
  }
}

function renderList() {
  const filtered = DATA.items.filter(matches);
  const list = $('list');
  list.textContent = '';
  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = '条件に合うものはありません。';
    list.appendChild(empty);
    return;
  }
  const groups = new Map();
  for (const item of filtered) {
    const key = item.date || 'none';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  const keys = [...groups.keys()].sort((a, b) => {
    if (a === 'none') return 1;
    if (b === 'none') return -1;
    return a < b ? -1 : 1;
  });
  for (const key of keys) {
    const day = document.createElement('section');
    day.className = 'day';
    const head = document.createElement('div');
    head.className = 'day-head';
    const dateEl = document.createElement('span');
    dateEl.className = 'day-date';
    dateEl.textContent = key === 'none' ? '日付未確定' : formatDate(key);
    head.appendChild(dateEl);
    if (key !== 'none') {
      const rel = relative(key);
      const relEl = document.createElement('span');
      relEl.className = 'day-rel' + (rel.cls ? ' ' + rel.cls : '');
      relEl.textContent = rel.text;
      head.appendChild(relEl);
    }
    day.appendChild(head);
    for (const item of groups.get(key)) day.appendChild(renderItem(item));
    list.appendChild(day);
  }
}

function renderPanels() {
  const rules = $('rules');
  rules.textContent = '';
  for (const rule of DATA.rules) {
    const li = document.createElement('li');
    li.textContent = rule.replace(/\*\*/g, '');
    rules.appendChild(li);
  }
  const applied = $('applied');
  applied.textContent = '';
  for (const text of DATA.applied) {
    const li = document.createElement('li');
    li.textContent = text;
    applied.appendChild(li);
  }
  const legend = $('legend');
  legend.textContent = '';
  if (DATA.legend && DATA.legend.length) {
    const intro = document.createElement('div');
    intro.textContent = '出典の区別';
    const ul = document.createElement('ul');
    for (const line of DATA.legend) {
      const li = document.createElement('li');
      li.textContent = line.replace(/\*\*/g, '');
      ul.appendChild(li);
    }
    legend.appendChild(intro);
    legend.appendChild(ul);
  }
}

function renderNotice() {
  const notice = $('notice');
  const warnings = (DATA.warnings || []).slice();
  if (DATA.error) warnings.unshift('元データを読めませんでした: ' + DATA.error);
  if (!warnings.length) {
    notice.hidden = true;
    return;
  }
  notice.hidden = false;
  notice.textContent = warnings.join(' / ');
}

function renderMeta() {
  const generated = DATA.generated_at.replace('T', ' ').slice(0, 16);
  const files = (DATA.sources || []).map((s) => s.split('/').pop()).join(' ・ ');
  $('meta').textContent = `元データ: ${files} ／ 取り込み ${DATA.items.length}件 ／ 解析 ${generated}`;
}

function render() {
  renderMeta();
  renderNotice();
  renderSummary();
  renderList();
  renderPanels();
}

async function load() {
  const res = await fetch('/api/data');
  DATA = await res.json();
  USER = DATA.state || {};
  render();
}

$('reload').addEventListener('click', load);
$('f-bucket').addEventListener('change', (e) => { view.bucket = e.target.value; render(); });
$('f-source').addEventListener('change', (e) => { view.source = e.target.value; render(); });
$('f-status').addEventListener('change', (e) => { view.status = e.target.value; view.range = null; render(); });
$('f-query').addEventListener('input', (e) => { view.query = e.target.value.trim(); render(); });
$('clear').addEventListener('click', () => {
  view = { bucket: 'all', source: 'all', status: 'upcoming', range: null, query: '' };
  $('f-bucket').value = 'all';
  $('f-source').value = 'all';
  $('f-status').value = 'upcoming';
  $('f-query').value = '';
  render();
});

load();
