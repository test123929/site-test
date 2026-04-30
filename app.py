"""
⚠️  PENTEST OEFENOMGEVING — GEEN ECHTE SITE
Intentioneel kwetsbaar voor educatieve doeleinden.
"""

from flask import Flask, request, render_template_string, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "novatech_secret_2024"  # VULNERABILITY: zwakke hardcoded secret

DATABASE = "novatech.db"

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            role TEXT DEFAULT 'employee',
            department TEXT,
            secret TEXT
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            author TEXT,
            priority TEXT
        );
        DELETE FROM employees;
        DELETE FROM tickets;
        INSERT INTO employees VALUES (1,'admin','Admin@2024','admin','IT Infrastructure','FLAG{admin_panel_gevonden}');
        INSERT INTO employees VALUES (2,'j.bakker','Welkom01!','employee','Finance','FLAG{bakker_data_gelekt}');
        INSERT INTO employees VALUES (3,'m.visser','Zomer2024','employee','HR','FLAG{visser_privé_gevonden}');
        INSERT INTO tickets VALUES (1,'Server downtime melding','Productieserver NL-03 offline','admin','Hoog');
        INSERT INTO tickets VALUES (2,'VPN toegang aanvragen','Nieuwe medewerker heeft VPN nodig','j.bakker','Normaal');
        INSERT INTO tickets VALUES (3,'Wachtwoord reset','Gebruiker vergeten wachtwoord','m.visser','Laag');
    """)
    db.commit()
    db.close()

# ── HOME ──────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(SHELL, page="home", body=HOME)

# ── LOGIN — SQL INJECTION ─────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        u = request.form.get("username","")
        p = request.form.get("password","")
        db = get_db()
        # ⚠️ VULNERABILITY: SQL Injection
        q = f"SELECT * FROM employees WHERE username='{u}' AND password='{p}'"
        try:
            row = db.execute(q).fetchone()
        except Exception as e:
            error = f"Database fout: {e}"
            row = None
        db.close()
        if row:
            session["user"] = row["username"]
            session["role"] = row["role"]
            session["dept"] = row["department"]
            return redirect("/portal")
        error = error or "Ongeldige inloggegevens."
    rendered_login = render_template_string(LOGIN, error=error)
    return render_template_string(SHELL, page="login", body=rendered_login)

# ── PORTAL (dashboard) ────────────────────────────────────
@app.route("/portal")
def portal():
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    tickets = db.execute("SELECT * FROM tickets").fetchall()
    db.close()
    return render_template_string(SHELL, page="portal", body=PORTAL,
                                  user=session["user"], role=session["role"],
                                  dept=session["dept"], tickets=tickets)

# ── ZOEKEN — XSS + SQL INJECTION ─────────────────────────
@app.route("/search")
def search():
    q = request.args.get("q","")
    results = []
    if q:
        db = get_db()
        # ⚠️ VULNERABILITY: SQL Injection
        try:
            results = db.execute(f"SELECT * FROM tickets WHERE title LIKE '%{q}%' OR description LIKE '%{q}%'").fetchall()
        except:
            results = []
        db.close()
    # ⚠️ VULNERABILITY: XSS — geen escaping
    result_html = ""
    for t in results:
        result_html += f"""
        <div class="ticket-row">
            <span class="prio prio-{t['priority'].lower()}">{t['priority']}</span>
            <div>
                <div class="ticket-title">{t['title']}</div>
                <div class="ticket-desc">{t['description']}</div>
                <div class="ticket-meta">Ingediend door {t['author']}</div>
            </div>
        </div>"""
    search_output = f'<p class="search-label">Resultaten voor: <strong>{q}</strong></p>' + (result_html or '<p class="no-res">Geen tickets gevonden.</p>') if q else ""
    return render_template_string(SHELL, page="search", body=SEARCH, q=q, search_output=search_output)

# ── MEDEWERKER PROFIEL — IDOR ────────────────────────────
@app.route("/employee/<int:eid>")
def employee(eid):
    db = get_db()
    # ⚠️ VULNERABILITY: IDOR — geen autorisatiecheck
    emp = db.execute(f"SELECT * FROM employees WHERE id={eid}").fetchone()
    db.close()
    if not emp:
        return render_template_string(SHELL, page="employee", body="<div class='card'><p>Medewerker niet gevonden.</p></div>")
    return render_template_string(SHELL, page="employee", body=PROFILE, emp=emp)

# ── LOGOUT ────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── DISCLAIMER ────────────────────────────────────────────
@app.route("/disclaimer")
def disclaimer():
    return render_template_string(SHELL, page="disclaimer", body=DISCLAIMER)

# ════════════════════════════════════════════════════════
# TEMPLATES
# ════════════════════════════════════════════════════════

SHELL = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NovaTech — Medewerker Portaal</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f0f2f5;
  --surface:#ffffff;
  --sidebar:#0f1923;
  --sidebar-hover:#1a2737;
  --accent:#0066ff;
  --accent-dark:#0052cc;
  --danger:#e53e3e;
  --warn:#f6ad55;
  --success:#38a169;
  --text:#1a202c;
  --muted:#718096;
  --border:#e2e8f0;
  --mono:'DM Mono',monospace;
  --sans:'DM Sans',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--text);display:flex;min-height:100vh;flex-direction:column}

/* ── PENTEST BANNER ── */
.pentest-bar{
  background:#7c3aed;
  color:#fff;
  text-align:center;
  font-size:.75rem;
  font-family:var(--mono);
  padding:6px 1rem;
  letter-spacing:.3px;
  position:sticky;top:0;z-index:200;
}
.pentest-bar a{color:#ddd6fe;text-decoration:underline}

/* ── TOPBAR ── */
.topbar{
  background:var(--surface);
  border-bottom:1px solid var(--border);
  padding:0 2rem;
  height:56px;
  display:flex;align-items:center;gap:1rem;
  position:sticky;top:28px;z-index:100;
  box-shadow:0 1px 3px rgba(0,0,0,.06);
}
.logo{font-size:1.05rem;font-weight:600;color:var(--text);display:flex;align-items:center;gap:.5rem}
.logo-dot{width:8px;height:8px;border-radius:50%;background:var(--accent)}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:1rem}
.topbar-right a{color:var(--muted);text-decoration:none;font-size:.82rem;transition:color .15s}
.topbar-right a:hover{color:var(--text)}
.user-chip{background:var(--bg);border:1px solid var(--border);border-radius:20px;padding:4px 12px;font-size:.78rem;color:var(--text)}

/* ── LAYOUT ── */
.layout{display:flex;flex:1}
.sidebar{
  width:220px;min-height:calc(100vh - 84px);
  background:var(--sidebar);
  padding:1.5rem 0;
  flex-shrink:0;
}
.sidebar-section{padding:0 1rem .5rem;font-size:.65rem;font-family:var(--mono);color:#4a6080;text-transform:uppercase;letter-spacing:1px;margin-top:1rem}
.sidebar a{
  display:flex;align-items:center;gap:.75rem;
  padding:.6rem 1.25rem;
  color:#8899aa;
  text-decoration:none;
  font-size:.83rem;
  transition:background .15s,color .15s;
  border-left:2px solid transparent;
}
.sidebar a:hover,.sidebar a.active{background:var(--sidebar-hover);color:#fff;border-left-color:var(--accent)}
.sidebar .icon{font-size:.9rem;width:16px;text-align:center}

.main{flex:1;padding:2rem;max-width:960px}

/* ── CARDS ── */
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.75rem;margin-bottom:1.25rem}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem}
.card-title{font-size:1rem;font-weight:600}

/* ── STATS ── */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.25rem}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.25rem}
.stat-num{font-size:1.75rem;font-weight:600;color:var(--accent)}
.stat-label{font-size:.78rem;color:var(--muted);margin-top:.2rem}

/* ── TICKETS ── */
.ticket-row{display:flex;align-items:flex-start;gap:1rem;padding:.875rem 0;border-bottom:1px solid var(--border)}
.ticket-row:last-child{border-bottom:none}
.prio{font-size:.68rem;font-family:var(--mono);padding:2px 8px;border-radius:4px;font-weight:500;white-space:nowrap;margin-top:2px}
.prio-hoog{background:#fff5f5;color:var(--danger)}
.prio-normaal{background:#fffbeb;color:#b7791f}
.prio-laag{background:#f0fff4;color:var(--success)}
.ticket-title{font-size:.88rem;font-weight:500}
.ticket-desc{font-size:.8rem;color:var(--muted);margin-top:.15rem}
.ticket-meta{font-size:.73rem;color:#a0aec0;margin-top:.25rem;font-family:var(--mono)}

/* ── PROFILE TABLE ── */
.profile-table{width:100%;border-collapse:collapse;font-size:.85rem}
.profile-table td{padding:.6rem .75rem;border-bottom:1px solid var(--border)}
.profile-table td:first-child{color:var(--muted);width:35%;font-size:.78rem}
.flag-cell{font-family:var(--mono);color:var(--success);font-weight:500}

/* ── LOGIN FORM ── */
.login-wrap{min-height:calc(100vh - 84px);display:flex;align-items:center;justify-content:center;background:var(--bg)}
.login-box{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2.5rem;width:100%;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,.07)}
.login-logo{text-align:center;margin-bottom:2rem}
.login-logo .name{font-size:1.3rem;font-weight:600;margin-top:.5rem}
.login-logo .sub{font-size:.78rem;color:var(--muted);margin-top:.2rem}
.form-group{margin-bottom:1rem}
label{display:block;font-size:.78rem;color:var(--muted);margin-bottom:.35rem;font-weight:500}
input[type=text],input[type=password]{
  width:100%;background:var(--bg);border:1px solid var(--border);
  color:var(--text);padding:.65rem .9rem;border-radius:7px;
  font-family:var(--sans);font-size:.88rem;transition:border-color .15s
}
input:focus{outline:none;border-color:var(--accent);background:#fff}
.btn{
  width:100%;background:var(--accent);color:#fff;border:none;
  padding:.75rem;border-radius:7px;font-family:var(--sans);
  font-weight:600;font-size:.9rem;cursor:pointer;transition:background .15s;margin-top:.5rem
}
.btn:hover{background:var(--accent-dark)}
.error-msg{color:var(--danger);font-size:.78rem;margin-top:.5rem;text-align:center}
.login-help{text-align:center;font-size:.75rem;color:var(--muted);margin-top:1.5rem}

/* ── SEARCH ── */
.search-bar{display:flex;gap:.75rem;margin-bottom:1.5rem}
.search-bar input{flex:1}
.search-bar button{background:var(--accent);color:#fff;border:none;padding:.65rem 1.25rem;border-radius:7px;cursor:pointer;font-family:var(--sans);font-weight:600;font-size:.85rem}
.search-label{font-size:.82rem;color:var(--muted);margin-bottom:1rem;font-family:var(--mono)}
.no-res{color:var(--muted);font-size:.85rem}

/* ── DISCLAIMER ── */
.disclaimer-box{max-width:700px;margin:0 auto}
.disc-header{background:#7c3aed;color:#fff;border-radius:10px;padding:2rem;margin-bottom:1.25rem;text-align:center}
.disc-header h1{font-size:1.5rem;margin-bottom:.5rem}
.disc-header p{font-size:.85rem;opacity:.85}
.vuln-list{list-style:none;display:grid;gap:.75rem;margin-top:.75rem}
.vuln-list li{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:.875rem 1rem;font-size:.85rem}
.vuln-list li strong{color:var(--accent);font-family:var(--mono)}

.badge{display:inline-block;background:#ebf4ff;color:var(--accent);font-size:.68rem;font-family:var(--mono);padding:2px 8px;border-radius:4px;margin-left:.5rem}
</style>
</head>
<body>

<div class="pentest-bar">
  ⚠️ &nbsp;PENTEST OEFENOMGEVING — Dit is geen echte site. Intentioneel kwetsbaar voor educatieve doeleinden. &nbsp;<a href="/disclaimer">Meer info</a>
</div>

{% if page == 'login' %}
<div class="login-wrap">
  <div>{{ body | safe }}</div>
</div>

{% elif page in ['home','portal','search','employee','disclaimer'] %}
<div class="topbar">
  <div class="logo"><div class="logo-dot"></div> NovaTech Solutions</div>
  <div class="topbar-right">
    {% if session.get('user') %}
      <span class="user-chip">{{ session.get('user') }}</span>
      <a href="/logout">Uitloggen</a>
    {% else %}
      <a href="/login">Inloggen</a>
    {% endif %}
    <a href="/disclaimer" style="color:#7c3aed;font-weight:600">⚠️ Disclaimer</a>
  </div>
</div>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-section">Portaal</div>
    <a href="/" class="{{ 'active' if page=='home' }}"><span class="icon">🏠</span> Dashboard</a>
    <a href="/portal" class="{{ 'active' if page=='portal' }}"><span class="icon">📋</span> Mijn Tickets</a>
    <a href="/search" class="{{ 'active' if page=='search' }}"><span class="icon">🔍</span> Zoeken</a>
    <div class="sidebar-section">Medewerkers</div>
    <a href="/employee/1" class="{{ 'active' if page=='employee' }}"><span class="icon">👤</span> Profielen</a>
    <div class="sidebar-section">Systeem</div>
    <a href="/disclaimer"><span class="icon">⚠️</span> Disclaimer</a>
    {% if session.get('user') %}
    <a href="/logout"><span class="icon">🚪</span> Uitloggen</a>
    {% endif %}
  </div>
  <div class="main">{{ body | safe }}</div>
</div>
{% endif %}

</body>
</html>"""

