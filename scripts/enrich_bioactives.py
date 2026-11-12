"""Composti bioattivi misurati: carotenoidi non provitaminici da USDA FoodData Central SR Legacy (CSV ufficiale 2018-04,
data/raw/fdc_sr_legacy/sr_legacy.zip, https://fdc.nal.usda.gov/download-datasets).

Le tabelle italiane (CREA, BDA-IEO) non riportano licopene, luteina, zeaxantina, alfa-carotene e beta-criptoxantina;
USDA li misura per la maggior parte di frutta e verdura crude. Fonte non italiana, dichiarata nel campo source.
I composti della bozza (antocianine, alliina, capsaicina, ecc. con quantità senza fonte) non sono verificabili sulle
fonti del progetto: vanno in draft_legacy_values.json; se il composto coincide con un carotenoide USDA si registra
la discrepanza.
Uso:  python scripts/enrich_bioactives.py
"""
import csv
import io
import zipfile

from common import CONFIG, DATA, RAW, add_discrepancy, finalize_completeness, load_json, mark_enriched, save_json

ZIP = RAW / "fdc_sr_legacy" / "sr_legacy.zip"
PRE = "FoodData_Central_sr_legacy_food_csv_2018-04/"
NUTR = {"337": ("Licopene", "Lycopene"), "338": ("Luteina + zeaxantina", "Lutein + zeaxanthin"),
        "322": ("Alfa-carotene", "Alpha-carotene"), "334": ("Beta-criptoxantina", "Beta-cryptoxanthin")}
DRAFT_SAME = {"licopene": "337", "luteina": "338", "luteina e zeaxantina": "338", "zeaxantina e luteina": "338"}
# id alimento -> (fdc_id, corrispondenza)
FDC = {
    "aglio_garlic": 169230, "asparago_asparagus": 168389, "carciofo_artichoke": 169205, "carota_carrot": 170393,
    "barbabietola_beetroot": 169145, "bietola_da_coste_swiss_chard": 169991, "bietola_da_taglio_leaf_beet": (170375, "approx"),
    "cardo_cardoon": 169981, "cavoletto_di_bruxelles_brussels_sprout": 170383, "cavolfiore_cauliflower": 169986,
    "broccolo_broccoli": 170379, "cavolo_cappuccio_cabbage": 169975, "cavolo_nero_black_kale": (168421, "approx"),
    "cavolo_rapa_kohlrabi": 168424, "cavolo_verza_savoy_cabbage": 170388, "cece_chickpea": 173756, "cetriolo_cucumber": 168409,
    "cicoria_da_cespo_chicory": (169992, "approx"), "cicoria_da_taglio_cutting_chicory": 169992,
    "cima_di_rapa_turnip_greens": 170381, "cipolla_estiva_summer_onion": 170000, "cipolla_invernale_winter_onion": 170000,
    "fagiolo_bean": (175189, "approx"), "fagiolino_green_bean": 169961, "fava_broad_bean": 170377, "finocchio_fennel": 169385,
    "lattuga_da_cespo_head_lettuce": (168429, "approx"), "lattuga_da_taglio_leaf_lettuce": 169249, "lenticchia_lentil": 172420,
    "melanzana_eggplant": 169228, "pastinaca_parsnip": 170417, "patata_potato": 170026, "peperone_bell_pepper": 170108,
    "pisello_pea": 170419, "pomodoro_tomato": 170457, "porro_leek": 169246, "radicchio_radicchio": 168564, "rapa_turnip": 170465,
    "ravanello_radish": 169276, "rucola_arugula": 169387, "scalogno_shallot": 170499, "sedano_celery": 169988,
    "spinacio_spinach": 168462, "topinambur_jerusalem_artichoke": 169236, "valerianella_corn_salad": 169219,
    "zucca_pumpkin": 168448, "zucchina_zucchini": 169291, "arachide_peanut": 172430, "anguria_watermelon": 167765,
    "melone_melon": (169092, "approx"), "albicocca_apricot": 171697, "arancia_orange": 169097, "cachi_persimmon": 169941,
    "castagna_chestnut": 170575, "ciliegia_cherry": 171719, "clementine_clementine": 168195, "fico_fig": 173021,
    "fragola_strawberry": 167762, "kiwi_kiwifruit": 168153, "lampone_raspberry": 167755, "limone_lemon": 167746,
    "mandarino_mandarin": 169105, "mela_apple": 171688, "melograno_pomegranate": 169134, "mirtillo_blueberry": 171711,
    "mora_blackberry": 173946, "pera_pear": 169118, "pesca_peach": 169928, "susina_plum": 169949, "uva_table_grape": 174683,
    "banana_banana": 173944, "mango_mango": 169910, "avocado_avocado": 171705, "basilico_basil": 172232,
    "peperoncino_chili_pepper": 170106, "prezzemolo_parsley": 170416, "rosmarino_rosemary": 173473, "timo_thyme": 173470,
    "menta_mint": (173475, "approx"), "fungo_champignon_button_mushroom": 169251, "fungo_pleurotus_oyster_mushroom": 168580,
    "mais_corn": 169998, "orzo_barley": 170284, "grano_duro_durum_wheat": 169721, "riso_rice": (169760, "approx"),
    "grano_saraceno_buckwheat": 170286, "cavolo_rosso_red_cabbage": 169977, "sedano_rapa_celeriac": 170400,
    "indivia_belga_belgian_endive": 170404, "scarola_escarole": 168412, "indivia_riccia_curly_endive": 168412,
    "nespola_loquat": 169908, "pompelmo_grapefruit": 173033, "mela_cotogna_quince": 168163, "ribes_redcurrant": 173964,
    "pesca_noce_nectarine": 169914, "fico_d_india_prickly_pear": 167750, "litchi_lychee": 169086, "lime_lime": 168155,
    "ananas_pineapple": 169124, "papaya_papaya": 169926, "maracuja_passion_fruit": 169108,
}
# alimenti aggiunti il 2026-11-05 (config/new_items_2026_11_05.json)
FDC.update({k: (v["fdc_id"][0], v["fdc_id"][1]) for k, v in load_json(CONFIG / "new_items_2026_11_05.json").items() if v.get("fdc_id")})


