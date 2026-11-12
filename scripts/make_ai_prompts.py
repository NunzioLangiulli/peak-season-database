"""Prompts to generate the missing images with an AI model (data/ai_image_prompts.md).

For every product and each of the 5 view types with no valid current photo and no candidates, writes an English prompt
(generative models work better in English) with common name, scientific name and the style guidelines shared by
all the app's images. Generated images must be declared as such (provider "ai_generated") when they are
added to the database.
Usage:  python scripts/make_ai_prompts.py   (after find_image_candidates.py, and optionally after the selection)
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
LAB = {"full_frame": "Full-frame product", "isolated_background": "White or coloured background", "plant_in_field": "Plant",
       "botanical_plate": "Botanical plate", "cut_section": "Cut / cross-section"}
NO_CUT = {"erbe_spezie", "cereali"}


def main():
    db = load_json(db_path())
    cpath = IMAGES / "_candidates" / "candidates.json"
    cand = load_json(cpath)["items"] if cpath.exists() else {}
    L = ["# Prompts for AI-generated images\n",
         "Only for the image types that have neither a valid current photo nor candidates. Style shared by all prompts: "
         f"*{STYLE}*\n",
         "Generated images must be declared as such in the metadata (provider `ai_generated`, author = model used).\n"]
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
        L.append(f"## {it['names']['en']} ({it['names']['it']})\n")
        for t in miss:
            p = TYPE[t].format(en=en, sci=sci, plant=plant, where=where, bg="white" if n % 2 == 0 else "pale coloured")
            full = p if t == "botanical_plate" else f"{p} {STYLE}"
            L.append(f"- **{LAB[t]}**: `{full}`")
            n += 1
        L.append("")
    (DATA / "ai_image_prompts.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote data/ai_image_prompts.md:", n, "prompts")


if __name__ == "__main__":
    main()