HOME = """
<div class="card">
  <div class="card-header">
    <span class="card-title">Welkom bij NovaTech Solutions</span>
    <span class="badge">Intern portaal</span>
  </div>
  <p style="color:var(--muted);font-size:.88rem;line-height:1.7">
    Dit is het interne medewerkerportaal van NovaTech. Log in om tickets te beheren, collega's te raadplegen en systeemtoegang te beheren.
  </p>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-num">3</div>
    <div class="stat-label">Open tickets</div>
  </div>
  <div class="stat">
    <div class="stat-num">3</div>
    <div class="stat-label">Medewerkers</div>
  </div>
  <div class="stat">
    <div class="stat-num">1</div>
    <div class="stat-label">Kritieke melding</div>
  </div>
</div>

<div class="card">
  <div class="card-header"><span class="card-title">Recente activiteit</span></div>
  <div class="ticket-row">
    <span class="prio prio-hoog">Hoog</span>
    <div>
      <div class="ticket-title">Server downtime melding</div>
      <div class="ticket-meta">admin · zojuist</div>
    </div>
  </div>
  <div class="ticket-row">
    <span class="prio prio-normaal">Normaal</span>
    <div>
      <div class="ticket-title">VPN toegang aanvragen</div>
      <div class="ticket-meta">j.bakker · 2u geleden</div>
    </div>
  </div>
  <div class="ticket-row">
    <span class="prio prio-laag">Laag</span>
    <div>
      <div class="ticket-title">Wachtwoord reset</div>
      <div class="ticket-meta">m.visser · gisteren</div>
    </div>
  </div>
</div>
"""

