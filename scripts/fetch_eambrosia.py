"""Downloads all Italian geographical indications (PDO/PGI/TSG) from the EU eAmbrosia register -> data/raw/eambrosia_it.json

Public API used by the page https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/
(POST .../eambrosia-public-api/api/gi-applications/filter, body with a 'filters' list and first/rows pagination).
Usage:  python scripts/fetch_eambrosia.py
"""
from common import RAW, SESSION, save_json

URL = "https://ec.europa.eu/geographical-indications-register/eambrosia-public-api/api/gi-applications/filter"


def body(first, rows):
    f = lambda n, v: {"fieldName": n, "fieldValue": v}  # noqa: E731
    return {"cnCode": [], "filters": [f("geographicalIndicatorTypeId", []), f("qualityProductTypeId", []), f("countryAreaId", []),
                                       f("countryId", ["it"]), f("applicationTypeId", []), f("statusId", []),
                                       f("protectedName", None), f("fileName", None), f("producerGroupName", None), f("cnCode", None)],
            "first": first, "lang": "it", "sortField": "statusDate", "sortOrder": -1, "rows": rows, "registerId": None, "cnCodes": []}


def main():
    out, first, total = [], 0, None
    while total is None or first < total:
        j = SESSION.post(URL, json=body(first, 100), timeout=90).json()
        total = j["count"]
        res = j.get("results", [])
        if not res:
            break
        out += res
        first += len(res)
        print(f"{len(out)}/{total}")
    keep = ["id", "appUniqueId", "protectedName", "geographicalIndicatorTypeCode", "geographicalIndicatorType", "qualityProductType",
            "productCategory", "status", "registrationDate", "fileName", "countryId"]
    save_json(RAW / "eambrosia_it.json", {"_source": URL, "count": total,
                                          "items": [{k: r.get(k) for k in keep} for r in out]})
    print("saved", len(out), "entries; countries:", sorted({r.get("countryId") for r in out}))


if __name__ == "__main__":
    main()
