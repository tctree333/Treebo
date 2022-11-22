# other.py | misc. commands
# Copyright (C) 2019-2021  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

import aiohttp
from discord import app_commands
from discord.ext import commands
from sciolyid.data import get_aliases, possible_words
from sciolyid.util import better_spellcheck, cache
from sciolyid.functions import CustomCooldown

from treebo_functions import decrypt_chacha

logger = logging.getLogger("treebo")


class Treebo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    @cache()
    async def item_from_obs(obs_id: str):
        url = f"https://api.inaturalist.org/v1/observations/{obs_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                content = await resp.json()
                if resp.status != 200 or not content or len(content["results"]) != 1:
                    raise ValueError("Invalid observation ID")

                current_item = content["results"][0]["taxon"]["preferred_common_name"]

        logger.info(f"observation found for {obs_id}: {current_item}")
        return current_item, content["results"][0]["uri"]

    # Observation command - gives original iNaturalist observation from observation code
    @commands.hybrid_command(
        help="- Gives the original iNaturalist observation from an observation code",
        aliases=["source", "asset", "original", "orig", "obs"],
    )
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.user))
    @app_commands.describe(
        code="The asset code to search for.",
        name="The tree name that corresponds to the asset.",
    )
    async def observation(self, ctx: commands.Context, code: str, *, name: str):
        logger.info("command: observation")

        guess = name.lower().replace("-", " ").strip()
        if not guess:
            await ctx.send("Please provide the tree name to get the original asset.", ephemeral=True)
            return

        try:
            asset = str(int(decrypt_chacha(code).hex(), 16))
            current_item, url = await self.item_from_obs(asset)
        except:
            await ctx.send("**Invalid asset code!**", ephemeral=True)
            return

        correct_list = (x.lower() for x in get_aliases(current_item))
        correct = better_spellcheck(guess, correct_list, possible_words)
        if correct or ((await self.bot.is_owner(ctx.author)) and guess == "please"):
            await ctx.send(f"**Here you go!**\n{url}")
        else:
            await ctx.send(
                f"**Sorry, that's not the correct tree.**\n*Please try again.*", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Treebo(bot))
