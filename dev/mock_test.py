#!/usr/bin/env python3
"""Kör Hyllan lokalt mot påhittad Spotify-data och tar skärmdumpar (mobil + dator).
Användning: python3 dev/mock_test.py   -> skärmdumpar i /tmp/hyllan-test/
Kräver: pip install playwright && playwright install chromium
Bygg vidare: lägg till klick/steg i run() för det du vill testa."""
import json, asyncio, os, shutil
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = '/tmp/hyllan-test'; os.makedirs(OUT, exist_ok=True)
shutil.copy(os.path.join(ROOT, 'index.html'), OUT + '/index.html')
open(OUT + '/config.js', 'w').write("window.HYLLAN_CONFIG={lastfmKey:'TEST'};")

def img(c): return [{"url": f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><rect width='300' height='300' fill='%23{c}'/></svg>", "width": 300, "height": 300}]
ARTISTS = ["Kacey Musgraves", "Bon Iver", "Robyn"]
def alb(i, typ, total, c):
    return {"id": f"al{i}", "uri": f"spotify:album:al{i}", "name": f"Album {i}", "album_type": typ, "total_tracks": total,
            "release_date": "2026-0%d-01" % (i % 9 + 1), "images": img(c), "artists": [{"id": f"ar{i%3}".ljust(22, '0'), "name": ARTISTS[i % 3]}]}
ITEMS = []
for i, (typ, tot, c) in enumerate([("album", 12, "c96"), ("single", 3, "69c"), ("album", 4, "9c6"), ("album", 5, "c69"), ("single", 1, "666")]):
    a = alb(i, typ, tot, c)
    for n in range(tot):
        ITEMS.append({"added_at": "2026-05-0%dT00:00:00Z" % (i + 1), "item": {"id": f"t{i}_{n}", "uri": f"spotify:track:t{i}_{n}", "name": f"Låt {n+1}",
            "type": "track", "duration_ms": 200000, "track_number": n + 1, "disc_number": 1, "album": a, "artists": a["artists"]}})
# Fler listor för biblioteksläget: 2025 delar en låt med 2026 (ska räknas en gång), "Gubbrock" ska inte ingå.
EXTRA = []
for i, (typ, tot, c) in enumerate([("album", 6, "a5c"), ("single", 2, "5ac")], start=10):
    a = alb(i, typ, tot, c)
    for n in range(tot):
        EXTRA.append({"added_at": "2025-03-01T00:00:00Z", "item": {"id": f"t{i}_{n}", "uri": f"spotify:track:t{i}_{n}", "name": f"Låt {n+1}",
            "type": "track", "duration_ms": 200000, "track_number": n + 1, "disc_number": 1, "album": a, "artists": a["artists"]}})
PL_ITEMS = {"pl": ITEMS, "pl25": EXTRA + [ITEMS[-1]], "gr": ITEMS[:3]}
PLAYLISTS = [{"id": "pl", "name": "2026", "snapshot_id": "s1"}, {"id": "pl25", "name": "2025", "snapshot_id": "s1"}, {"id": "gr", "name": "Gubbrock", "snapshot_id": "s1"}]
DEVICES = [{"id": "pc", "name": "Dator", "type": "Computer", "is_active": True, "is_restricted": False}]

async def run(w, h, touch, prefix):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": w, "height": h}, has_touch=touch, is_mobile=touch)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: print("PAGEERR", e))
        async def route(r):
            u = r.request.url
            if "/me/playlists" in u: body = {"items": [{**p, "owner": {"id": "me"}, "items": {"total": len(PL_ITEMS[p["id"]])}} for p in PLAYLISTS], "next": None}
            elif "/items" in u and "/playlists/" in u:
                its = PL_ITEMS[u.split("/playlists/")[1].split("/")[0]]; body = {"items": its, "next": None, "total": len(its)}
            elif "/me/player/devices" in u: body = {"devices": DEVICES}
            elif "/me/player" in u and r.request.method == "GET": body = {"is_playing": True, "progress_ms": 60000, "device": DEVICES[0], "item": ITEMS[2]["item"]}
            elif u.endswith("/v1/me"): body = {"id": "me"}
            elif "/v1/artists/" in u: body = {"images": []}
            else: return await r.fulfill(status=204)
            await r.fulfill(status=200, content_type="application/json", body=json.dumps(body))
        await pg.route("https://api.spotify.com/**", route)
        await pg.route("https://ws.audioscrobbler.com/**", lambda r: r.fulfill(status=200, content_type="application/json",
                       headers={"Access-Control-Allow-Origin": "*"}, body='{"toptags":{"tag":[{"name":"pop","count":100}]}}'))
        await pg.goto(f"file://{OUT}/index.html")
        await pg.evaluate("""localStorage.setItem('access_token','x');localStorage.setItem('expires_at',String(Date.now()+1e7));
          localStorage.setItem('own_genres_v1',JSON.stringify({al0:{main:'Country',subs:['Americana'],t:1},al2:{main:'Pop',subs:['Electropop'],t:1}}))""")
        await pg.reload(); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{OUT}/{prefix}-start.png")
        await pg.evaluate("navigate({view:'genres'})"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"{OUT}/{prefix}-genrer.png")
        await pg.evaluate("openSettings()"); await pg.wait_for_timeout(300)
        btn = pg.get_by_text("Släng lokala ändringar")
        await btn.scroll_into_view_if_needed(); await pg.screenshot(path=f"{OUT}/{prefix}-installningar.png")
        await btn.click(); await pg.screenshot(path=f"{OUT}/{prefix}-slang1.png")
        await pg.get_by_text("Tryck igen").click(); await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"{OUT}/{prefix}-slang2.png")
        print(prefix, "kvar lokalt:", await pg.evaluate("localStorage.getItem('own_genres_v1')"))
        await pg.evaluate("closeSheet()"); await pg.wait_for_timeout(400)
        # Biblioteket: årslistorna som en
        await pg.evaluate("pickPlaylist('__lib__')"); await pg.wait_for_timeout(2500)
        print(prefix, "bibliotek:", await pg.evaluate("[plName(), tracks.length, albums.length, loose.length, curId]"))
        await pg.screenshot(path=f"{OUT}/{prefix}-bibliotek.png")
        await pg.evaluate("navigate({view:'playlists'})"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"{OUT}/{prefix}-spellistor.png")
        # Omstart: ska visa biblioteket direkt från IndexedDB
        await pg.reload(); await pg.wait_for_timeout(300)
        print(prefix, "efter omstart:", await pg.evaluate("[curId, tracks.length, localStorage.getItem('pl_cache_v1')]"))
        await b.close()

asyncio.run(run(390, 844, True, "mobil")); asyncio.run(run(1440, 900, False, "dator"))
print("Skärmdumpar i", OUT)
