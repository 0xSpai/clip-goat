from discord_webhook import DiscordWebhook, DiscordEmbed
from modules.util.auth import discord_webhook
from datetime import datetime

def error(string):
    content = "@everyone"
    allowed_mentions = {
    "parse": ["everyone"],
    }
    embed = DiscordEmbed(
        title="Error Notification",
        color=0xFF0000,
    )
    embed.add_embed_field(name="Error", value=str(string), inline=False)
    embed.add_embed_field(
        name="Timestamp", value=datetime.utcnow().isoformat() + "Z", inline=False
    )

    webhook = DiscordWebhook(url=discord_webhook, content=content, allowed_mentions=allowed_mentions)
    webhook.add_embed(embed)
    webhook.execute()

def success(string):
    content = "@everyone"
    allowed_mentions = {
    "parse": ["everyone"],
    }
    embed = DiscordEmbed(
        title="Video Uploaded",
        color=0x00FF00,
    )
    embed.add_embed_field(name="Video details", value=str(string), inline=False)

    webhook = DiscordWebhook(url=discord_webhook, content=content, allowed_mentions=allowed_mentions)
    webhook.add_embed(embed)
    webhook.execute()