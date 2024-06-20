import asyncio
import io
import os
from collections import deque
from typing import List
import random
import requests
import discord
from discord.ext import commands, tasks
from discord import app_commands
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

MY_GUILD = discord.Object(id=os.getenv("MY_GUILD"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


class VoiceManager:
    """Manages voice-related operations."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.voice_cache = []
        self.user_voices = {}
        self.session = requests.Session()

    def fetch_voices(self):
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        self.voice_cache = response.json().get('voices', [])

    def find_voice_by_name(self, name: str):
        return next((voice for voice in self.voice_cache if voice["name"] == name), None)

    def fetch_audio_stream(self, text: str, voice_id: str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        params = {
            "optimize_streaming_latency": 1
        }
        payload = {
            "model_id": "eleven_multilingual_v2",
            "text": text,
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = self.session.post(url, params=params, headers=headers, json=payload, stream=True)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except requests.RequestException as e:
            logger.error(f"Error fetching audio stream: {e}")
            return None


class MyBot(commands.Bot):
    def __init__(self, intents: discord.Intents, voice_manager: VoiceManager):
        super().__init__(command_prefix='!', intents=intents)
        self.voice_manager = voice_manager
        self.audio_queue = deque()

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        self.update_voice_cache.start()

    @tasks.loop(minutes=2)
    async def update_voice_cache(self):
        try:
            self.voice_manager.fetch_voices()
        except requests.RequestException as e:
            logger.error(f"Error updating voice cache: {e}")

    def play_next_audio(self, interaction: discord.Interaction, error=None):
        if error:
            logger.error(f'Player error: {error}')
        if self.audio_queue:
            audio_stream = self.audio_queue.popleft()
            audio_stream.seek(0)  # Ensure the stream is at the start
            source = discord.FFmpegPCMAudio(audio_stream, pipe=True)
            interaction.guild.voice_client.play(source, after=lambda e: self.play_next_audio(interaction, e))
        else:
            logger.info("No more audio in the queue.")


intents = discord.Intents.all()
voice_manager = VoiceManager(api_key=ELEVENLABS_API_KEY)
bot = MyBot(intents=intents, voice_manager=voice_manager)


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.tree.command(name='say', description='Plays a text-to-speech response from Eleven Labs')
@app_commands.describe(text='The text to be spoken')
async def say(interaction: discord.Interaction, text: str):
    try:
        await interaction.response.defer(thinking=True)

        if len(text) > 100:
            await interaction.followup.send(f'Max 100 chars. Your text is too long ({len(text)} chars).')
            return

        await ensure_voice_connection(interaction)
        voice = bot.voice_manager.user_voices.get(interaction.user.global_name, random.choice(bot.voice_manager.voice_cache))
        audio_stream = bot.voice_manager.fetch_audio_stream(text, voice['voice_id'])

        if audio_stream:
            bot.audio_queue.append(audio_stream)
            if not interaction.guild.voice_client.is_playing():
                bot.play_next_audio(interaction)
            await interaction.followup.send("Message queued")
        else:
            await interaction.followup.send("Failed to generate audio stream.")
    except Exception as e:
        logger.exception(e)


async def ensure_voice_connection(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None or not interaction.guild.voice_client.is_connected():
            await channel.connect()
        elif interaction.guild.voice_client.channel != channel:
            await interaction.guild.voice_client.move_to(channel)
    else:
        await interaction.followup.send('You are not in a voice channel.')


@bot.tree.command()
async def voice(interaction: discord.Interaction, voice: str):
    """Set user's voice"""
    await interaction.response.defer()
    global_name = str(interaction.user.global_name)
    selected_voice = next((v for v in bot.voice_manager.voice_cache if v['name'].lower() == voice.lower()), None)
    if not selected_voice:
        await interaction.followup.send('No voice found.')
        return
    bot.voice_manager.user_voices[global_name] = selected_voice
    await interaction.followup.send(f"Voice set to {selected_voice['name']}")


@voice.autocomplete('voice')
async def voices_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    voices_name = [voice["name"] for voice in bot.voice_manager.voice_cache if voice["category"] == "cloned"]

    return [
        app_commands.Choice(name=voice_name, value=voice_name)
        for voice_name in voices_name if current.lower() in voice_name.lower()
    ]


@bot.tree.command()
async def volume(interaction: discord.Interaction, volume: int):
    """Changes the bot volume"""
    if interaction.guild.voice_client is None:
        await interaction.response.send_message("Not connected to a voice channel.")
        return

    interaction.guild.voice_client.source.volume = volume / 100
    await interaction.response.send_message(f"Changed volume to {volume}%")


@bot.tree.command()
async def stop(interaction: discord.Interaction):
    """Stops and disconnects the bot from voice channel"""
    if interaction.guild.voice_client.channel:
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message("Disconnected from the voice channel.")
    else:
        await interaction.response.send_message("Not connected to a voice channel.")


async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
