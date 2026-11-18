# Hyllan – Robins egen musikapp ovanpå Spotify

Läs hela filen innan du gör något. Den sammanfattar allt från första chatten (nov 2026).

## Vad det är
- Ett eget "modernt iTunes"-gränssnitt för Robins Spotify-spellistor: album, artister, låtar, egna genrer/subgenrer.
- Webbapp (en enda `index.html`, vanilla JS, ingen byggprocess) på GitHub Pages: https://ukeitaro0.github.io/spotify-hylla/
- Används som hemskärmsapp på iPhone (Safari) och i webbläsare på Windows-dator. Bara Robin använder den.
- Ljudet spelas alltid i Spotify-appen (Spotify Connect via Web API). Hyllan är fjärrkontroll + bibliotek.

## Arbetssätt med Robin (viktigt)
- Svara på svenska, kort, punktat, ett steg i taget. Inga artiga följdfrågor på slutet.
- **Less is more.** Nya saker ska passa in i helheten utan att plottra. Bygg inte på feature efter feature.
- **Ta aldrig bort något utan Robins godkännande.** Föreslå i stället.
- **"Hela biblioteket" (läsa in alla ~716 spellistor, ~27 000 låtar) får INTE påbörjas utan uttryckligt OK från Robin.**
- Bolla och visa mockups (Design-artefakt) innan större omgörningar. Mockup-ritytan: https://claude.ai/artifact/PaU4zsNRs5qAQygsEepKwe
- Robin committar inte själv. Claude committar och pushar direkt till `main` (GitHub Pages bygger från main).

## Filer i repot
- `index.html` – hela appen (CSS + JS inline).
- `config.js` – Robins Last.fm-nyckel. **Skriv aldrig över den.**
- `genres.json` – egna genrer per album-id `{"<albumId>": {"main","subs":[],"t"}}` och artistval per låt `{"artist:<trackUri>": {"artist":{"id","name"},"t"}}`. `t` = tidsstämpel, nyast vinner.
- `merge_genres.py` – slår ihop en export Robin klistrar in: `python3 merge_genres.py export.json`. Commit:a sedan `genres.json`.
- `bump.sh` – kör före **varje** commit som ändrar index.html. Sätter `BUILD` i index.html + `version.json`; appen laddar om sig själv när versionen ändras. Versionen syns under ⚙︎.
- `version.json`, `manifest.json`, `apple-touch-icon.png`, `icon-*.png`, `icon.svg` – version och ikon.
- `dev/mock_test.py` – kör appen mot påhittad Spotify-data i Playwright och tar skärmdumpar (mobil 390×844 med touch, dator 1440×900). Testa alltid så innan push.

## Flöde för en ändring
1. Ändra `index.html` (Python-replace eller Edit). 2. Syntaxkolla JS: extrahera `<script>`-blocket och kör `node --check`.
3. Kör `dev/mock_test.py` (utöka med steg) och titta på skärmdumparna. 4. `./bump.sh`.
5. `git commit` (svensk commit-text) och `git -c push.negotiate=true push origin HEAD:main`.
6. Berätta för Robin vilken version (BUILD) det blev.
Genrer: Robin trycker ⚙︎ → Kopiera och klistrar in JSON i chatten → kör merge_genres.py → commit + push.

## Spotify-begränsningar (Development Mode, efter feb 2026)
- Kräver att Robin har Premium. Max 5 användare. Anropskvot delas per konto – var sparsam.
- Spellisteinnehåll bara för listor man äger/samarbetar på: `GET /playlists/{id}/items` (fältet heter `item`, inte `track`).
- Borttagna endpoints bl.a. `GET /artists` (flera), `GET /albums`, `GET /tracks`. `GET /artists/{id}` (en) finns kvar.
- Artistgenrer från Spotify är i praktiken tomma → egna genrer + Last.fm-förslag.
- 429: Retry-After går oftast INTE att läsa i webbläsaren (CORS). Därför: okänd väntetid = pausa ALLA Spotify-anrop 10 min (`blocked_until`), dubblas vid upprepning (max 4 h, `block_len`). `api()` frågar inte alls under spärr. Fram till 20261117 loopade appen var 2:a sekund på 429 (tusentals anrop) – får aldrig hända igen. Långa spärrar har rapporterats (~19 h).
- Artistbilder hämtas bara för rutor som syns (IntersectionObserver), max 24 i kö, 1,5 s paus.
- Scopes: playlist-read-private, playlist-read-collaborative, playlist-modify-private/public, user-read-playback-state, user-modify-playback-state. Nya scopes kräver att Robin loggar in igen.
- Client ID `60281313632147df82bb02cdd1691929`, redirect `https://ukeitaro0.github.io/spotify-hylla/` (PKCE, ingen secret).