LOGIN = """
<div class="login-box">
  <div class="login-logo">
    <div style="font-size:2rem">🔐</div>
    <div class="name">NovaTech Solutions</div>
    <div class="sub">Medewerker Portaal — Inloggen</div>
  </div>
  <form method="POST">
    <div class="form-group">
      <label>Gebruikersnaam</label>
      <input type="text" name="username" placeholder="gebruikersnaam" autocomplete="off">
    </div>
    <div class="form-group">
      <label>Wachtwoord</label>
      <input type="password" name="password" placeholder="••••••••">
    </div>
    {% if error %}<p class="error-msg">{{ error }}</p>{% endif %}
    <button type="submit" class="btn">Inloggen</button>
  </form>
  <p class="login-help">Problemen met inloggen? Neem contact op met IT.</p>
</div>
"""

PORTAL = """
<div class="card">
  <div class="card-header">
    <span class="card-title">Welkom terug, {{ user }}</span>
    <span class="badge">{{ role }} · {{ dept }}</span>
  </div>
  <p style="color:var(--muted);font-size:.85rem">Je bent ingelogd in het NovaTech portaal.</p>
</div>

<div class="card">
  <div class="card-header"><span class="card-title">Alle tickets</span></div>
  {% for t in tickets %}
  <div class="ticket-row">
    <span class="prio prio-{{ t.priority | lower }}">{{ t.priority }}</span>
    <div>
      <div class="ticket-title">{{ t.title }}</div>
      <div class="ticket-desc">{{ t.description }}</div>
      <div class="ticket-meta">{{ t.author }}</div>
    </div>
  </div>
  {% endfor %}
</div>
"""

