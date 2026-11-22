"""Add (or refresh) tap-to-open lineups on a week page.
usage: python3 -I tools/inject_lineups.py <slug>/week-N/index.html lu.json <a|b> "<label>"
lu.json is what tools/lineups_fetch.js returns (a = $kullz FF, b = Boy Men Feet Balls).
Prints "WEEK MISMATCH" and changes nothing if the page's week isn't ESPN's current week.
Idempotent: removes an earlier injection (between the LINEUPS markers) first."""
import json, re, sys, html as H

page, data, key, label = sys.argv[1:5]
h = open(page, encoding='utf-8').read()
h = re.sub(r'<!--LINEUPS-->.*?<!--/LINEUPS-->', '', h, flags=re.S)
L = json.load(open(data, encoding='utf-8'))[key]
wk = L['sc']
m = re.search(r'/week-(\d+)/', page.replace('\\', '/'))
if m and int(m.group(1)) != wk:
    print('WEEK MISMATCH page', m.group(1), 'espn', wk); sys.exit(0)
POS = {1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'D/ST'}
SLOT = {0: 'QB', 2: 'RB', 4: 'WR', 6: 'TE', 23: 'FLEX', 16: 'D/ST', 17: 'K', 20: 'BE', 21: 'IR'}
ORDER = [0, 2, 4, 6, 23, 16, 17, 20, 21]
norm = lambda s: re.sub(r'\s+', ' ', s).strip()

teams = {}
for tid, ros in L['ros'].items():
    rows = []
    for slot, name, pro, bye, inj, proj, act, pos in ros:
        flag = ''
        if bye == wk: flag = 'BYE'
        elif inj == 'OUT': flag = 'O'
        elif inj == 'INJURY_RESERVE': flag = 'IR'
        elif inj == 'DOUBTFUL': flag = 'D'
        elif inj == 'QUESTIONABLE': flag = 'Q'
        rows.append({'s': SLOT.get(slot, str(slot)), 'o': ORDER.index(slot) if slot in ORDER else 99,
                     'n': name, 'p': POS.get(pos, ''), 't': pro, 'f': flag,
                     'pr': proj, 'a': act})
    rows.sort(key=lambda r: r['o'])
    for r in rows: del r['o']
    teams[norm(L['tn'][tid])] = rows

payload = json.dumps({'label': label, 'teams': teams}, ensure_ascii=False).replace('</', '<\\/')

css = """
.lu-btn{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;margin-top:12px;padding:9px 12px;border-radius:12px;
  border:1px solid var(--line);background:color-mix(in srgb,var(--fg) 5%,transparent);color:var(--fg);font:600 14px/1 var(--cond);
  letter-spacing:.08em;text-transform:uppercase;cursor:pointer}
.lu-btn:hover{background:color-mix(in srgb,var(--accent) 14%,transparent)}
.lu-btn .ar{transition:transform .25s}.mu.lu-open .lu-btn .ar{transform:rotate(180deg)}
.lu{display:grid;grid-template-rows:0fr;transition:grid-template-rows .35s ease}
.mu.lu-open .lu{grid-template-rows:1fr}
.lu>div{overflow:hidden}
.lu-cols{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding-top:12px}
.games .mu.lu-open{grid-column:1/-1}
.mu{container-type:inline-size}
@container (max-width:560px){.lu-cols{grid-template-columns:1fr}}
.lu-team h4{margin:0 0 6px;font:400 20px/1.1 var(--display);letter-spacing:.04em;color:var(--accent2)}
.lu-row{display:grid;grid-template-columns:44px 1fr auto;gap:8px;align-items:baseline;padding:5px 0;border-top:1px solid var(--line);font-size:14px}
.lu-row .sl{font:600 12px/1 var(--cond);letter-spacing:.06em;color:var(--muted)}
.lu-row .nm{min-width:0}.lu-row .nm small{color:var(--muted);font-size:12px;margin-left:4px}
.lu-row .pt{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.lu-row .pt small{display:block;color:var(--muted);font-size:11px}
.lu-row.bench{opacity:.62}
.lu-sub{margin:10px 0 2px;font:600 11px/1 var(--cond);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.lu-f{display:inline-block;margin-left:6px;padding:1px 6px;border-radius:6px;font:700 11px/1.5 var(--cond);letter-spacing:.04em;
  background:color-mix(in srgb,var(--loss) 22%,transparent);color:var(--loss)}
.lu-f.q{background:color-mix(in srgb,var(--accent2) 22%,transparent);color:var(--accent2)}
.lu-so{margin:0 0 6px;font-size:13px;color:var(--muted)}.lu-so b{color:var(--fg);font-size:15px}
.lu-note{margin:10px 0 0;color:var(--muted);font-size:12px}
"""

