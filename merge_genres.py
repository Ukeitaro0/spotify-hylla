#!/usr/bin/env python3
"""Slår ihop en export (stdin eller fil) med genres.json. Nyast per album vinner; tom genre = ta bort."""
import json, sys
src = json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)
cur = json.load(open('genres.json'))
added = changed = removed = skipped = 0
for k, v in src.items():
    if isinstance(v, list): v = {"main": v[0] if v else "", "subs": v[1:], "t": 0}
    old = cur.get(k)
    if old and old.get('t', 0) > v.get('t', 0): skipped += 1; continue
    if k.startswith('rate:'):                        # betyg 1–5 för album eller låt; 0 = ta bort
        if not v.get('r'):
            if k in cur: del cur[k]; removed += 1
            continue
        if old is None: added += 1
        elif old.get('r') != v['r']: changed += 1
        cur[k] = {"r": v['r'], "t": v.get('t', 0)}
        continue
    if k.startswith('artist:'):                      # "visa under artist" för en låt
        if not v.get('artist'):
            if k in cur: del cur[k]; removed += 1
            continue
        if old is None: added += 1
        elif old.get('artist') != v['artist']: changed += 1
        cur[k] = {"artist": v['artist'], "t": v.get('t', 0)}
        continue
    if not v.get('main') and not v.get('subs'):
        if k in cur: del cur[k]; removed += 1
        continue
    new = {"main": v.get('main', ''), "subs": v.get('subs', []), "t": v.get('t', 0)}
    if old is None: added += 1
    elif (old.get('main'), old.get('subs')) != (new['main'], new['subs']): changed += 1
    cur[k] = new
with open('genres.json', 'w') as f:
    f.write("{\n" + ",\n".join(f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}' for k, v in cur.items()) + "\n}\n")
print(f"nya {added}, ändrade {changed}, borttagna {removed}, äldre än befintliga (hoppade över) {skipped}, totalt {len(cur)}")
