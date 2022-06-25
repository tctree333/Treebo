import logging
from typing import List, Tuple, Optional

import aiohttp
from sciolyid.util import cache


COUNT = 5
OBSERVATIONS_URL = "https://api.inaturalist.org/v1/observations?photos=true&photo_licensed=true&rank=species&taxon_name={specimen}&quality_grade=research&per_page={count}&order_by=id&order=asc&id_above={last_id}"
IMAGE_URL = "https://inaturalist-open-data.s3.amazonaws.com/photos/{}/medium.jpg"

logger = logging.getLogger("forestree")


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
    urls = []
    async with session.get(
        OBSERVATIONS_URL.format(specimen=item, count=count, last_id=index)
    ) as resp:
        observations = (await resp.json())["results"]

    if not observations:
        async with session.get(
            OBSERVATIONS_URL.format(specimen=item, count=count, last_id="")
        ) as resp:
            observations = (await resp.json())["results"]

    if not observations:
        return (0, tuple())

    for observation in observations:
        for photo in observation["photos"]:
            urls.append(IMAGE_URL.format(photo["id"]))
    return (observations[-1]["id"], tuple(urls))
