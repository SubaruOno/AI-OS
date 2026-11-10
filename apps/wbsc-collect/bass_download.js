// BASS（U-23 の入力画面 https://japanu23.s.bacs.ooo/input/）で、今大会のチーム（名前が「_u23_26」で終わる）の試合を
// 1つの JSON にまとめてダウンロードする。Chrome でログイン済みの入力画面を開き、ページの JS として流す。
// ファイルのダウンロードになるので、流す前にすばるの了承を取る（2026-11-10 に了承を得て1回流した。24試合・5,946球で約21.8MB）。
// 届いたファイルは ~/Downloads から ~/野球/U23ワールドカップ2026/05_収集データ/u23-wc-2026/bass/ に移し、
// python3 -I bass_json.py list / export で試合ごとの書き出しにする。
const m = [...document.querySelectorAll('*')].find(e => e.__vue__).__vue__.$root.$master;
try { await m.sync('game'); } catch (e) {}
try { await m.sync('gamedata'); } catch (e) {}
const teams = (await m.findFrom('team', {selector: {_id: {$gt: null}}, limit: 1000})).docs;
const u23ids = new Set(teams.filter(t => /_u23_26/.test(t.name || '')).map(t => t._id));
const allGames = (await m.findFrom('game', {selector: {_id: {$gt: null}}, limit: 5000})).docs;
const mine = allGames.filter(x => u23ids.has(x.first_team_id) || u23ids.has(x.second_team_id))
  .sort((a, b) => String(a.game_num).localeCompare(String(b.game_num)));
const gd = [];
for (const x of mine) {
  const d = await m.findFrom('gamedata', {selector: {game_id: x._id, page: {$gte: 0}}, use_index: 'gamedata', limit: 5000});
  gd.push(...(d.docs || d));
}
const teamIds = new Set();
mine.forEach(x => { teamIds.add(x.first_team_id); teamIds.add(x.second_team_id); });
const refIds = new Set();
gd.forEach(r => {
  for (const k of ['pitcher', 'batter', 'catcher']) if (r[k] && r[k].id) refIds.add(r[k].id);
  const ru = r.runner || {};
  for (const b of Object.keys(ru)) if (ru[b] && ru[b].id) refIds.add(ru[b].id);
});
const players = (await m.findFrom('player', {selector: {_id: {$gt: null}}, limit: 30000})).docs
  .filter(p => teamIds.has(p.team_id) || refIds.has(p._id));
const balltypes = (await m.findFrom('balltype', {selector: {_id: {$gt: null}}, limit: 500})).docs;
const obj = {
  meta: {exported_at: new Date().toISOString(), source: 'japanu23.s.bacs.ooo/input',
         what: 'U-23 2026 (_u23_26 teams) games, all gamedata pages, teams, players, balltypes'},
  teams: teams.filter(t => teamIds.has(t._id)), games: mine, gamedata: gd, players, balltypes,
};
const text = JSON.stringify(obj);
const day = new Date().toISOString().slice(0, 10).replace(/-/g, '');
const a = document.createElement('a');
a.href = URL.createObjectURL(new Blob([text], {type: 'application/json'}));
a.download = `bass_u23_2026_all_${day}.json`;
document.body.appendChild(a); a.click(); a.remove();
JSON.stringify({bytes: new Blob([text]).size, games: mine.length, gamedata: gd.length, teams: obj.teams.length, players: players.length});
