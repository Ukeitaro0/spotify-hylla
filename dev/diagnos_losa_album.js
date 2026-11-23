// Diagnos: varför räknas album som lösa låtar?
// Klistra in i konsolen (F12) på https://ukeitaro0.github.io/spotify-hylla/ på datorn.
// Läser BARA den lokala cachen (IndexedDB 'hyllan' + localStorage). Gör inga Spotify-anrop.
(async () => {
  const db = await new Promise((ok, err) => { const r = indexedDB.open('hyllan', 1); r.onsuccess = () => ok(r.result); r.onerror = () => err(r.error); });
  const recs = await new Promise((ok, err) => { const q = db.transaction('pl').objectStore('pl').getAll(); q.onsuccess = () => ok(q.result); q.onerror = () => err(q.error); });
  const meta = new Map(JSON.parse(localStorage.getItem('pl_list_v1') || '[]').map(p => [p.id, p]));
  const name = id => meta.get(id)?.name || id;
  const isYear = id => { const n = (name(id) || '').trim(); return /^\d{4}$/.test(n) && +n >= 2012; };
  const norm = s => (s || '').toLowerCase().replace(/\s*[\(\[][^\)\]]*[\)\]]/g, '').replace(/\s+-\s+.*$/, '')
    .replace(/\b(deluxe|expanded|edition|remaster(ed)?|anniversary|version|special)\b/g, '').replace(/[^\p{L}\p{N}]+/gu, ' ').trim();

  // album-id -> { album, lists:Set, ids:Set(spår-id), nums:Set }
  const byAlbum = new Map(), byTitle = new Map();   // byTitle: artist+låttitel -> album-id:n
  recs.forEach(r => (r.items || []).forEach(({ t }) => {
    const a = t.album; if (!byAlbum.has(a.id)) byAlbum.set(a.id, { a, lists: new Set(), ids: new Set(), nums: new Set() });
    const g = byAlbum.get(a.id); g.lists.add(r.id); g.ids.add(t.id); g.nums.add(`${t.disc_number}-${t.track_number}`);
    const tk = (t.artists?.[0]?.id || '') + '|' + norm(t.name); (byTitle.get(tk) || byTitle.set(tk, new Set()).get(tk)).add(a.id);
  }));
  // Samma låt (artist + titel) på flera album-id = olika utgåvor (deluxe, återutgåva, annan marknad)
  const sib = new Map();
  byTitle.forEach(set => { if (set.size > 1) set.forEach(x => set.forEach(y => { if (x !== y) (sib.get(x) || sib.set(x, new Set()).get(x)).add(y); })); });
  // Samma artist + albumnamn som börjar likadant (Halcyon / Halcyon Days)
  const all = [...byAlbum.entries()];
  all.forEach(([x, gx]) => all.forEach(([y, gy]) => { if (x === y) return; const nx = norm(gx.a.name), ny = norm(gy.a.name);
    if (nx && ny && gx.a.artists?.[0]?.id === gy.a.artists?.[0]?.id && (ny.startsWith(nx + ' ') || nx.startsWith(ny + ' ') || nx === ny))
      (sib.get(x) || sib.set(x, new Set()).get(x)).add(y); }));

  const rows = [];
  byAlbum.forEach((g, id) => {
    const typ = (g.a.album_type || '').toLowerCase();
    if (!['album', 'compilation'].includes(typ)) return;
    const libIds = [...g.lists].filter(isYear);
    const inLib = new Set(); recs.filter(r => isYear(r.id)).forEach(r => r.items.forEach(({ t }) => { if (t.album.id === id) inLib.add(t.id); }));
    const total = g.a.total_tracks || 0;
    if (inLib.size >= total && total) return;             // komplett i biblioteket
    const sibl = [...(sib.get(id) || [])];
    const orsak = [];
    if (sibl.length) orsak.push(`annan utgåva: ${sibl.map(x => `${byAlbum.get(x).a.name} (${byAlbum.get(x).ids.size}/${byAlbum.get(x).a.total_tracks})`).join(', ')}`);
    if (g.ids.size > inLib.size) orsak.push(`${g.ids.size - inLib.size} låtar ligger bara i icke-årslistor`);
    if (g.ids.size < total) orsak.push(`saknar ${total - g.ids.size} av ${total} spår totalt`);
    rows.push({ artist: g.a.artists?.[0]?.name, album: g.a.name, år: (g.a.release_date || '').slice(0, 4), typ,
      'har/totalt': `${inLib.size}/${total}`, orsak: orsak.join('; ') || '?', listor: [...g.lists].map(name).join(', '), id });
  });
  rows.sort((x, y) => (x.artist || '').localeCompare(y.artist || '') || x.album.localeCompare(y.album));
  console.table(rows);
  const c = s => rows.filter(r => r.orsak.includes(s)).length;
  console.log(`${rows.length} ofullständiga album. Annan utgåva: ${c('annan utgåva')}. Bara i icke-årslistor: ${c('icke-årslistor')}. Saknar spår: ${c('saknar')}.`);
  const nära = rows.filter(r => { const [h, t] = r['har/totalt'].split('/').map(Number); return t && t - h <= 2 && h >= 6; }).length;
  console.log(`Saknar högst 2 spår (≥6 låtar): ${nära}`);
  window.__rows = JSON.stringify(rows);
  console.log('Skriv nu:  copy(__rows)  och tryck Enter – klistra sedan in i chatten.');
})();
