"""Verifica nome scientifico, genere e famiglia della bozza con WFO (piante) / GBIF (funghi) ed EPPO.

- scientific_name/genus: confermati se coincidono (senza autori) con il nome trovato in WFO/GBIF o EPPO.
- family: confermata se coincide con WFO/GBIF. Se diversa, si mantiene la famiglia secondo APG IV quando la
  differenza è solo di sistema di classificazione (es. Chenopodiaceae in WFO = Amaranthaceae in APG IV) e si
  annota; altrimenti si segnala come discrepanza.
Uso:  python scripts/verify_botany.py
"""
import re

from common import DATA, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

APG_EQUIV = {("Chenopodiaceae", "Amaranthaceae"), ("Amaryllidaceae", "Alliaceae"), ("Grossulariaceae", "Grossulariaceae")}


def canon(s):
    s = (s or "").replace("×", "x").replace(" x ", " ")
    s = re.sub(r"\b(subsp|var|f|convar)\.", "", s)
    return " ".join(w for w in s.split() if w[:1].islower() or w == s.split()[0])[:80].lower()


def main():
    db = load_json(DATA / "database.json")
    idx = {i["id"]: i for i in load_json(DATA / "items_index.json")["items"]}
    stats = {"nome": 0, "famiglia": 0, "fam_apg": 0, "fam_diversa": 0}
    for it in db["items"]:
        b = it["botany"]
        chk = idx[it["id"]]["botany_check"]
        ref = chk.get("wfo") or chk.get("gbif") or {}
        names = [ref.get("name"), chk["eppo"].get("eppo_preferred_name"), chk["eppo"].get("matched_on")]
        sci = canon(b["scientific_name"].split("/")[0])
        enr = []
        if any(n and (canon(n).startswith(sci) or sci.startswith(canon(n))) for n in names):
            enr += ["botany.scientific_name", "botany.genus"]
            stats["nome"] += 1
        fam = ref.get("family")
        if fam and b["family"]:
            if fam == b["family"]:
                enr.append("botany.family"); stats["famiglia"] += 1
            elif (fam, b["family"]) in APG_EQUIV or (b["family"], fam) in APG_EQUIV:
                enr.append("botany.family"); stats["fam_apg"] += 1
                it["data_completeness"]["notes"] += f" Famiglia {b['family']} (APG IV) = {fam} in WFO (sistema precedente)."
            else:
                add_discrepancy(it, "botany.family", b["family"], fam, "WFO/GBIF", "mantenuta la famiglia della bozza: da verificare")
                stats["fam_diversa"] += 1
        elif fam and not b["family"]:
            b["family"] = fam; enr.append("botany.family")
        mark_enriched(it, enr)
        finalize_completeness(it)
    save_json(DATA / "database.json", db)
    print(stats)


if __name__ == "__main__":
    main()
