#!/usr/bin/env python3
# c0886: "frontend design skill" reel. Orange Claude accent.
# Beat 1 = before/after website swap on the two "this" words (user's key request).
import json, re, html, sys
A="#f0813f"; AB="#ffa766"; AD="rgba(240,129,63,0.45)"; GL="rgba(240,129,63,0.16)"
RED="#ff5470"; GREY="#8b938e"
d=json.load(open(sys.argv[1] if len(sys.argv)>1 else "../edit/tT/transcripts/cutT.json"))
WS=[w for w in d["words"] if w.get("type")=="word" and w.get("start") is not None]
TOTAL=37.28
def W(i): return round(WS[i]["start"],2)
def esc(s): return html.escape(s)
def eb(e): return f'<div class="eyebrow"><span class="ebdot"></span>{esc(e)}</div>' if e else ""
def js_s(s): return json.dumps(s)

# sanity: verify anchor words are what we expect
EXPECT={6:"this",8:"this",10:"sixty",16:"Just",19:"front-end",24:"/frontendesign,",31:'"Redesign',
        40:"Linear.",41:"Don't",51:'makeover,"',55:"Enter.",57:"Claude",65:"front-end",69:"redesign",
        73:"And",89:"skills",96:"completely",98:"free."}
for i,t in EXPECT.items():
    assert t.lower() in WS[i]["text"].lower() or WS[i]["text"].lower() in t.lower(), f"word {i}: {WS[i]['text']} != {t}"

THIS1=W(6); THIS2=W(8); SIXTY=W(10)
B=[0.0, W(16), W(25), W(52), W(56), W(73), TOTAL]   # 6 beats

PROMPT1="Redesign my entire frontend in the theme of Linear."
PROMPT2=" Don't stop until you have given the entire software a makeover."

UGLY=(f'<div class="bwin ugly" id="ug">'
      f'<div class="bbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
      f'<span class="burl">my-old-site.com</span></div>'
      f'<div class="ubody">'
      f'<div class="umarq">*** WELCOME TO MY WEBSITE !!! ***</div>'
      f'<div class="uhead">BEST Company Inc.</div>'
      f'<div class="unav"><u>Home</u> | <u>About&nbsp;Us</u> | <u>Products</u> | <u>Contact!!</u></div>'
      f'<div class="urow"><div class="uimg">&#10060;<br>img_final2.jpg</div>'
      f'<div class="utext">We are the <font color="red"><b>BEST</b></font> company since 1997. '
      f'Click <u>HERE</u> to learn more about our GREAT services!!!</div></div>'
      f'<div class="ubtn">&gt;&gt;&gt; CLICK ME NOW &lt;&lt;&lt;</div>'
      f'</div></div>')

CLEAN=(f'<div class="bwin clean" id="cl">'
       f'<div class="bbar dark"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
       f'<span class="burl dark">yoursite.com</span></div>'
       f'<div class="cbody">'
       f'<div class="cnav"><span class="clogo"></span><span class="cbrand">Nova</span>'
       f'<span class="cnavlinks">Product&nbsp;&nbsp;&nbsp;Pricing&nbsp;&nbsp;&nbsp;Docs</span></div>'
       f'<div class="cglow"></div>'
       f'<div class="chead">Build better<br>software, faster.</div>'
       f'<div class="csub">The platform your team actually wants to use.</div>'
       f'<div class="cbtnrow"><span class="cbtn">Start free</span><span class="cbtn ghost">Book a demo</span></div>'
       f'</div></div>')

