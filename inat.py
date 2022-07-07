import logging
from typing import Tuple

import aiohttp
from sentry_sdk import capture_message


COUNT = 5
OBSERVATIONS_URL = "https://api.inaturalist.org/v1/observations?photos=true&photo_licensed=true&rank=species&taxon_name={specimen}&quality_grade=research&per_page={count}&order_by=id&order=asc&id_above={last_id}"
IMAGE_URL = "https://inaturalist-open-data.s3.amazonaws.com/photos/{id}/medium.{ext}"

logger = logging.getLogger("treebo")

sciname_lookup = {}
with open("data/scinames.txt", "r") as f:
    for line in f.readlines():
        common, sci = line.split(",")
        sciname_lookup[common.strip()] = sci.strip()


async def get_urls(
    session: aiohttp.ClientSession,
    item: str,
    index: int,
    count: int = COUNT,
) -> Tuple[int, Tuple[str, ...]]:
    """Return URLS of images of the specimen to download.

    This method uses iNaturalist's API to fetch image urls. It will
    try up to 2 times to successfully retrieve URLS.

    `index` is the ID of the last observation that was downloaded.
    This function will try to return `images_to_download` number of
    images. The new ID is returned as the first element of the tuple.
    """
    sciname = sciname_lookup.get(item, item)
    if sciname == item:
        logger.info(f"no sciname found for {item}, falling back")
        capture_message(f"no sciname found for {item}")

    urls = []
    async with session.get(
        OBSERVATIONS_URL.format(specimen=sciname, count=count, last_id=index)
    ) as resp:
        observations = (await resp.json())["results"]

    if not observations:
        async with session.get(
            OBSERVATIONS_URL.format(specimen=sciname, count=count, last_id="")
        ) as resp:
            observations = (await resp.json())["results"]

    if not observations:
        return (0, tuple())

    logger.info(f"observation ids: {','.join([str(o['id']) for o in observations])}")
    for observation in observations:
        logger.info(f"observation at: {observation['observed_on']}")
        for photo in observation["photos"]:
            urls.append(
                IMAGE_URL.format(id=photo["id"], ext=photo["url"].split(".")[-1])
            )
    return (observations[-1]["id"], tuple(urls))