def load():
    z = zipfile.ZipFile(ZIP)
    rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(PRE + n), encoding="utf-8"))  # noqa: E731
    desc = {f["fdc_id"]: f["description"] for f in rd("food.csv")}
    nid = {n["id"]: n["nutrient_nbr"] for n in rd("nutrient.csv") if n["nutrient_nbr"] in NUTR}
    want = {str(v[0] if isinstance(v, tuple) else v) for v in FDC.values()}
    vals = {}
    for r in rd("food_nutrient.csv"):
        if r["fdc_id"] in want and r["nutrient_id"] in nid:
            vals.setdefault(r["fdc_id"], {})[nid[r["nutrient_id"]]] = float(r["amount"])
    return desc, vals


def main():
    desc, vals = load()
    db = load_json(DATA / "database.json")
    legacy = load_json(DATA / "draft_legacy_values.json")
    P = "nutrition_and_sustainability.bioactive_compounds"
    n_items = n_comp = 0
    for it in db["items"]:
        n = it["nutrition_and_sustainability"]
        old = [c for c in (n.get("bioactive_compounds") or []) if c.get("source") == "user_draft"]
        if old:
            legacy["items"].setdefault(it["id"], {})[P] = old
        m = FDC.get(it["id"])
        new = []
        if m:
            fid, match = (m if isinstance(m, tuple) else (m, "exact"))
            v = vals.get(str(fid), {})
            for nb in ("337", "338", "322", "334"):
                if v.get(nb):
                    it_n, en_n = NUTR[nb]
                    new.append({"name": it_n, "name_en": en_n, "amount": v[nb], "unit": "µg", "percent_nrv": None, "source": "usda_fdc"})
            for c in old:
                nb = DRAFT_SAME.get(c["name"].lower())
                if nb and v.get(nb) and c.get("unit") == "µg" and abs(c["amount"] - v[nb]) > 0.2 * v[nb]:
                    add_discrepancy(it, P, f"{c['name']} {c['amount']} µg", f"{NUTR[nb][0]} {v[nb]} µg",
                                    f"USDA FDC SR Legacy fdcId {fid}")
            url = f"https://fdc.nal.usda.gov/food-details/{fid}/nutrients"
            if url not in it["sources_by_topic"]["other_urls"]:
                it["sources_by_topic"]["other_urls"].append(url)
            it["sources_by_topic"].setdefault("source_codes", {})["usda_fdc"] = {"fdc_id": fid, "description": desc.get(str(fid)), "match": match}
        n["bioactive_compounds"] = new
        dropped = [c["name"] for c in old if not DRAFT_SAME.get(c["name"].lower())]
        note = " Composti bioattivi: " + (f"carotenoidi da USDA FDC SR Legacy fdcId {m if not isinstance(m, tuple) else m[0]} "
                                          f"('{desc.get(str(m if not isinstance(m, tuple) else m[0]))}', fonte non italiana)" if m else
                                          "nessuna fonte del progetto li misura")
        if dropped:
            note += f"; composti della bozza non verificabili ({', '.join(dropped)}) spostati in draft_legacy_values"
        it["data_completeness"]["notes"] += note + "."
        mark_enriched(it, [P])
        finalize_completeness(it)
        n_items += bool(new)
        n_comp += len(new)
    save_json(DATA / "database.json", db)
    save_json(DATA / "draft_legacy_values.json", legacy)
    print(f"alimenti con carotenoidi USDA: {n_items}, valori: {n_comp}")


if __name__ == "__main__":
    main()