BEATS_HTML=[
 # 0 beforeafter
 (f'<div class="stack">{UGLY}{CLEAN}<div class="chip swapchip" id="sc0">60 SECONDS · 1 CLAUDE PROMPT</div></div>'),
 # 1 skillcard
 (f'{eb("THE SKILL")}<div class="strow"><div class="numbadge" id="nb1">&gt;_</div>'
  f'<div class="skname" id="sk1">FRONTEND<br>DESIGN</div></div>'
  f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
  f'<span class="wtitle">claude</span></div>'
  f'<div class="wbody term short"><div class="tprompt">&rsaquo;&nbsp;<span class="tcmd" id="cmd1"></span><span class="cur">&#9611;</span></div></div></div>'),
 # 2 promptcard
 (f'{eb("THE EXACT PROMPT")}'
  f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
  f'<span class="wtitle">claude</span></div>'
  f'<div class="wbody term tall"><div class="tprompt wrap">&rsaquo;&nbsp;<span class="tcmd" id="cmd2"></span><span class="cur">&#9611;</span></div></div></div>'
  f'<div class="lpill" id="lp2"><span class="ldot"></span>LINEAR</div>'),
 # 3 enterkey
 (f'<div class="keywrap"><div class="keycap" id="kc3">ENTER&nbsp;&#9166;</div></div>'),
 # 4 claudecard
 (f'{eb("CLAUDE TAKES OVER")}<div class="chwrap">'
  f'<img src="assets/logos/claude.svg" class="cclogo" id="cl4"/>'
  f'<div class="ghchip" id="gc4">frontend-design</div>'
  f'<div class="rgstamp" id="rs4">FULL REDESIGN</div></div>'),
 # 5 cta
 (f'<div class="kw" id="ck5">COMMENT<br><span class="acc">&ldquo;SKILLS&rdquo;</span></div>'
  f'<div class="ctasub" id="cu5">&rarr; ALL MY CLAUDE SKILLS</div>'
  f'<div class="ghchip free" id="fr5">100% FREE</div>'
  f'<div class="meter"><span id="mt5"></span></div>'),
]
KINDS=["beforeafter","skillcard","promptcard","enterkey","claudecard","ctacomment"]

clips=[];tw=[]
for i,inner_html in enumerate(BEATS_HTML):
    s,e=B[i],B[i+1]; dur=e-s
    clips.append(f'<div class="beat" id="beat{i}" data-start="{s}" data-duration="{dur:.2f}" data-track-index="{i+2}">'
                 f'<div class="inner {KINDS[i]}" id="in{i}">{inner_html}</div></div>')
    js=[f'tl.fromTo("#beat{i}",{{opacity:0,y:30,scale:0.97}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"power3.out"}},{s:.2f});']
    if i==0:
        # ugly site pops on "this"#1
        js.append(f'tl.fromTo("#ug",{{opacity:0,scale:0.7,y:40}},{{opacity:1,scale:1,y:0,duration:0.3,ease:"back.out(1.7)"}},{THIS1-0.05:.2f});')
        # clean site swaps in on "this"#2; ugly drops away
        js.append(f'tl.to("#ug",{{opacity:0,scale:0.82,y:50,rotation:-4,duration:0.3,ease:"power2.in"}},{THIS2-0.05:.2f});')
        js.append(f'tl.fromTo("#cl",{{opacity:0,scale:0.7,y:-40}},{{opacity:1,scale:1,y:0,duration:0.32,ease:"back.out(1.7)"}},{THIS2-0.02:.2f});')
        js.append(f'tl.fromTo("#sc0",{{opacity:0,scale:0.7,y:16}},{{opacity:1,scale:1,y:0,duration:0.28,ease:"back.out(2)"}},{SIXTY:.2f});')
    if i==1:
        js.append(f'tl.fromTo("#nb1",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk1",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{max(s+0.1,W(19)-0.25):.2f});')
        cmd="/frontend-design"
        js.append(f'var c1={js_s(cmd)};tl.to({{n:0}},{{n:c1.length,duration:1.3,ease:"none",onUpdate:function(){{document.getElementById("cmd1").textContent=c1.slice(0,Math.round(this.targets()[0].n));}}}},{W(24)-0.15:.2f});')
    if i==2:
        t1s=W(31)-0.1; t1d=(W(40)-0.4)-t1s          # type sentence 1, finish before "Linear." is spoken
        t2s=W(41); t2d=(W(51)+0.5)-t2s              # type sentence 2 across its spoken window
        js.append(f'var p1={js_s(PROMPT1)};tl.to({{n:0}},{{n:p1.length,duration:{t1d:.2f},ease:"none",onUpdate:function(){{document.getElementById("cmd2").textContent=p1.slice(0,Math.round(this.targets()[0].n));}}}},{t1s:.2f});')
        js.append(f'var p2={js_s(PROMPT2)};tl.to({{n:0}},{{n:p2.length,duration:{t2d:.2f},ease:"none",onUpdate:function(){{document.getElementById("cmd2").textContent=p1+p2.slice(0,Math.round(this.targets()[0].n));}}}},{t2s:.2f});')
        js.append(f'tl.fromTo("#lp2",{{opacity:0,scale:0.6,y:14}},{{opacity:1,scale:1,y:0,duration:0.3,ease:"back.out(2)"}},{W(40):.2f});')
    if i==3:
        js.append(f'tl.fromTo("#kc3",{{opacity:0,scale:1.5}},{{opacity:1,scale:1,duration:0.22,ease:"power3.out"}},{s+0.03:.2f});')
        js.append(f'tl.to("#kc3",{{y:16,boxShadow:"0 4px 0 #7a3c14, 0 0 40px rgba(240,129,63,0.5)",duration:0.1,ease:"power2.in"}},{W(55):.2f});')
        js.append(f'tl.to("#kc3",{{y:0,boxShadow:"0 18px 0 #7a3c14, 0 0 60px rgba(240,129,63,0.4)",duration:0.16,ease:"back.out(3)"}},{W(55)+0.12:.2f});')
    if i==4:
        js.append(f'tl.fromTo("#cl4",{{opacity:0,scale:0.5,rotate:-14}},{{opacity:1,scale:1,rotate:0,duration:0.4,ease:"back.out(1.8)"}},{W(57)-0.1:.2f});')
        js.append(f'tl.fromTo("#gc4",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{W(65):.2f});')
        js.append(f'tl.fromTo("#rs4",{{opacity:0,scale:1.5,rotate:-8}},{{opacity:1,scale:1,rotate:-4,duration:0.3,ease:"back.out(2)"}},{W(69):.2f});')
    if i==5:
        js.append(f'tl.fromTo("#ck5",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{W(89)-0.3:.2f});')
        js.append(f'tl.fromTo("#cu5",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.26,ease:"power3.out"}},{W(89)+0.2:.2f});')
        js.append(f'tl.fromTo("#fr5",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2.2)"}},{W(98):.2f});')
        js.append(f'tl.fromTo("#mt5",{{scaleX:0}},{{scaleX:1,duration:1.2,ease:"power2.out"}},{s+0.4:.2f});')
    if i<len(BEATS_HTML)-1:
        js.append(f'tl.to("#beat{i}",{{opacity:0,duration:0.16,ease:"power2.in"}},{e-0.16:.2f});')
    tw.append("\n      ".join(js))

