"""Aligns the lists of vitamins/minerals cited in the 'health_benefits_and_curiosities' texts (scripts/texts/block_*.json, hb field)
with the computed nutrition claims (Reg. (EC) 1924/2006): "ricco di" = 'Ad alto contenuto di', "fonte di" = 'Fonte di'.
Rewrites only the sentence with "ricc... di" / "high in"; the rest of the text stays unchanged. The original sentences go to
draft_legacy_values (texts_hb_before_sync).
Usage:  python scripts/sync_nutrient_mentions.py [--apply]   (without --apply it only shows a preview)
"""
import glob
import re
import sys

from common import DATA, ROOT, load_json, save_json

IT_NAME = {"vitamina A": "vitamina A", "vitamina C": "vitamina C", "vitamina D": "vitamina D", "vitamina E": "vitamina E", "vitamina K": "vitamina K",
           "tiamina": "tiamina", "riboflavina": "riboflavina", "niacina": "niacina", "vitamina B6": "vitamina B6", "folato": "folati",
           "vitamina B12": "vitamina B12", "potassio": "potassio", "calcio": "calcio", "fosforo": "fosforo", "magnesio": "magnesio",
           "ferro": "ferro", "zinco": "zinco", "rame": "rame", "manganese": "manganese", "selenio": "selenio", "iodio": "iodio"}
EN_NAME = {"vitamin A": "vitamin A", "vitamin C": "vitamin C", "vitamin D": "vitamin D", "vitamin E": "vitamin E", "vitamin K": "vitamin K",
           "thiamin": "thiamin", "riboflavin": "riboflavin", "niacin": "niacin", "vitamin B6": "vitamin B6", "folate": "folate",
           "vitamin B12": "vitamin B12", "potassium": "potassium", "calcium": "calcium", "phosphorus": "phosphorus", "magnesium": "magnesium",
           "iron": "iron", "zinc": "zinc", "copper": "copper", "manganese": "manganese", "selenium": "selenium", "iodine": "iodine"}


def join(xs, conj):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + f" {conj} " + xs[-1]


def lists(cl, lang):
    names = {k.lower(): v for k, v in (IT_NAME if lang == "it" else EN_NAME).items()}   # claims with Title Case initials
    hi_p, so_p = ("ad alto contenuto di ", "fonte di ") if lang == "it" else ("high ", "source of ")
    cl = [c.lower() for c in cl]
    hi = [names[c[len(hi_p):]] for c in cl if c.startswith(hi_p) and c[len(hi_p):] in names]
    so = [names[c[len(so_p):]] for c in cl if c.startswith(so_p) and c[len(so_p):] in names]
    return hi, so


def list_re(names):
    nm = "|".join(sorted({re.escape(x) for x in names} | ({"folato", "folati", "vitamine del gruppo B"} if "folati" in names else set()), key=len, reverse=True))
    item = rf"(?:{nm})(?:\s*\([^)]*\))?"
    return rf"(?:{item})(?:(?:, | e | and |, and ){item})*"


IT_L = list_re(list(IT_NAME.values()))
EN_L = list_re(list(EN_NAME.values()))
IT_RE = re.compile(rf"(?P<adj>ricc(?:o|a|hi|he|hissim[oaie])) di (?P<h>{IT_L})(?P<mid> (?:ed? )?(?:è |sono )?fonte di )?(?P<s>{IT_L})?")
EN_RE = re.compile(rf"(?P<adj>(?:very |extremely )?(?:high|rich)) in (?P<h>{EN_L})(?P<mid> and (?:a )?source of )?(?P<s>{EN_L})?")
IT_ONLY_SRC = re.compile(rf"(?P<adj>)(?P<h>)(?P<mid>\bfonte di )(?P<s>{IT_L})")


def names_in(seg, lang):
    if not seg:
        return set()
    names = IT_NAME if lang == "it" else EN_NAME
    out = {v for v in names.values() if re.search(rf"\b{re.escape(v)}\b", seg)}
    if lang == "it" and re.search(r"\bfolat[oi]\b", seg):
        out.add("folati")
    return out


def rebuild(text, cl, lang):
    rx = IT_RE if lang == "it" else EN_RE
    hi, so = lists(cl, lang)
    m = rx.search(text)
    if not m:
        return text
    L = IT_L if lang == "it" else EN_L
    ext = (re.compile(rf"(?:,? e (?:ricc\w+ di |di )(?P<h>{L})|,? e (?:è )?fonte di (?P<s>{L}))") if lang == "it"
           else re.compile(rf"(?:,? and (?:very |extremely )?(?:high|rich) in (?P<h>{L})|,? and (?:a )?source of (?P<s>{L}))"))
    end, hs, ss = m.end(), [m.group("h")], [m.group("s") or ""]
    while True:
        m2 = ext.match(text, end)
        if not m2:
            break
        hs.append(m2.group("h") or ""); ss.append(m2.group("s") or ""); end = m2.end()
    h_txt, s_txt = names_in(" ".join(hs), lang), names_in(" ".join(ss), lang)
    if h_txt == set(hi) and s_txt <= set(so) | set(hi):
        return text
    conj = "e" if lang == "it" else "and"
    adj = m.group("adj")
    adj = {"ricchissimo": "ricco", "ricchissima": "ricca", "ricchissimi": "ricchi", "ricchissime": "ricche"}.get(adj, adj)
    adj = re.sub(r"^(very|extremely) ", "", adj)
    m_adj = adj
    if lang == "it":
        new = (f"{m_adj} di {join(hi, 'e')}" if hi else "") + (f"{' e ' if hi else ''}fonte di {join(so, 'e')}" if so else "")
        if not hi and not so:
            new = "fonte di poche vitamine e minerali"
    else:
        new = (f"{m_adj} in {join(hi, conj)}" if hi else "") + (f"{' and a ' if hi else 'a '}source of {join(so, conj)}" if so else "")
        if not hi and not so:
            new = "a modest source of vitamins and minerals"
    return text[:m.start()] + new + text[end:]

def main():
    apply = "--apply" in sys.argv
    db = {it["id"]: it for it in load_json(DATA / "database.json")["items"]}
    legacy = load_json(DATA / "draft_legacy_values.json")
    n = 0
    for f in sorted(glob.glob(str(ROOT / "scripts" / "texts" / "block_*.json"))):
        blk = load_json(f)
        changed = False
        for iid, t in blk.items():
            if iid not in db or not t.get("hb"):
                continue
            cl = db[iid]["nutrition_and_sustainability"]["nutrition_claims_eu"]
            if not cl:          # nessun valore nutrizionale (es. alimenti senza scheda CREA/BDA/USDA)
                continue
            it_new, en_new = rebuild(t["hb"][0], cl["it"], "it"), rebuild(t["hb"][1], cl["en"], "en")
            if (it_new, en_new) != tuple(t["hb"]):
                n += 1
                print(f"--- {iid}\n  IT before: {t['hb'][0][:230]}\n  IT after : {it_new[:230]}\n  EN after : {en_new[:230]}")
                if apply:
                    legacy["items"].setdefault(iid, {}).setdefault("texts_hb_before_sync", t["hb"])
                    t["hb"] = [it_new, en_new]
                    changed = True
        if apply and changed:
            save_json(f, blk)
    if apply:
        save_json(DATA / "draft_legacy_values.json", legacy)
    print("texts to align:", n, "(applied)" if apply else "(preview)")


if __name__ == "__main__":
    main()