SEARCH = """
<div class="card">
  <div class="card-header"><span class="card-title">Tickets zoeken</span></div>
  <form method="GET">
    <div class="search-bar">
      <input type="text" name="q" value="{{ q }}" placeholder="Zoek op titel of omschrijving...">
      <button type="submit">Zoeken</button>
    </div>
  </form>
  {{ search_output | safe }}
</div>
"""

PROFILE = """
<div class="card">
  <div class="card-header">
    <span class="card-title">Medewerkersprofiel</span>
    <span class="badge">ID #{{ emp.id }}</span>
  </div>
  <table class="profile-table">
    <tr><td>Gebruikersnaam</td><td>{{ emp.username }}</td></tr>
    <tr><td>Afdeling</td><td>{{ emp.department }}</td></tr>
    <tr><td>Rol</td><td>{{ emp.role }}</td></tr>
    <tr><td>Intern token</td><td class="flag-cell">{{ emp.secret }}</td></tr>
  </table>
  <div style="margin-top:1rem;display:flex;gap:.5rem">
    <a href="/employee/{{ emp.id - 1 }}" style="font-size:.78rem;color:var(--muted);text-decoration:none">← Vorige</a>
    <a href="/employee/{{ emp.id + 1 }}" style="font-size:.78rem;color:var(--muted);text-decoration:none;margin-left:auto">Volgende →</a>
  </div>
</div>
"""