NP=22
parts_html="".join(f'<span class="pt" id="pt{k}" style="left:{(k*131+40)%1040}px;top:{(k*97+30)%760}px;width:{5+(k%3)*3}px;height:{5+(k%3)*3}px;opacity:{0.12+0.2*((k*7)%5)/5:.2f}"></span>' for k in range(NP))
streaks_html="".join(f'<span class="stk" id="stk{k}" style="top:{120+k*230}px"></span>' for k in range(3))
bg=['tl.to("#glow",{x:120,y:30,scale:1.15,duration:6,yoyo:true,repeat:9,ease:"sine.inOut"},0);',
    'tl.to("#grid",{backgroundPosition:"0px 110px",duration:6,ease:"none",repeat:9},0);']
for k in range(NP):
    dur=4+(k%5)
    bg.append(f'tl.to("#pt{k}",{{y:-{120+(k%4)*60},duration:{dur},ease:"none",repeat:{int(60/dur)+1}}},0);')
    bg.append(f'tl.to("#pt{k}",{{opacity:0,duration:{dur},yoyo:true,repeat:{int(60/dur)+1},ease:"sine.inOut"}},0);')
for k in range(3):
    bg.append(f'tl.fromTo("#stk{k}",{{x:-1200}},{{x:1200,duration:{5+k*2},ease:"none",repeat:9}},{k*1.5});')

