import discord
import requests
import os
from discord.ext import commands, tasks
from typing import Dict, Optional

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "PUT_YOUR_BOT_TOKEN_HERE",
)
DISCORD_GUILD_ID = int(
    os.getenv("DISCORD_GUILD_ID", "PUT_YOUR_GUILD_ID_HERE")
)  # Replace with your guild ID
WOM_GROUP_ID = int(
    os.getenv("WOM_GROUP_ID", "PUT_YOUR_WOM_GROUP_ID_HERE")
)  # Replace with your WOM group ID
WOM_API_KEY = os.getenv(
    "WOM_API_KEY", "PUT_YOUR_WOM_API_KEY_HERE"
)  # Replace with your WOM API key
CREATE_MISSING_ROLES = True
REMOVE_WOM_ROLES_NOT_ASSIGNED = True
ROLE_CREATION_CASING = "title"
WOM_ROLE_NAMES = {"Squire", "Knight", "Owner"}  # change this to your WOM/clan roles

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def get_wom_members() -> Dict[str, str]:
    """
    Fetches the Wise Old Man group members and their roles.

    Returns:
        Dict[str, str]: A dictionary mapping usernames (lowercase) to their WOM role.
    """
    url = f"https://api.wiseoldman.net/v2/groups/{WOM_GROUP_ID}"
    headers = {"x-api-key": f"{WOM_API_KEY}"} if WOM_API_KEY else {}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching WOM group members: {e}")
        return {}
    memberships = resp.json().get("memberships", [])
    return {m["player"]["username"].lower(): m["role"] for m in memberships}


async def sync_wom_roles(guild: discord.Guild) -> None:
    """
    Synchronizes Discord roles with WOM group roles for all guild members.

    Args:
        guild (discord.Guild): The Discord guild to sync roles in.
    """
    perms = guild.me.guild_permissions
    if not perms.manage_roles:
        print("Missing required permissions: Manage Roles")
        return

    wom_lookup = get_wom_members()
    if not wom_lookup:
        print("No members found in WOM group")
        return

    discord_roles = {role.name: role for role in guild.roles}
    updated_members = 0

    for member in guild.members:
        possible_names = {member.display_name.lower(), member.name.lower()}
        wom_role_name: Optional[str] = None
        for name in possible_names:
            if name in wom_lookup:
                wom_role_name = wom_lookup[name]
                break
        if not wom_role_name:
            continue

        # Case-insensitive WOM role check
        if wom_role_name.lower() not in {role.lower() for role in WOM_ROLE_NAMES}:
            continue

        # Apply casing if creating a new role
        role_name_to_create = wom_role_name
        if ROLE_CREATION_CASING == "lower":
            role_name_to_create = wom_role_name.lower()
        elif ROLE_CREATION_CASING == "title":
            role_name_to_create = wom_role_name.title()

        # Try to find the role case-insensitively
        discord_role = next(
            (
                r
                for n, r in discord_roles.items()
                if n.lower() == role_name_to_create.lower()
            ),
            None,
        )
        if not discord_role and CREATE_MISSING_ROLES:
            try:
                discord_role = await guild.create_role(name=role_name_to_create)
                discord_roles[role_name_to_create] = discord_role
            except Exception as e:
                print(f"Failed to create role {role_name_to_create}: {e}")
                continue
        elif not discord_role:
            continue

        # Remove other WOM roles from the member (if enabled)
        if REMOVE_WOM_ROLES_NOT_ASSIGNED:
            roles_to_remove = [
                role
                for role in member.roles
                if role.name.lower() in {r.lower() for r in WOM_ROLE_NAMES}
                and role != discord_role
            ]
        else:
            roles_to_remove = []

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            if discord_role not in member.roles:
                await member.add_roles(discord_role)
                updated_members += 1
        except Exception as e:
            print(f"Failed to update roles for {member.display_name}: {e}")

    print(f"Automated sync complete! Updated {updated_members} member(s).")


@bot.event
async def on_ready() -> None:
    """
    Event handler called when the bot is ready.
    Syncs slash commands and starts the automated WOM sync task.
    """
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) to Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    guild = bot.get_guild(DISCORD_GUILD_ID)
    if guild and not wom_sync_task.is_running():
        wom_sync_task.start()


@tasks.loop(minutes=5)
async def wom_sync_task() -> None:
    """
    Automated task that syncs WOM roles every 5 minutes.
    """
    guild = bot.get_guild(DISCORD_GUILD_ID)
    if guild:
        await sync_wom_roles(guild)
    else:
        print("Guild not found for automated sync.")


@bot.tree.command(
    name="sync-wom-ranks", description="Sync WOM roles with Discord members"
)
async def syncwom(interaction: discord.Interaction) -> None:
    """
    Slash command to manually sync WOM roles with Discord members.

    Args:
        interaction (discord.Interaction): The interaction object from Discord.
    """
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Guild not found!")
        return

    await sync_wom_roles(guild)
    await interaction.followup.send("Manual sync complete!")


if __name__ == "__main__":
    if not BOT_TOKEN or not WOM_API_KEY:
        print("Missing BOT_TOKEN or WOM_API_KEY in environment variables.")
    else:
        bot.run(BOT_TOKEN)

if not wom_sync_task.is_running():
    wom_sync_task.start()
