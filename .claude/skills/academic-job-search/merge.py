#!/usr/bin/env python3
"""Merge agent JSON files into output/jobs-YYYY-MM-DD.html; `--check` runs the self-check."""
import argparse, glob, html, json, os, re, unicodedata
from collections import Counter

SKILL = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SKILL, "..", "..", ".."))
ENTRIES = os.path.join(SKILL, "entries.json")
FIELDS = ("university", "country", "deadline", "references", "link", "department", "title", "rank", "area",
          "priority", "materials", "contact", "notes", "flag", "checked")
BRANCH_MARKERS = ("hkust-gz", "hkust(gz)", "cuhk-shenzhen", "cuhk shenzhen",
                  "nyu abu dhabi", "nyu shanghai", "duke kunshan")
BOARD_HOSTS = ("higheredjobs.com", "jobs.ac.uk", "academicjobsonline.org", "cra.org", "euraxess")
DATED = re.compile(r"\d{4}-\d{2}-\d{2}$")
TITLE_STOP = {"tenure", "track", "tenured", "position", "positions", "faculty", "open", "rank", "the", "of",
              "in", "and", "professor", "professors", "professorships", "assistant", "associate", "full",
              "or", "a", "an"}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def load_universities():
    """normalized canonical name or alias -> (canonical name, country)"""
    table = {}
    for line in open(os.path.join(SKILL, "universities.md"), encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[2] not in ("North America", "EU", "Asia"):
            continue
        name, country, _, aliases = cells[:4]
        for key in [name] + aliases.split(";"):
            if key.strip():
                table[norm(key)] = (name, country)
    return table


def host_of(link):
    return re.sub(r"^https?://(www\.)?", "", link).split("/")[0]


def link_key(link):
    m = re.search(r"interfolio\.com/(?:apply/)?(\d+)", link)
    if m:
        return "interfolio:" + m.group(1)
    ids = re.findall(r"\d{5,}", link)
    return host_of(link) + ":" + (ids[-1] if ids else re.sub(r"[?#].*", "", link).rstrip("/"))


def title_tokens(t):
    t = re.sub(r"\((?:[fmdwx]/){1,3}[fmdwx]\)", " ", t.lower())  # gender tags like (f/m/d)
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", t).split() if w not in TITLE_STOP}


def same_posting(a, b):
    ka, kb = link_key(a["link"]), link_key(b["link"])
    if ka == kb:
        return True
    (ha, ia), (hb, ib) = ka.split(":", 1), kb.split(":", 1)
    if ha == hb and ia.isdigit() and ib.isdigit():
        return False
    ta, tb = title_tokens(a["title"]), title_tokens(b["title"])
    return bool(ta | tb) and len(ta & tb) / len(ta | tb) >= 0.5


def firmness(deadline):
    return 2 if DATED.match(deadline) else 1 if deadline == "rolling" else 0


def score(e):
    # any host outside BOARD_HOSTS counts as a university link
    s = -2 if any(b in host_of(e["link"]) for b in BOARD_HOSTS) else 3
    s += firmness(e["deadline"])
    s += 2 if e["flag"] == "ok" else 1 if e["flag"] == "deadline-unclear" else 0
    return s


def dedupe(entries):
    kept = []
    for e in entries:
        dup = next((k for k in kept if k["university"] == e["university"] and same_posting(k, e)), None)
        if dup is None:
            kept.append(e)
            continue
        keep, other = (e, dup) if score(e) > score(dup) else (dup, e)
        if firmness(other["deadline"]) > firmness(keep["deadline"]):
            keep["deadline"] = other["deadline"]
        tag = f"[also listed: {other['link']}]"
        if other["link"] != keep["link"] and tag not in keep["notes"]:
            keep["notes"] = (keep["notes"] + " " + tag).strip()
        kept[kept.index(dup)] = keep
    return kept


def sort_key(e):
    d = e["deadline"]
    tail = 2 if e.get("flag") == "unverified" else 1 if e.get("flag", "ok") != "ok" else 0
    return (tail, 0, d) if DATED.match(d) else (tail, 1, "") if d == "rolling" else (tail, 2, "")


def merge(entries, today, table):
    """Returns (kept sorted, drops as (reason, entry), past-deadline entries)."""
    kept, drops = [], []
    for e in entries:
        for k, v in (("university", ""), ("title", ""), ("link", ""), ("notes", ""),
                     ("deadline", "unknown"), ("flag", "ok")):
            e.setdefault(k, v)
        if e["deadline"] == "unknown" and e["flag"] == "ok":
            e["flag"] = "deadline-unclear"
        blob = (e["title"] + " " + e["link"]).lower()
        hit = next((m for m in BRANCH_MARKERS if m in blob), None)
        if hit:
            drops.append((f"branch campus ({hit})", e))
            continue
        m = table.get(norm(e["university"]))
        if not m:
            drops.append(("not in universities.md", e))
            continue
        e["university"], e["country"] = m
        kept.append(e)
    kept = dedupe(kept)
    past = [e for e in kept if DATED.match(e["deadline"]) and e["deadline"] < today]
    kept = sorted((e for e in kept if not any(e is p for p in past)), key=sort_key)
    return kept, drops, past


def gap_rows(gaps, table):
    """HTML rows for universities the sweep could not check; unmatched names are printed and skipped."""
    H = html.escape
    rows = []
    for g in gaps:
        m = table.get(norm(g["university"]))
        if not m:
            print("gap not in universities.md:", g["university"])
            continue
        links = " ".join(f'<a href="{H(u)}" target="_blank" rel="noopener">{H(host_of(u))}</a>'
                         for u in g["check"].split(" and "))
        rows.append((m[1], m[0], f"<tr><td>{H(m[0])}</td><td>{H(m[1])}</td><td>{H(g['blocked'])}</td><td>{links}</td></tr>"))
    return [r for _, _, r in sorted(rows)]


def render(kept, today, out_dir, gaps=()):
    H = html.escape
    rows = []
    for e in kept:
        cls = ' class="flagged"' if e["flag"] != "ok" else ""
        link = f'<a href="{H(e["link"])}" target="_blank" rel="noopener">Apply</a>'
        cells = [H(e["university"]), H(e["country"]), H(e["deadline"]), H(str(e.get("references", "unknown"))),
                 link, H(e.get("department", "")), H(e["title"]), H(e.get("rank", "open")), H(e.get("area", "")),
                 H(e.get("priority", "")), f'<td class="wide">{H(e.get("materials", ""))}</td>',
                 H(e.get("contact", "unknown")), f'<td class="wide">{H(e["notes"])}</td>', H(e["flag"]),
                 H(e.get("checked", today))]
        tds = "".join(c if c.startswith("<td") else f"<td>{c}</td>" for c in cells)
        rows.append(f"<tr{cls}>{tds}</tr>")
    tpl = open(os.path.join(SKILL, "template.html"), encoding="utf-8").read()
    out = (tpl.replace("<!--DATE-->", today).replace("<!--COUNT-->", str(len(rows)))
           .replace("<!--ROWS-->", "\n".join(rows)).replace("<!--GAPS-->", "\n".join(gaps)))
    os.makedirs(out_dir, exist_ok=True)
    outp = os.path.join(out_dir, f"jobs-{today}.html")
    open(outp, "w", encoding="utf-8").write(out)
    for old in glob.glob(os.path.join(out_dir, "*")):
        if os.path.abspath(old) != os.path.abspath(outp):
            os.remove(old)
            print("deleted", os.path.basename(old))
    return outp


def load_entries():
    return json.load(open(ENTRIES, encoding="utf-8")) if os.path.exists(ENTRIES) else []


def save_entries(kept):
    rows = [{k: e[k] for k in FIELDS if k in e} for e in kept]
    json.dump(rows, open(ENTRIES, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def check():
    table = load_universities()

    def m(n):
        r = table.get(norm(n))
        return r and r[0]
    assert m("Peking University") == "Peking University"
    assert m("Lingnan University") is None
    assert m("CUHK, Shenzhen") is None
    assert m("Virginia Tech") == "Virginia Tech"
    assert m("UC Irvine") == "University of California, Irvine"
    assert m("HKUST") == "Hong Kong University of Science and Technology"
    assert m("UBC") == "University of British Columbia"

    def E(**kw):
        e = dict(university="X", country="Y", deadline="unknown", flag="ok", notes="", title="", link="")
        e.update(kw)
        return e
    kept, drops, _ = merge([E(university="Hong Kong University of Science and Technology",
                              link="https://facrecruit.hkust-gz.edu.cn/", title="Faculty Positions, HKUST(GZ)"),
                            E(university="Lingnan University", link="https://ln.edu.hk/x")],
                           "2026-09-06", table)
    assert not kept and [r for r, _ in drops] == ["branch campus (hkust-gz)", "not in universities.md"]

    t = "Assistant Professor of Quantum Information"
    assert len(dedupe([E(link="https://apply.interfolio.com/191224", title=t),
                       E(link="https://apply.interfolio.com/191104", title=t)])) == 2
    assert len(dedupe([E(link="https://jobs.hku.hk/cw/en/job/534341", title="Tenure-Track Assistant Professor"),
                       E(link="https://jobs.hku.hk/en/job/534341/tenuretrack-assistant-professor-several-posts",
                         title="Tenure-track Assistant Professor (several posts)")])) == 1
    mirror = E(link="https://www.higheredjobs.com/faculty/details.cfm?JobCode=179531222",
               title="Assistant Professor in Quantum Information Theory", deadline="2026-12-01")
    uni = E(link="https://apply.interfolio.com/191224",
            title="Assistant Professor of Quantum Information Theory and Quantum Computing")
    out = dedupe([mirror, uni])
    assert len(out) == 1 and "interfolio" in out[0]["link"] and out[0]["deadline"] == "2026-12-01"
    assert "[also listed: https://www.higheredjobs.com" in out[0]["notes"]
    assert out[0]["notes"].count("[also listed") == 1, "tag not appended twice"
    same = dedupe([E(link="https://apply.interfolio.com/191224", title=t),
                   E(link="https://apply.interfolio.com/191224", title=t)])
    assert len(same) == 1 and "[also listed" not in same[0]["notes"]

    ds = [E(deadline=d) for d in ("rolling", "2026-12-01", "unknown", "2026-10-15")]
    assert [e["deadline"] for e in sorted(ds, key=sort_key)] == ["2026-10-15", "2026-12-01", "rolling", "unknown"]
    assert title_tokens("Professors of Cybersecurity (f/m/d)") == title_tokens("Professors of Cybersecurity")
    ds2 = ds + [E(deadline="2026-09-20", flag="unverified")]
    assert sorted(ds2, key=sort_key)[-1]["deadline"] == "2026-09-20", "unverified rows sort last"
    ds3 = ds2 + [E(deadline="rolling", flag="deadline-unclear")]
    assert [e["flag"] for e in sorted(ds3, key=sort_key)][-2:] == ["deadline-unclear", "unverified"], "flagged rows after ok rows"
    g = gap_rows([dict(university="Peking University", blocked="403", check="https://a.jp/x and https://b.jp/y"),
                  dict(university="Columbia University", blocked="500", check="https://c.edu/"),
                  dict(university="Lingnan University", blocked="404", check="https://d.hk/")], table)
    assert len(g) == 2 and g[0].startswith("<tr><td>Peking University</td><td>China</td>") and g[0].count("<a href") == 2
    print("check ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="run date YYYY-MM-DD")
    ap.add_argument("--in-dir", help="directory of agent JSON files")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--no-save", action="store_true", help="do not rewrite entries.json")
    ap.add_argument("--gaps", help="JSON list of {university, blocked, check}: universities the sweep could not check")
    ap.add_argument("--check", action="store_true", help="run the self-check and exit")
    a = ap.parse_args()
    if a.check:
        check()
        return
    if not (a.date and a.in_dir):
        ap.error("--date and --in-dir are required")

    entries = []
    for f in sorted(glob.glob(os.path.join(a.in_dir, "*.json"))):
        try:
            arr = json.load(open(f, encoding="utf-8"))
        except Exception as ex:
            print(f"!! {f}: {ex}")
            continue
        for e in arr:
            e["_src"] = os.path.basename(f)
            entries.append(e)
    table = load_universities()
    kept, drops, past = merge(entries, a.date, table)
    gaps = gap_rows(json.load(open(a.gaps, encoding="utf-8")), table) if a.gaps else []
    prior = load_entries()
    prior_keys = {link_key(e["link"]) for e in prior}
    kept_keys = {link_key(e["link"]) for e in kept}
    kept_keys |= {link_key(u) for e in kept for u in re.findall(r"\[also listed: (\S+?)\]", e["notes"])}
    outp = render(kept, a.date, a.out_dir, gaps)
    if not a.no_save:
        save_entries(kept)

    areas = Counter(k for e in kept for k in re.split(r"[,\s]+", e.get("area", "")) if k)
    print("wrote", outp)
    print("entries", len(kept))
    print("areas", dict(areas))
    print("flagged", sum(1 for e in kept if e["flag"] != "ok"))
    print("gap rows", len(gaps))
    print("by source", dict(Counter(e["_src"] for e in kept)))
    new = [e for e in kept if link_key(e["link"]) not in prior_keys]
    gone = [e for e in prior if link_key(e["link"]) not in kept_keys]
    print("new since last report:", len(new))
    for e in new:
        print(f"  - {e['university']} | {e['title'][:60]} | {e['link']}")
    print("gone since last report:", len(gone))
    for e in gone:
        print(f"  - {e['university']} | {e['title'][:60]} | {e['link']}")
    print("dropped:", len(drops))
    for reason, e in drops:
        print(f"  - {reason}: {e['university']} | {e['title'][:60]} | {e['link']} ({e['_src']})")
    print("dropped past deadline:", len(past))
    for e in past:
        print(f"  - {e['university']} {e['deadline']} {e['title'][:60]}")


if __name__ == "__main__":
    main()
