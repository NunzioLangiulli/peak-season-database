"""Regole dei claim nutrizionali UE per l'app (revisione 2026-11-13, richiesta dell'utente). Idempotente.

1. Ogni vitamina e minerale (nutrition_and_sustainability.vitamins / minerals) riceve una chiave stabile "key"
   (vitamin_c, folate, potassium...), indipendente dal nome mostrato.
2. metadata.nutrition_claims_eu_rules descrive ogni claim presente nel database (testo IT esatto di
   nutrition_claims_eu.it): gruppo del Reg. CE 1924/2006 (senza / a bassissimo contenuto / a basso contenuto / ad alto
   contenuto / fonte di), nutriente (chiavi dei macronutrienti senza _g, "kcal" per l'energia, "salt" per sodio/sale, key
   dei micronutrienti) e tono (favorable = claim positivo; warning = contenuto alto da tenere d'occhio, oggi non usato).
L'app raggruppa i claim, colora i riquadri dei macronutrienti e mette in evidenza le barre delle vitamine con un claim.
Uso:  python scripts/build_nutrition_claims_rules.py   (dopo gli script dei claim, prima di title_case_labels.py)
"""
import re

from common import DATA, load_json, save_json

KEYS = {  # nome IT dell'elenco (senza la parte tra parentesi) -> chiave
    "Vitamina A": "vitamin_a", "Tiamina": "thiamin", "Riboflavina": "riboflavin", "Niacina": "niacin", "Vitamina B6": "vitamin_b6",
    "Folati": "folate", "Folato": "folate", "Vitamina B12": "vitamin_b12", "Vitamina C": "vitamin_c", "Vitamina D": "vitamin_d",
    "Vitamina E": "vitamin_e", "Vitamina K": "vitamin_k", "Acido Pantotenico": "pantothenic_acid", "Biotina": "biotin",
    "Calcio": "calcium", "Ferro": "iron", "Fosforo": "phosphorus", "Magnesio": "magnesium", "Potassio": "potassium",
    "Sodio": "sodium", "Zinco": "zinc", "Rame": "copper", "Manganese": "manganese", "Selenio": "selenium", "Iodio": "iodine",
    "Cloruro": "chloride", "Fluoruro": "fluoride", "Cromo": "chromium", "Molibdeno": "molybdenum",
}
MACRO = {  # parola del claim -> (nutriente, etichetta IT, EN)
    "grassi": ("fats", "Grassi", "Fat"), "zuccheri": ("sugars", "Zuccheri", "Sugars"), "sodio": ("salt", "Sodio/Sale", "Sodium/Salt"),
    "sale": ("salt", "Sodio/Sale", "Sodium/Salt"), "fibre": ("fiber", "Fibre", "Fibre"), "proteine": ("proteins", "Proteine", "Protein"),
    "calorico": ("kcal", "Calorie", "Energy"), "calorie": ("kcal", "Calorie", "Energy"),
}
GROUPS = {
    "free": {"label": {"it": "Senza", "en": "Free of"}, "order": 1},
    "very_low": {"label": {"it": "A Bassissimo Contenuto di", "en": "Very Low in"}, "order": 2},
    "low": {"label": {"it": "A Basso Contenuto di", "en": "Low in"}, "order": 3},
    "high": {"label": {"it": "Ad Alto Contenuto di", "en": "High in"}, "order": 4},
    "source": {"label": {"it": "Fonte di", "en": "Source of"}, "order": 5},
}
PREFIX = [(r"^senza\b", "free"), (r"^a bassissimo contenuto", "very_low"), (r"^a basso contenuto", "low"),
          (r"^ad alto contenuto", "high"), (r"^fonte di", "source")]


def key_of(name):
    base = re.sub(r"\s*\(.*\)\s*$", "", name or "").strip()
    return KEYS.get(base) or KEYS.get(base.title())


def parse(claim_it, micro_names):
    low = claim_it.lower()
    grp = next((g for rx, g in PREFIX if re.search(rx, low)), None)
    if not grp:
        return None
    for w, (k, it, en) in MACRO.items():
        if re.search(rf"\b{w}\b", low):
            return {"group": grp, "nutrient": k, "nutrient_label": {"it": it, "en": en}}
    for k, (it, en) in micro_names.items():
        if re.search(rf"\b{re.escape(it.lower())}\b", low):
            return {"group": grp, "nutrient": k, "nutrient_label": {"it": it, "en": en}}
    return None


def main():
    db = load_json(DATA / "database.json")
    micro, missing = {}, set()
    for it in db["items"]:
        n = it["nutrition_and_sustainability"]
        for x in n.get("vitamins", []) + n.get("minerals", []):
            k = key_of(x.get("name"))
            if not k:
                missing.add(x.get("name"))
                continue
            x["key"] = k
            short_it = re.sub(r"\s*\(.*\)\s*$", "", x["name"]).strip()
            short_en = re.sub(r"\s*\(.*\)\s*$", "", x.get("name_en") or short_it).strip()
            micro.setdefault(k, (short_it, short_en))
    micro.setdefault("folate", ("Folato", "Folate"))
    names = dict(micro)
    names["folate"] = ("Folato", "Folate")            # nei claim si usa il singolare
    claims, unknown = {}, []
    for it in db["items"]:
        cl = it["nutrition_and_sustainability"].get("nutrition_claims_eu") or {}
        for c_it, c_en in zip(cl.get("it") or [], cl.get("en") or []):
            if c_it in claims:
                continue
            r = parse(c_it, names)
            if not r:
                unknown.append(c_it)
                continue
            claims[c_it] = {**r, "tone": "favorable", "en": c_en}
    db["metadata"]["nutrition_claims_eu_rules"] = {
        "description": {
            "it": "Claim nutrizionali del Reg. CE 1924/2006 presenti nel database: per ogni testo (nutrition_claims_eu.it) il gruppo, il "
                  "nutriente e il tono. Nutrienti: chiavi di macros_per_100g senza _g, kcal per l'energia, salt per sodio e sale, key di "
                  "vitamins/minerals per i micronutrienti. Tono: favorable = claim positivo; warning = contenuto alto da tenere d'occhio.",
            "en": "Nutrition claims of Reg. EC 1924/2006 found in the database: for each text (nutrition_claims_eu.it) the group, the nutrient "
                  "and the tone. Nutrients: macros_per_100g keys without _g, kcal for energy, salt for sodium and salt, vitamins/minerals key "
                  "for micronutrients. Tone: favorable = positive claim; warning = high content to watch."},
        "groups": GROUPS,
        "tones": {"favorable": {"it": "Favorevole", "en": "Favourable"}, "warning": {"it": "Da Tenere d'Occhio", "en": "To Watch"}},
        "nutrient_keys": {k: {"it": v[0], "en": v[1]} for k, v in sorted(micro.items())},
        "claims": dict(sorted(claims.items())),
    }
    save_json(DATA / "database.json", db)
    print(f"claim: {len(claims)}; non riconosciuti: {unknown}; micronutrienti senza chiave: {sorted(missing)}")


if __name__ == "__main__":
    main()
