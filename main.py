
import discord
from discord.ext import commands

import os

from data.services.user_service import user_service
from utils.config import cfg
from utils.context import BlooContext
from utils.database import db
from utils.logger import logger
from utils.misc import IssueCache, RuleCache
from utils.mod.filter import find_triggered_filters
from utils.misc import BanCache
from utils.permissions.permissions import permissions
from utils.tasks import Tasks


# Remove warning from songs cog
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

initial_extensions = [
    "cogs.monitors.filter",
    "cogs.monitors.antiraid",
    "cogs.commands.info.stats",
    "cogs.commands.info.devices",
    "cogs.commands.info.help",
    "cogs.commands.info.userinfo",
    "cogs.commands.info.tags",
    "cogs.commands.misc.admin",
    "cogs.commands.misc.genius",
    "cogs.commands.misc.giveaway",
    "cogs.commands.misc.ioscfw",
    "cogs.commands.misc.canister",
    "cogs.commands.misc.memes",
    "cogs.commands.misc.misc",
    "cogs.commands.misc.subnews",
    "cogs.commands.mod.antiraid",
    "cogs.commands.mod.filter",
    "cogs.commands.mod.modactions",
    "cogs.commands.mod.modutils",
    "cogs.monitors.applenews",
    "cogs.monitors.birthday",
    "cogs.monitors.blootooth",
    "cogs.monitors.boosteremojis",
    "cogs.monitors.logging",
    "cogs.monitors.role_assignment_buttons",
    "cogs.monitors.twitfix",
    "cogs.monitors.sabbath",
    "cogs.monitors.songs",
    "cogs.monitors.xp",
    "cogs.monitors.jailbreak_monitors",
    "cogs.monitors.unban_appeals",
]

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True
mentions = discord.AllowedMentions(everyone=False, users=True, roles=False)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = Tasks(self)

        # force the config object and database connection to be loaded
        if cfg and db and permissions:
            logger.info("Presetup phase completed! Connecting to Discord...")

    async def get_application_context(self, interaction: discord.Interaction, *, cls=BlooContext) -> BlooContext:
        return await super().get_application_context(interaction, cls=cls)

    async def process_application_commands(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id != cfg.guild_id:
            return

        if permissions.has(interaction.user.guild, interaction.user, 6):
            return await super().process_application_commands(interaction)

        db_user = user_service.get_user(interaction.user.id)
        if db_user.command_bans.get(interaction.data.get("name")):
            ctx = await self.get_application_context(interaction)
            await ctx.send_error("You are not allowed to use that command!")
            return

        options = interaction.data.get("options")
        if options is None or not options:
            return await super().process_application_commands(interaction)

        message_content = " ".join(
            [str(option.get("value") or "") for option in options])

        triggered_words = find_triggered_filters(
            message_content, interaction.user)

        if triggered_words:
            ctx = await self.get_application_context(interaction)
            await ctx.send_error("Your interaction contained a filtered word. Aborting!")
            return

        return await super().process_application_commands(interaction)


bot = Bot(intents=intents, allowed_mentions=mentions)


@bot.event
async def on_ready():
    bot.ban_cache = BanCache(bot)
    bot.issue_cache = IssueCache(bot)
    bot.rule_cache = RuleCache(bot)
    print("""
            88          88                          
            88          88                          
            88          88                          
            88,dPPYba,  88  ,adPPYba,   ,adPPYba,   
            88P'    "8a 88 a8"     "8a a8"     "8a  
            88       d8 88 8b       d8 8b       d8  
            88b,   ,a8" 88 "8a,   ,a8" "8a,   ,a8"  
            8Y"Ybbd8"'  88  `"YbbdP"'   `"YbbdP"'   
                """)
    logger.info(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Version: {discord.__version__}')
    logger.info(
        f'Made with ❤️ by SlimShadyIAm#9999 and the Bloo development team. Enjoy!')


if __name__ == '__main__':
    bot.remove_command("help")
    for extension in initial_extensions:
        bot.load_extension(extension)

bot.run(os.environ.get("BLOO_TOKEN"), reconnect=True)
