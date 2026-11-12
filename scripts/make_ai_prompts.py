"""Prompt per generare con un modello di AI le immagini che mancano (data/ai_image_prompts.md).

Per ogni alimento e per ciascuno dei 5 tipi senza foto attuale valida né candidate, scrive un prompt in inglese
(i modelli generativi rendono meglio in inglese) con nome comune, nome scientifico e indicazioni di stile comuni a
tutte le immagini dell'app. Le immagini generate vanno dichiarate come tali (provider "ai_generated") quando le
aggiungeremo al database.
Uso:  python scripts/make_ai_prompts.py   (dopo find_image_candidates.py, ed eventualmente dopo la scelta)
"""
from common import DATA, IMAGES, load_json
from find_image_candidates import db_path

STYLE = ("Photorealistic, natural vivid colours, soft diffuse daylight, sharp focus, high resolution, landscape 3:2 format. "
         "No plates, no bowls, no cooked food, no hands, no text, no labels, no logos, no watermark.")
TYPE = {
    "full_frame": "Close-up of many fresh {en} ({sci}) filling the entire frame edge to edge, no background visible.",
    "isolated_background": "A few fresh {en} ({sci}) on a plain seamless {bg} background, studio product photo, soft shadow.",
    "plant_in_field": "The living {plant} of {en} ({sci}) growing outdoors {where}, showing leaves and the edible part ready for harvest; professional nature photography, not only flowers.",
    "botanical_plate": "Vintage botanical illustration plate of {sci} ({en}) in the style of 19th-century scientific engravings: whole plant with roots, leaves, flowers, fruit and seed details, numbered parts, on aged cream paper. Portrait format allowed.",
    "cut_section": "Fresh {en} ({sci}) cut in half showing the cross-section and inner structure, next to a whole one, on a plain light background.",
}
LAB = {"full_frame": "Prodotto a tutto campo", "isolated_background": "Sfondo bianco o colorato", "plant_in_field": "Pianta",
       "botanical_plate": "Tavola botanica", "cut_section": "Tagliato / sezione"}
NO_CUT = {"erbe_spezie", "cereali"}


def main():
    db = load_json(db_path())
    cpath = IMAGES / "_candidates" / "candidates.json"
    cand = load_json(cpath)["items"] if cpath.exists() else {}
    L = ["# Prompt per immagini generate con AI\n",
         "Solo per i tipi di immagine per cui non abbiamo né una foto attuale valida né candidate. Stile comune a tutti i prompt: "
         f"*{STYLE}*\n",
         "Le immagini generate andranno indicate come tali nei metadati (provider `ai_generated`, autore = modello usato).\n"]
    n = 0
    for it in db["items"]:
        have = {d["view_type"] for d in it["images"]["image_details"] if not d.get("flags")}
        miss = [t for t in TYPE if t not in have and not cand.get(it["id"], {}).get(t)
                and not (t == "cut_section" and it["category"] in NO_CUT)]
        if not miss:
            continue
        en = it["names"]["en"].split("(")[0].strip().lower()
        sci = it["botany"]["scientific_name"] or ""
        plant = "tree" if it["category"] == "frutta" else ("fungus" if it["category"] == "funghi" else "plant")
        where = "in a forest floor" if it["category"] == "funghi" else ("in an orchard" if it["category"] == "frutta" else "in a vegetable garden")
        L.append(f"## {it['names']['it']} ({it['names']['en']})\n")
        for t in miss:
            p = TYPE[t].format(en=en, sci=sci, plant=plant, where=where, bg="white" if n % 2 == 0 else "pale coloured")
            full = p if t == "botanical_plate" else f"{p} {STYLE}"
            L.append(f"- **{LAB[t]}**: `{full}`")
            n += 1
        L.append("")
    (DATA / "ai_image_prompts.md").write_text("\n".join(L), encoding="utf-8")
    print("scritto data/ai_image_prompts.md:", n, "prompt")


if __name__ == "__main__":
    main()
