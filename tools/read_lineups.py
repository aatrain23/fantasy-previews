"""Turn the saved javascript_tool result from tools/lineups_fetch.js into lu.json.
usage: python3 -I tools/read_lineups.py <saved result file> <out lu.json>"""
import json, sys
t = open(sys.argv[1], encoding='utf-8').read()
try:  # the tool sometimes saves a JSON array of {type, text} parts
    a = json.loads(t)
    if isinstance(a, list): t = ''.join(x.get('text', '') for x in a if isinstance(x, dict))
except ValueError:
    pass
if '@@' not in t: sys.exit('no @@ marker in the result: ' + t[:200])
s = t[t.index('@@') + 2:]
if s.startswith('{\\"'):  # still JSON-quoted: decode the outer string literal first
    lit = json.JSONDecoder().raw_decode('"' + t.split('"', 1)[1])[0]
    s = lit[lit.index('@@') + 2:]
d = json.JSONDecoder().raw_decode(s)[0]
for k in 'ab':
    assert d[k]['ros'] and d[k]['games'], 'missing league ' + k
json.dump(d, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print('week', d['a']['sc'], d['b']['sc'], 'teams', len(d['a']['ros']), len(d['b']['ros']))
