// Activation-code store. Codes map to Xtream credentials held server-side in KV.
// New codes are 16 random chars (unguessable); legacy 4-digit codes are kept so existing users keep working.
const J = (obj, status = 200) => new Response(JSON.stringify(obj), {
  status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
});

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const m = url.pathname.match(/^\/c(?:\/([A-Za-z0-9]{4,32}))?$/);
    if (!m) return J({ error: 'not found' }, 404);

    if (req.method === 'GET' && m[1]) {
      const v = await env.ACT.get('c:' + m[1]);
      return v ? new Response(v, { headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } }) : J({ error: 'not found' }, 404);
    }

    if (req.method === 'POST' && !m[1]) {
      const raw = await req.text();
      if (raw.length > 1024) return J({ error: 'too large' }, 413);
      let d;
      try { d = JSON.parse(raw); } catch { return J({ error: 'bad json' }, 400); }
      const ok = (s, n) => typeof s === 'string' && s.length > 0 && s.length <= n;
      if (!ok(d.url, 200) || !/^https?:\/\//i.test(d.url) || !ok(d.user, 100) || !ok(d.pass, 100)) return J({ error: 'invalid' }, 400);
      const bytes = crypto.getRandomValues(new Uint8Array(16));
      const code = Array.from(bytes, b => 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[b % 32]).join('');
      await env.ACT.put('c:' + code, JSON.stringify({ url: d.url, user: d.user, pass: d.pass }));
      return J({ code });
    }
    return J({ error: 'method' }, 405);
  },
};
