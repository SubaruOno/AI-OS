// アプリの入力ボタンが作るのと同じ形のページで短い試合を組み、191列のExcelに書き出す（選手名はテスト用）
import * as XLSX from '/Users/subaruono/Projects/TerakoyaAI/ShigabaseiOS/node_modules/xlsx/xlsx.mjs';
import * as fs from 'node:fs';
XLSX.set_fs(fs);
import { blank, type Page } from '/Users/subaruono/Projects/TerakoyaAI/ShigabaseiOS/lib/scoring/engine.ts';
import { COLUMN191_HEADERS, export191Game } from '/Users/subaruono/Projects/TerakoyaAI/ShigabaseiOS/lib/scoring/export191.ts';

const team=(id:string,name:string,p:string)=>[...[2,3,4,5,6,7,8,9,10].map((pos,i)=>({team_id:id,slot:i+1,position_id:pos,uniform_no:i+1,batting_hand:i%3===1?'L':'R',throwing_hand:'R',player_snapshot:{id:`${p}${i+1}`,name:`選手${p}${String(i+1).padStart(2,'0')}`,uniform_no:i+1}})),{team_id:id,slot:10,position_id:1,uniform_no:11,batting_hand:'R',throwing_hand:'R',player_snapshot:{id:`${p}P`,name:`選手${p}11`,uniform_no:11}}];
const lineup=[...team('away','対戦校(テスト)','B'),...team('home','滋賀大学(テスト)','A')];
let t=0;const pg=(x:Partial<Page>):Page=>({...blank(),pitch_type:'ストレート',course:[131,131],ball_speed:'138',time:`13:${String(10+Math.floor(t/2)).padStart(2,'0')}:${String((t++%2)*30).padStart(2,'0')}`,...x});
const R=(label:string,kind:string|number)=>({res:{label,kind}});
const bb=(x:number,y:number,feature=1,rank='B')=>({batted_ball:{x,y},feature,rank} as Partial<Page>);
const pages:Page[]=[
  // 1回表
  pg({...R('ボール','B'),course:[60,90]}),
  pg({...R('単打',1),...bb(95,120),catch_fielder:[7]}),                               // 打者 出塁
  pg({...R('ボール','B'),pitch_type:'スライダー',ra:{1:{to:2,steal:true} as any}}),     // 一走 二進（盗塁）
  pg({...R('凡打','out'),...bb(150,180),catch_fielder:[6,3],ra:{2:{back:true} as any}}), // 二走 残留、打者 アウト
  pg({...R('死球','hbp'),pitch_type:'カーブ'}),                                          // 二走 継続、打者 出塁
  pg({pitch_type:null,course:null,ball_speed:'',pickoff_throw_to:1,ra:{1:{out:true}}}),  // 一走 投手牽制死
  pg({...R('二塁打',2),...bb(210,90,3,'A'),catch_fielder:[9]}),                         // 二走 本進、打者 二進
  pg({...R('犠飛','sf'),...bb(130,60,2),catch_fielder:[8],ra:{0:{out:true},2:{to:3}}}), // 二走 三進、打者 アウト（3アウト）
  // 1回裏
  pg({...R('本塁打',4),...bb(60,40,2,'A')}),                                            // 打者 本進
  pg({...R('単打',1),...bb(170,110),catch_fielder:[8]}),
  pg({...R('単打',1),...bb(100,130),catch_fielder:[7]}),                                // 一走 二進
  pg({...R('凡打','out'),...bb(140,170),catch_fielder:[6,4,3],ra:{1:{out:true},2:{to:3}}}), // 一走 封殺、二走 三進、打者 アウト（併殺）
  pg({...R('ボール','B'),flags:['WP'],pitch_type:'フォーク',course:[130,250],ra:{3:{to:4}}}), // 三走 本進（暴投）
  pg({...R('見送','S'),pitch_type:'チェンジ'}),
  pg({...R('空振','S'),pitch_type:'スライダー'}),
  pg({...R('見送','S'),ra:{0:{out:true}}}),                                              // 見逃し三振（3アウト）
];
const game:any={id:'sample',display_game_number:'SAMPLE',game_date:'2026-10-01',game_time:'13:00',away_team_id:'away',home_team_id:'home',away_name:'対戦校(テスト)',home_name:'滋賀大学(テスト)',season:'秋季',kind:'リーグ戦',week:'1',day:'1',game_number:1,scorer:'テスト'};
const rows=export191Game(game,lineup as any,pages.map((page,i)=>({seq:i+1,page})),{});
const ws=XLSX.utils.aoa_to_sheet([COLUMN191_HEADERS as unknown as string[],...rows]);
const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,'試合記録');
const out=new URL('./191-sample-app-input.xlsx',import.meta.url).pathname;XLSX.writeFile(wb,out);
for(const r of rows)console.log(r[9],r[10],r[11],'|',r[45],'|一走',r[36],'二走',r[37],'三走',r[38],'打者',r[39],'|',r[12],'-',r[13],'|',r[17],r[18]);
