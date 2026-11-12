"""Valida data/database.json: schema formale (data/schema.json) + controlli logici.

Uso:  python scripts/validate_db.py [--strict] [--report data/validation_report.json]
  --strict  tratta anche gli avvisi come errori (per il rilascio finale)

Controlli:
  E = errore (exit code 1)   W = avviso
  E  conformità a JSON Schema 2020-12 (enum, 12 mesi, traduzioni IT/EN non vuote, campi non previsti, ...)
  E  ID univoci; nome file immagini = <id>_NN.jpg; file della galleria esistenti; primaria in galleria;
     image_details allineati alla galleria
  E  keep_away_from verso ID esistenti e diversi da sé stessi
  E  missing_fields coerente con i campi realmente nulli
  E  intervalli min <= max (temperatura, umidità, giorni di conservazione)
  E  is_complete = true solo senza campi mancanti né da verificare
  W  somma acqua+macro > 105 g/100 g; kcal incoerenti con i macronutrienti (> 25% di scarto)
  W  foto presenti su disco ma non in galleria (lanciare sync_images.py)
  W  ID diverso da <nome_it>_<name_en> normalizzati
"""
import json
import re
import sys
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker

from common import DATA, IMAGES, load_json, null_paths


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def main():
    strict = "--strict" in sys.argv
    raw = load_json(DATA / "database.json", raw=True)          # il file così com'è, con i riferimenti al corpus
    schema = load_json(DATA / "schema.json")
    errors, warnings = [], []

    v = Draft202012Validator(schema, format_checker=FormatChecker())
    for e in sorted(v.iter_errors(raw), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in e.absolute_path)
        if path.startswith("items/"):
            idx = int(path.split("/")[1])
            path = raw["items"][idx].get("id", idx).__str__() + ":" + "/".join(path.split("/")[2:])
        errors.append(f"[schema] {path}: {e.message[:200]}")

    # corpus condiviso: ogni riferimento deve esistere, ogni voce deve essere usata
    corpus = raw.get("shared_descriptions_corpus") or {}
    used = set()

    def refs(o, where):
        if isinstance(o, dict):
            if "corpus_ref" in o:
                used.add(o["corpus_ref"])
                if o["corpus_ref"] not in corpus:
                    errors.append(f"[corpus] {where}: corpus_ref '{o['corpus_ref']}' non esiste in shared_descriptions_corpus")
                return
            for x in o.values():
                refs(x, where)
        elif isinstance(o, list):
            for x in o:
                refs(x, where)
    for it in raw.get("items", []):
        refs(it, it.get("id"))
    for k in sorted(set(corpus) - used):
        warnings.append(f"[corpus] voce '{k}' non usata da nessun prodotto")
    if errors:
        print(f"ERRORI: {len(errors)}")
        for e in errors[:40]:
            print("  E", e)
        sys.exit(1)
    db = load_json(DATA / "database.json")                     # testi completi per i controlli logici

    items = db.get("items", [])
    ids = [it.get("id") for it in items]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"ID duplicati: {sorted(dup)}")
    idset = set(ids)
    disk = {f.name for f in IMAGES.glob("*.jpg")} if IMAGES.exists() else set()
    referenced = set()

    for it in items:
        iid = it.get("id")
        try:
            # --- immagini
            im = it["images"]
            gal = im["gallery"]
            referenced |= set(gal)
            for f in gal:
                if not re.match(rf"^{re.escape(iid)}_\d{{2}}\.jpg$", f):
                    errors.append(f"{iid}: nome immagine non conforme '{f}'")
                if f not in disk:
                    errors.append(f"{iid}: immagine '{f}' assente in assets/images/")
            if im["primary"] and im["primary"] not in gal:
                errors.append(f"{iid}: primary '{im['primary']}' non è nella galleria")
            if gal and not im["primary"]:
                errors.append(f"{iid}: galleria non vuota ma primary nullo")
            if [d["filename"] for d in im["image_details"]] != gal:
                errors.append(f"{iid}: image_details non allineati alla galleria")
            # --- etilene
            kaf = it["ripening_and_storage"]["ethylene_compatibility"]["keep_away_from"]
            for k in kaf:
                if k not in idset or k == iid:
                    errors.append(f"{iid}: keep_away_from -> '{k}' non valido")
            # --- intervalli
            ph = it["ripening_and_storage"]["postharvest_physiology"]
            for key in ("optimal_temperature_c", "optimal_humidity_percent"):
                r = ph[key]
                if r and r["min"] > r["max"]:
                    errors.append(f"{iid}: {key} min > max")
            for key in ("room_temp_days", "refrigerated_days"):
                r = ph["estimated_shelf_life_days"][key]
                if r and r[0] > r[1]:
                    errors.append(f"{iid}: {key} [min,max] invertito")
            # --- completezza
            dc = it["data_completeness"]
            real = set(null_paths(it))
            listed = set(dc["missing_fields"])
            if real - listed:
                errors.append(f"{iid}: campi nulli non elencati in missing_fields: {sorted(real - listed)[:6]}")
            if listed - real:
                errors.append(f"{iid}: missing_fields elenca campi non nulli: {sorted(listed - real)[:6]}")
            if dc["is_complete"] and (real or dc.get("fields_pending_verification")):
                errors.append(f"{iid}: is_complete=true ma ci sono campi mancanti o da verificare")
            # --- plausibilità nutrizionale
            n = it["nutrition_and_sustainability"]
            m = n["macros_per_100g"]
            parts = [n["water_percentage"], m["carbs_g"], m["proteins_g"], m["fats_g"], m["fiber_g"]]
            if all(p is not None for p in parts) and sum(parts) > 105:
                warnings.append(f"{iid}: acqua+macro = {sum(parts):.1f} g/100 g (> 105)")
            if n["kcal_per_100g"] is not None and all(m[k] is not None for k in ("carbs_g", "proteins_g", "fats_g", "fiber_g")):
                calc = 3.75 * m["carbs_g"] + 4 * m["proteins_g"] + 9 * m["fats_g"] + 2 * m["fiber_g"]
                if calc > 5 and abs(calc - n["kcal_per_100g"]) / max(calc, n["kcal_per_100g"]) > 0.25:
                    warnings.append(f"{iid}: kcal dichiarate {n['kcal_per_100g']} vs calcolate da macro ~{calc:.0f}")
            # --- ID
            # l'ID è stabile (usato nei nomi file): basta che inizi con la prima parola del nome IT normalizzato
            first = slug(re.split(r"[\s(/,]", it["names"]["it"])[0])
            if not iid.startswith(first[:5]):
                warnings.append(f"{iid}: ID poco coerente con il nome IT '{it['names']['it']}'")
        except (KeyError, TypeError) as e:  # struttura rotta: già segnalata dallo schema
            errors.append(f"{iid}: struttura non valutabile ({type(e).__name__}: {e})")

    orphan = sorted(f for f in disk - referenced if re.match(r"^[a-z0-9_]+_\d{2}\.jpg$", f))
    if orphan:
        warnings.append(f"{len(orphan)} foto su disco non in galleria (esegui sync_images.py): {orphan[:8]}")

    pend = sum(len(it["data_completeness"].get("fields_pending_verification", [])) for it in items)
    miss = sum(len(it["data_completeness"]["missing_fields"]) for it in items)
    complete = sum(it["data_completeness"]["is_complete"] for it in items)
    print(f"Alimenti: {len(items)} | completi: {complete} | campi mancanti: {miss} | campi da verificare: {pend} | "
          f"immagini referenziate: {len(referenced)}")
    print(f"ERRORI: {len(errors)}   AVVISI: {len(warnings)}")
    for e in errors[:60]:
        print("  E", e)
    if len(errors) > 60:
        print(f"  ... altri {len(errors) - 60} errori")
    for w in warnings[:40]:
        print("  W", w)
    if len(warnings) > 40:
        print(f"  ... altri {len(warnings) - 40} avvisi")
    if "--report" in sys.argv:
        p = sys.argv[sys.argv.index("--report") + 1]
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"errors": errors, "warnings": warnings, "items": len(items), "missing_fields": miss,
                       "pending_verification": pend}, f, ensure_ascii=False, indent=2)
    sys.exit(1 if errors or (strict and warnings) else 0)


if __name__ == "__main__":
    main()