## Hur appen är byggd (översikt)
- Navigering: `route` = {view, genre, sub, artist, tab}. Vyer: home, albums, artists, tracks, loose, genres, genre, artist, playlists, search. `navigate()` + history (bakåtgest fungerar).
- Mobil (<900 px): flikar längst ner (Bibliotek, Genrer, Spellistor, Sök). Dator (≥900 px): fast sidomeny (Bibliotek, Genrer med subgenrer, Spellistor med sök, fällbara, Inställningar fast längst ner).
- Album = `album_type` album/compilation och alla spår finns i listan. Övrigt = "Övriga låtar" (lösa låtar). Dubbletter (singel som också finns på album) märks.
- Genrer per album-id (huvudgenre + subgenrer). Lösa låtar får genre via sitt album-id. Last.fm visas bara på album utan egen genre (kan stängas av).
- Artister: rutnät med runda bilder (riktiga bilder hämtas en i taget, 0,7 s paus, cache 60 dagar), artistsida med Album / Låtar utanför album / Medverkar på. "Visa under artist" i ⋯-menyn flyttar en låt till en gästartist.
- Spelare: minispelare + stor spelare (blanda, upprepa, spola, byt enhet). Senast spelat sparas och kan återupptas.
- Enhetsval: telefon spelar på telefonens Spotify, dator på datorns. iPhone listar inte Spotify när appen sover → Hyllan öppnar `spotify:` och spelar när man kommer tillbaka.
- Bibliotek: valet "Årslistor 2012–2026" (`LIB = '__lib__'`) slår ihop alla listor som heter ett årtal ≥ 2012. Bara nya/ändrade listor (snapshot_id) läses, en sida i taget med paus, och det kan fortsätta nästa gång. Dubbletter mellan listor räknas en gång. "Ta bort ur spellistan" finns inte i biblioteket.
- Betyg 1–5 (stjärnor): per album-id och per låt-uri, låt utan eget ärver albumets, eget låtbetyg gäller. Synkas i `genres.json` som `"rate:<albumId|trackUri>": {"r","t"}` (r 0 = ta bort), samma Kopiera-flöde. Sätts i albumvyn (albumet + klickbara stjärnor per låt) och i ⋯-menyn. Filter "Alla betyg / ★3+ / ★4+ / ★5" (minst, sparas inte) bredvid sorteringen, plus sortering "Betyg". localStorage `ratings_v1`.
- Genreetiketter i albumvyn och stora spelaren är knappar (egna genrer, med ›) till genre-/subgenresidan i det som är valt nu. Last.fm-förslag är bara text. (Robin utvärderar, nov 2026.)
- Lagring: spellistornas innehåll i IndexedDB (`hyllan` → `pl`, en post per lista med snapshot). Gamla `pl_cache_v1` flyttas dit automatiskt. Övrigt i localStorage ( `own_genres_v1`, `artist_prefs_v1`, `artist_img_v1`, `last_played`, `my_device`, `side_closed`).

## Beslut som är tagna
- Mobil = flikar (förslag B), dator = sidomeny (D1). Gamla iTunes-kolumnbläddraren valdes bort.
- Ingen artistrad i genrevyn (Robin ville inte ha den). "Alla låtar" heter "Låtar".
- Genre syns inte på låtraderna.
- Alfabetsremsa bara i Artister (≥20 artister).
- Riktig iOS-app/egen CarPlay: inte värt det nu (kräver Mac + Apple-konto ~1 100 kr/år, CarPlay-behörighet osäker).

## Idéer på listan (inte påbörjade)
- Stiliserad illustration per genre på genrerutorna.
- CarPlay-genväg: Hyllan skapar/uppdaterar spellistor i Spotify per genre ("Hyllan · Country …") som används via Spotifys CarPlay.
- Titta närmare på hur låtraderna ska se ut (Robin återkommer).
- Hela biblioteket: steg 1 (årslistor) OK:at och byggt 2026-11-17. Robin går igenom genrer innan nästa steg. Nästa: genrelistorna (och frysboxen) som genreförslag, sedan artist-/albummappen. Topplistor/stämningslistor/Gillade låtar: inte nu.
- Genre per artist som standard (förslag, inte påbörjat).
