"""Build the local dashboard webpage and send the email digest."""
import html
import smtplib
import datetime
from email.mime.text import MIMEText


def _chip(text):
    return f'<span class="tag">{html.escape(text)}</span>'


def _card(j, is_new):
    tags = "".join(_chip(t) for t in j.get("tags", []))
    new_badge = '<span class="new">NEW</span>' if is_new else ""
    posted = f' · {html.escape(j["posted"])}' if j.get("posted") else ""
    src = html.escape(j.get("source", ""))
    return f"""
    <a class="card" href="{html.escape(j.get('url',''))}" target="_blank"
       data-text="{html.escape((j.get('title','')+' '+j.get('company','')+' '+j.get('location','')).lower())}"
       data-source="{src}" data-new="{'1' if is_new else '0'}">
      <div class="row">
        <h3>{html.escape(j.get('title','(no title)'))}</h3>{new_badge}
      </div>
      <div class="meta">{html.escape(j.get('company','')) } · {html.escape(j.get('location','') or '—')}{posted}</div>
      <div class="meta src">{src}</div>
      <div class="tags">{tags}</div>
    </a>"""


def build_dashboard(all_jobs, new_ids, path):
    now = datetime.datetime.now().strftime("%a %d %b %Y, %H:%M")
    sources = sorted({j.get("source", "").split(":")[0] for j in all_jobs})
    src_chips = "".join(
        f'<button class="filter" data-src="{html.escape(s)}">{html.escape(s)}</button>'
        for s in sources)
    cards = "".join(_card(j, j["id"] in new_ids) for j in all_jobs)
    new_count = len(new_ids)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JobHunt — London Finance</title>
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --line:#272b34; --txt:#e7e9ee;
           --mut:#9aa3b2; --acc:#4f8cff; --new:#1db66c; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt);
          font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  header {{ padding:24px 20px 12px; border-bottom:1px solid var(--line);
            position:sticky; top:0; background:var(--bg); z-index:5; }}
  h1 {{ margin:0 0 4px; font-size:20px; }}
  .sub {{ color:var(--mut); font-size:13px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
  #q {{ flex:1; min-width:200px; padding:9px 12px; border-radius:9px;
        border:1px solid var(--line); background:var(--card); color:var(--txt); }}
  .filter {{ padding:7px 12px; border-radius:9px; border:1px solid var(--line);
             background:var(--card); color:var(--mut); cursor:pointer; font-size:13px; }}
  .filter.on {{ color:#fff; border-color:var(--acc); background:#1d2738; }}
  main {{ padding:16px 20px 60px; display:grid; gap:12px;
          grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }}
  .card {{ display:block; text-decoration:none; color:inherit; background:var(--card);
           border:1px solid var(--line); border-radius:13px; padding:15px;
           transition:.15s border-color, .15s transform; }}
  .card:hover {{ border-color:var(--acc); transform:translateY(-2px); }}
  .row {{ display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }}
  .card h3 {{ margin:0; font-size:15px; }}
  .meta {{ color:var(--mut); font-size:13px; margin-top:5px; }}
  .src {{ font-size:11px; opacity:.7; }}
  .new {{ background:var(--new); color:#04140b; font-size:10px; font-weight:700;
          padding:2px 7px; border-radius:20px; letter-spacing:.04em; }}
  .tags {{ margin-top:9px; display:flex; flex-wrap:wrap; gap:6px; }}
  .tag {{ font-size:11px; background:#21283a; color:#a9c2ff; padding:2px 8px; border-radius:20px; }}
  .empty {{ color:var(--mut); padding:40px; text-align:center; grid-column:1/-1; }}
</style></head><body>
<header>
  <h1>London Finance — JobHunt</h1>
  <div class="sub">{len(all_jobs)} open roles · <b style="color:var(--new)">{new_count} new</b> · updated {now}</div>
  <div class="controls">
    <input id="q" placeholder="Search title, company, location…">
    <button class="filter on" data-src="__all">all</button>
    <button class="filter" data-src="__new">new only</button>
    {src_chips}
  </div>
</header>
<main id="grid">{cards or '<div class="empty">No matching roles yet. Run again tomorrow.</div>'}</main>
<script>
  const q=document.getElementById('q'), cards=[...document.querySelectorAll('.card')];
  let src='__all';
  function apply(){{
    const t=q.value.trim().toLowerCase();
    cards.forEach(c=>{{
      const okT=!t||c.dataset.text.includes(t);
      const okS=src==='__all'||(src==='__new'?c.dataset.new==='1':c.dataset.source.startsWith(src));
      c.style.display=(okT&&okS)?'':'none';
    }});
  }}
  q.addEventListener('input',apply);
  document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{{
    document.querySelectorAll('.filter').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); src=b.dataset.src; apply();
  }}));
</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def send_email(ecfg, new_jobs, dashboard_path, subject=None, to=None, heading=None):
    if not ecfg.get("enabled") or not new_jobs:
        return False
    if not ecfg.get("password") or not ecfg.get("username"):
        print("  [email] skipped: username/password not set")
        return False
    rows = []
    for j in new_jobs:
        tags = " ".join(f"[{t}]" for t in j.get("tags", []))
        rows.append(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #eee">'
            f'<a href="{html.escape(j.get("url",""))}" style="color:#1a56db;'
            f'text-decoration:none;font-weight:600">{html.escape(j.get("title",""))}</a><br>'
            f'<span style="color:#555;font-size:13px">{html.escape(j.get("company",""))} · '
            f'{html.escape(j.get("location","") or "—")} · {html.escape(j.get("source",""))} '
            f'<span style="color:#888">{html.escape(tags)}</span></span></td></tr>')
    body = f"""<div style="font-family:Arial,sans-serif;max-width:640px;margin:auto">
      <h2 style="margin:0 0 4px">{html.escape(heading) if heading else str(len(new_jobs)) + ' new London finance role(s)'}</h2>
      <p style="color:#666;margin:0 0 16px;font-size:13px">
        {len(new_jobs)} role(s) · {datetime.date.today().strftime('%A %d %B %Y')} ·
        full list in your dashboard: {html.escape(dashboard_path)}</p>
      <table style="width:100%;border-collapse:collapse">{''.join(rows)}</table>
    </div>"""
    msg = MIMEText(body, "html")
    msg["Subject"] = subject or f"🟢 {len(new_jobs)} new London finance roles — {datetime.date.today().isoformat()}"
    msg["From"] = ecfg["username"]
    msg["To"] = to or ecfg.get("to", ecfg["username"])
    try:
        with smtplib.SMTP(ecfg.get("smtp_host", "smtp.gmail.com"),
                          int(ecfg.get("smtp_port", 587))) as s:
            s.starttls()
            s.login(ecfg["username"], ecfg["password"])
            s.send_message(msg)
        print(f"  [email] sent {len(new_jobs)} new roles to {msg['To']}")
        return True
    except Exception as e:
        print(f"  [email] FAILED: {e}")
        return False