HTML=f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:"Montserrat","Inter",sans-serif}}
#root{{position:relative;width:1080px;height:1920px}}
#bgz{{position:absolute;top:0;left:0;width:1080px;height:864px;overflow:hidden}}
#grid{{position:absolute;inset:-40px;background-image:linear-gradient(rgba(240,129,63,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(240,129,63,0.05) 1px,transparent 1px);background-size:110px 110px}}
#glow{{position:absolute;top:120px;left:280px;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(240,129,63,0.24),transparent 65%);filter:blur(22px)}}
.pt{{position:absolute;border-radius:50%;background:{A};box-shadow:0 0 12px {A}}}
.stk{{position:absolute;left:0;width:520px;height:2px;background:linear-gradient(90deg,transparent,{A},transparent);opacity:0.3}}
.beat{{position:absolute;top:0;left:0;width:1080px;height:864px}}
.inner{{position:absolute;top:46px;left:60px;right:60px;height:740px;display:flex;flex-direction:column;justify-content:center;gap:22px}}
.eyebrow{{color:{A};font-size:32px;font-weight:800;letter-spacing:6px;text-transform:uppercase;display:flex;align-items:center;gap:13px}}
.ebdot{{width:14px;height:14px;border-radius:50%;background:{A};box-shadow:0 0 14px {A}}}
/* before/after */
.inner.beforeafter{{align-items:center;justify-content:center}}
.stack{{position:relative;width:940px;height:700px;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.bwin{{position:absolute;top:60px;left:0;width:940px;border-radius:22px;overflow:hidden;opacity:0}}
.bbar{{display:flex;align-items:center;gap:12px;background:#d8d8d8;padding:14px 20px}}
.bbar.dark{{background:#17171c}}
.burl{{margin-left:14px;background:#fff;color:#555;font-size:24px;font-weight:600;border-radius:9px;padding:4px 18px;font-family:ui-monospace,Menlo,monospace}}
.burl.dark{{background:#26262e;color:#b9b9c6}}
.td{{width:16px;height:16px;border-radius:50%}}.td.r{{background:#ff5f57}}.td.y{{background:#febc2e}}.td.g{{background:#28c840}}
.bwin.ugly{{border:3px solid #999;box-shadow:0 0 34px rgba(255,84,112,0.25)}}
.ubody{{background:#f7e977;padding:26px 30px;font-family:"Comic Sans MS","Chalkboard SE",cursive;text-align:center}}
.umarq{{color:#d40000;font-size:26px;font-weight:700;letter-spacing:2px}}
.uhead{{color:#0000cc;font-size:52px;font-weight:700;text-shadow:2px 2px 0 #ff00ff;margin-top:6px}}
.unav{{color:#0000ee;font-size:24px;margin-top:8px}}
.urow{{display:flex;gap:20px;margin-top:18px;align-items:center}}
.uimg{{flex:0 0 240px;height:150px;background:#fff;border:2px dashed #888;color:#c00;font-size:22px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:"Times New Roman",serif}}
.utext{{color:#222;font-size:24px;text-align:left;line-height:1.35;font-family:"Times New Roman",serif}}
.utext u{{color:#0000ee}}
.ubtn{{display:inline-block;margin-top:20px;background:#00a800;color:#ff0;font-size:28px;font-weight:700;padding:12px 26px;border:4px outset #7bd87b}}
.bwin.clean{{border:3px solid {AD};box-shadow:0 0 48px rgba(240,129,63,0.35)}}
.cbody{{position:relative;background:#0b0b0f;padding:30px 40px 40px;overflow:hidden;font-family:"Helvetica Neue","Inter",sans-serif}}
.cglow{{position:absolute;top:-120px;right:-100px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(240,129,63,0.35),transparent 65%);filter:blur(10px)}}
.cnav{{display:flex;align-items:center;gap:14px}}
.clogo{{width:22px;height:22px;border-radius:7px;background:linear-gradient(135deg,{A},{AB});box-shadow:0 0 14px {A}}}
.cbrand{{color:#fff;font-size:27px;font-weight:700;letter-spacing:0.5px}}
.cnavlinks{{margin-left:auto;color:#8b8b98;font-size:22px}}
.chead{{position:relative;color:#fff;font-size:64px;font-weight:800;letter-spacing:-2px;line-height:1.04;margin-top:46px}}
.csub{{position:relative;color:#9a9aa8;font-size:27px;margin-top:18px}}
.cbtnrow{{position:relative;display:flex;gap:18px;margin-top:30px;justify-content:flex-start}}
.cbtn{{background:linear-gradient(135deg,{A},{AB});color:#1a0f06;font-size:25px;font-weight:800;border-radius:12px;padding:14px 30px;box-shadow:0 0 26px rgba(240,129,63,0.5)}}
.cbtn.ghost{{background:transparent;color:#c9c9d4;border:1px solid #3a3a44;box-shadow:none}}
.chip{{color:{A};font-size:38px;font-weight:800;text-transform:uppercase;border:2px solid {AD};border-radius:40px;padding:13px 30px;background:rgba(20,14,8,0.85);box-shadow:0 0 18px {GL}}}
.swapchip{{position:absolute;bottom:70px;opacity:0}}
/* skillcard */
.inner.skillcard{{align-items:stretch;justify-content:center}}
.strow{{display:flex;align-items:center;gap:26px}}
.numbadge{{color:#1a0f06;background:{A};font-size:52px;font-weight:900;border-radius:18px;padding:12px 24px;box-shadow:0 0 30px {A};font-family:ui-monospace,Menlo,monospace}}
.skname{{color:#fff;font-size:88px;font-weight:900;letter-spacing:-2px;line-height:0.95;text-transform:uppercase;text-shadow:0 0 26px {GL}}}
.win{{background:#0c0f0e;border:2px solid {AD};border-radius:22px;overflow:hidden;box-shadow:0 0 44px {GL}}}
.wbar{{display:flex;align-items:center;gap:12px;background:#161b19;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.wtitle{{color:#9aa29a;font-size:27px;font-weight:700;margin-left:10px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.wbody{{padding:26px 30px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.term.short{{min-height:130px}}
.term.tall{{min-height:430px}}
.tprompt{{color:#e7efe9;font-size:44px;font-weight:700}}
.tprompt.wrap{{white-space:pre-wrap;line-height:1.4;font-size:42px}}
.tcmd{{color:{AB}}}
.cur{{color:{A};animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
/* promptcard */
.inner.promptcard{{align-items:stretch;justify-content:center}}
.lpill{{align-self:center;display:flex;align-items:center;gap:16px;color:#fff;background:#1b1b22;border:2px solid #5e6ad2;border-radius:40px;padding:14px 34px;font-size:40px;font-weight:900;letter-spacing:2px;box-shadow:0 0 34px rgba(94,106,210,0.55);opacity:0}}
.ldot{{width:26px;height:26px;border-radius:8px;background:#5e6ad2;box-shadow:0 0 16px #5e6ad2}}
/* enterkey */
.inner.enterkey{{align-items:center;justify-content:center}}
.keywrap{{display:flex;align-items:center;justify-content:center}}
.keycap{{color:#fff;background:linear-gradient(180deg,#2a2a30,#1a1a1f);font-size:110px;font-weight:900;letter-spacing:2px;border-radius:34px;padding:50px 90px;border:3px solid {AD};box-shadow:0 18px 0 #7a3c14, 0 0 60px rgba(240,129,63,0.4);opacity:0}}
/* claudecard */
.inner.claudecard{{align-items:center;justify-content:center}}
.chwrap{{display:flex;flex-direction:column;align-items:center;gap:30px}}
.cclogo{{width:300px;height:300px;object-fit:contain;filter:drop-shadow(0 0 34px rgba(217,119,87,0.55))}}
.ghchip{{color:#1a0f06;background:{A};font-size:44px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:14px 34px;box-shadow:0 0 32px {A};font-family:ui-monospace,Menlo,monospace;opacity:0}}
.rgstamp{{color:#fff;background:transparent;border:4px solid #fff;font-size:64px;font-weight:900;text-transform:uppercase;border-radius:18px;padding:12px 36px;letter-spacing:1px;box-shadow:0 0 30px rgba(255,255,255,0.25);opacity:0}}
/* cta */
.inner.ctacomment{{align-items:center;justify-content:center;background:rgba(20,14,8,0.9);border:2px solid {A};border-radius:26px;padding:44px;box-shadow:0 0 46px {GL}}}
.kw{{color:#fff;font-size:108px;font-weight:900;line-height:0.98;letter-spacing:-2px;text-align:center;text-shadow:0 0 30px {GL}}}
.kw .acc{{color:{A};text-shadow:0 0 26px {A}}}
.ctasub{{color:{AB};font-size:44px;font-weight:800;text-transform:uppercase;margin-top:6px}}
.ghchip.free{{font-family:"Montserrat",sans-serif}}
.meter{{width:100%;height:26px;background:rgba(255,255,255,0.08);border-radius:14px;overflow:hidden;border:1px solid {AD};margin-top:14px}}
.meter span{{display:block;height:100%;width:100%;transform-origin:left;transform:scaleX(0);background:linear-gradient(90deg,{A},{AB});box-shadow:0 0 18px {A}}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.2f}" data-width="1080" data-height="1920">
  <div id="bgz" data-start="0" data-duration="{TOTAL:.2f}" data-track-index="0"><div id="grid"></div><div id="glow"></div>{streaks_html}{parts_html}</div>
  {"".join(clips)}
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
      {chr(10).join(bg)}
      {chr(10).join(tw)}
window.__timelines["main"]=tl;</script></body></html>'''
open("index.html","w").write(HTML)
print(f"c0886: {len(BEATS_HTML)} beats, total {TOTAL}s")
for i in range(len(BEATS_HTML)): print(f"  {B[i]:5.2f}-{B[i+1]:5.2f} {KINDS[i]}")
print(f"  swap: ugly@{THIS1} clean@{THIS2} chip@{SIXTY}")
