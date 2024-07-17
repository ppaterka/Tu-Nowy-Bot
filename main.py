import os
import discord
import math
import asyncio
import yt_dlp
from asyncio import sleep
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
file_names = ['main.py', '.env', 'requirements.txt', 'venv']
directory = os.path.dirname(__file__)
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
prefix = ';'

bot = commands.Bot(command_prefix=prefix, intents=intents, description='Tu Nowy Bot', help_command=None)


ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'outtmpl': directory + '/%(title)s.%(ext)s'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)


class YTDL(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


# Bot commands
@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(title='Help', description='Commands:')
    embed.add_field(name=f'{prefix}sqrt <number>', value='Counts square root of number')
    embed.add_field(name=f'{prefix}clear <number>', value='Deletes messages')
    embed.add_field(name=f'{prefix}kick <user> "<reason>"', value='Kicks user')
    embed.add_field(name=f'{prefix}ban <user> "<reason>"', value='Bans user')
    embed.add_field(name=f'{prefix}unban <user>', value='Unbans user')
    embed.add_field(name=f'{prefix}play <url or title>', value='Plays song')
    embed.add_field(name=f'{prefix}stop', value='Stops song')
    await ctx.send(content=None, embed=embed)
    
    
@bot.command(name="play")
async def play(ctx, *url):
    voice_channel = ctx.author.voice.channel
    vc = get(ctx.bot.voice_clients, guild=ctx.guild)
    if vc:
        await ctx.send('Bot is playing right now! Stop it to play another song.')
    else:
        if voice_channel is not None:
            await voice_channel.connect()
            vc = get(ctx.bot.voice_clients, guild=ctx.guild)
            arguments = []
            for argument in url:
                arguments.append(argument)
            url_string = ' '.join(arguments)
            song = await YTDL.from_url(url_string, loop=bot.loop)
            vc.play(discord.FFmpegPCMAudio(source=song))
            file = os.path.split(song)
            filename = file[1].split('.')[0]
            await ctx.send(f'Playing: {filename.replace("_", " ")}')
            while vc.is_playing():
                await sleep(.1)
            else:
                await vc.disconnect()
                for files in os.listdir(directory):
                    if files not in file_names:
                        filepath = os.path.join(directory, files)
                        os.remove(filepath)
        else:
            await ctx.send(str(ctx.author.name) + 'is not in a channel.')


@bot.command(name='stop')
async def stop(ctx):
    vc = get(ctx.bot.voice_clients, guild=ctx.guild)
    if vc:
        vc.stop()
        await vc.disconnect()
        for files in os.listdir(directory):
            if files not in file_names:
                filepath = os.path.join(directory, files)
                os.remove(filepath)
    else:
        await ctx.send('The bot is not playing anything at the moment.')


@bot.command(name='sqrt', pass_context=True)
async def sqrt(ctx, number: int):
    result = math.sqrt(number)
    await ctx.send(f'Square root of {number} is {result}.')


@bot.command(name='clear', pass_context=True)
@commands.has_permissions(manage_messages=True)
async def clear(ctx, number: int):
    await ctx.message.delete()
    await ctx.channel.purge(limit=number)
    await ctx.send(f'Deleted {number} messages.')


@bot.command(name='kick', pass_context=True)
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.User, reason=None):
    await ctx.guild.kick(user, reason=reason)
    await ctx.send(f'User {user} has been kicked.')


@bot.command(name='ban', pass_context=True)
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.User, reason=None):
    await ctx.guild.ban(user, reason=reason)
    await ctx.send(f'User {user} has been banned.')


@bot.command(name='unban', pass_context=True)
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: discord.User):
    await ctx.guild.unban(user)
    await ctx.send(f'User {user} has been unbanned.')


# Error handling
@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f'Couldn\'t find.')
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}play <url or title>')


@sqrt.error
async def sqrt_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}sqrt <number>')


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You don\'t have permissions!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}clear <number>')


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You don\'t have permissions!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}kick <user> "<reason>"')


@ban.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You don\'t have permissions!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}ban <user> "<reason>"')


@unban.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You don\'t have permissions!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Usage: {prefix}unban <user>')


# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f'{prefix}help'))


@bot.event
async def on_message(message):
    bad_words = ['bad_word']
    msg = message.content.lower()

    if any(word in msg for word in bad_words):
            await message.delete()

    await bot.process_commands(message)


bot.run(TOKEN)
