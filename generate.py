# A script for generating family lists and specimen aliases from a list of specimens (common or scientific name)

SEARCH_URL = "https://api.inaturalist.org/v1/taxa?q={}&is_active=true&rank=species&all_names=true"
TAXON_URL = "https://api.inaturalist.org/v1/taxa/{}"

import requests
import time
from typing import Dict, List

headers = {
    "User-Agent": "SciOlyID",
}

with open("list.txt", "r") as f:
    data = f.readlines()

wikipedia: Dict[str, str] = {}
aliases: Dict[str, List[str]] = {}
families: Dict[str, List[str]] = {}
family_alias: Dict[str, str] = {}

family_ids: Dict[int, str] = {}

try:
    for specimen in data:
        print("specimen:", specimen.strip())
        url = SEARCH_URL.format(specimen.strip())
        r = requests.get(
            url,
            headers=headers,
        )
        returned = r.json()["results"][0]
        name = returned["preferred_common_name"].lower()
        wikipedia[name] = returned["wikipedia_url"]
        aliases[name] = [
            n["name"].lower()
            for n in returned["names"]
            if (n["locale"] == "sci" or n["locale"] == "en") and n["name"] != name
        ]

        specimen_family_ids = returned["ancestor_ids"]
        intersection = set(specimen_family_ids).intersection(set(family_ids.keys()))
        if len(intersection) == 0:
            print("fetching taxon")
            time.sleep(1)
            taxon_r = requests.get(
                TAXON_URL.format(",".join(map(str, specimen_family_ids)))
            )
            taxon_results = taxon_r.json()["results"]
            for taxon in taxon_results:
                if taxon["rank"] != "family":
                    continue
                family_name = taxon["name"].lower()
                print("found:", family_name)
                family_alias[family_name] = taxon["preferred_common_name"].lower()

                family_ids[taxon["id"]] = family_name
                families[family_name] = [name]
        else:
            families[family_ids[intersection.pop()]].append(name)

        time.sleep(1)


except Exception as e:
    print(e)
    pass

finally:
    with open("data/wikipedia.txt", "w") as f:
        for specimen, url in wikipedia.items():
            f.write(f"{specimen},{url}\n")

    with open("data/family_aliases.txt", "w") as f:
        for family, alias in family_alias.items():
            f.write(f'"{family}":["{alias}"],\n')

    for family, specimens in families.items():
        with open(f"data/categories/{family.lower()}.txt", "w") as f:
            for specimen in specimens:
                f.write(f"{specimen},{','.join(aliases[specimen])}\n")