js = r"""
(function(){
const D=JSON.parse(document.getElementById('lu-data').textContent);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm=s=>s.replace(/\s+/g,' ').trim();
const fl={BYE:'BYE',O:'OUT',IR:'IR',D:'DOUBTFUL',Q:'Q'};
function row(r,bench){
  const f=r.f?`<span class="lu-f${r.f==='Q'?' q':''}">${fl[r.f]}</span>`:'';
  const pr=r.pr==null?'–':Number(r.pr).toFixed(1);
  const sc=r.a!=null?`<small>scored ${Number(r.a).toFixed(1)}</small>`:'';
  return `<div class="lu-row${bench?' bench':''}"><span class="sl">${esc(r.s)}</span><span class="nm">${esc(r.n)}<small>${esc(r.p)} · ${esc(r.t)}</small>${f}</span><span class="pt">${pr}${sc}</span></div>`;
}
function team(name){
  const rs=D.teams[norm(name)]; if(!rs) return '';
  const st=rs.filter(r=>r.s!=='BE'&&r.s!=='IR'), be=rs.filter(r=>r.s==='BE'||r.s==='IR');
  const played=st.filter(r=>r.a!=null);
  const so=played.length?`<div class="lu-so">Scored so far: <b>${played.reduce((x,r)=>x+r.a,0).toFixed(1)}</b> · ${played.length} of ${st.length} starters played or playing</div>`:'';
  return `<div class="lu-team"><h4>${esc(name)}</h4>${so}${st.map(r=>row(r,false)).join('')}<div class="lu-sub">Bench</div>${be.map(r=>row(r,true)).join('')}</div>`;
}
document.querySelectorAll('.mu').forEach((mu,i)=>{
  const names=[...mu.querySelectorAll(':scope>.t>b')].map(b=>b.textContent);
  if(names.length!==2||!names.every(n=>D.teams[norm(n)])) return;
  const id='lu-'+i;
  const btn=document.createElement('button');
  btn.className='lu-btn';btn.type='button';btn.setAttribute('aria-expanded','false');btn.setAttribute('aria-controls',id);
  btn.innerHTML='Lineups <span class="ar" aria-hidden="true">▾</span>';
  const panel=document.createElement('div');panel.className='lu';panel.id=id;
  panel.innerHTML=`<div><div class="lu-cols">${team(names[0])}${team(names[1])}</div><p class="lu-note">ESPN projections per player. ${esc(D.label)}</p></div>`;
  mu.append(btn,panel);
  const toggle=()=>{const o=mu.classList.toggle('lu-open');btn.setAttribute('aria-expanded',o)};
  btn.addEventListener('click',e=>{e.stopPropagation();toggle()});
  mu.style.cursor='pointer';
  mu.addEventListener('click',e=>{if(e.target.closest('.lu'))return;toggle()});
});
})();
"""

block = ('<!--LINEUPS--><style>' + css + '</style>'
         '<script type="application/json" id="lu-data">' + payload + '</script>'
         '<script>' + js + '</script><!--/LINEUPS-->')
i = h.rfind('</body>')
h = h[:i] + block + h[i:]
open(page, 'w', encoding='utf-8').write(h)

# check: every matchup card's two teams have lineup data
names = re.findall(r'<div class="t"><b>(.*?)</b>', h)
missing = sorted({norm(H.unescape(n)) for n in names} - set(teams))
print(page, 'cards teams:', len({norm(H.unescape(n)) for n in names}), 'missing:', missing)