DISCLAIMER = """
<div class="disclaimer-box">
  <div class="disc-header">
    <div style="font-size:2.5rem">⚠️</div>
    <h1>Pentest Oefenomgeving</h1>
    <p>Deze site is opzettelijk kwetsbaar gemaakt voor educatieve doeleinden</p>
  </div>

  <div class="card">
    <div class="card-title" style="margin-bottom:1rem">Wat is dit?</div>
    <p style="font-size:.85rem;color:var(--muted);line-height:1.7">
      NovaTech Solutions is een <strong>volledig nep bedrijf</strong>. Deze site simuleert een intern medewerkerportaal
      en bevat opzettelijke beveiligingslekken om pentesting technieken te leren.
      Er zijn geen echte gebruikers, geen echte data en geen echte systemen aan verbonden.
    </p>
  </div>

  <div class="card">
    <div class="card-title" style="margin-bottom:1rem">Kwetsbaarheden om te vinden</div>
    <ul class="vuln-list">
      <li><strong>SQL Injection</strong> — Loginpagina: bypass authenticatie zonder wachtwoord</li>
      <li><strong>XSS</strong> — Zoekpagina: injecteer HTML/JavaScript via de zoekbalk</li>
      <li><strong>IDOR</strong> — Medewerkersprofielen: bekijk data van andere gebruikers via URL</li>
    </ul>
  </div>

  <div class="card">
    <div class="card-title" style="margin-bottom:.75rem">Spelregels</div>
    <p style="font-size:.85rem;color:var(--muted);line-height:1.7">
      ✅ Gebruik deze site om pentesting te leren<br>
      ✅ Probeer alle kwetsbaarheden te vinden<br>
      ❌ Gebruik deze technieken NOOIT op echte sites zonder toestemming<br>
      ❌ Deel geen gevonden kwetsbaarheden als echte lekken
    </p>
  </div>
</div>
"""

if __name__ == "__main__":
    init_db()
    print("\n✅ NovaTech portaal gestart op http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
