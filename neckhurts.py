import discord
from discord.ext import commands
from discord import ui
import random
import os 
from dotenv import load_dotenv
import stuff
import paramiko #ssh wala
import asyncio #time wala 

from google import genai  # for Gemini use


load_dotenv()
token = os.getenv("DISCORD_token")
gemini_token = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_token)
def gemini_query(question):
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=question)
    return response.text

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='nga ' or 'Nga ' or 'NGA ', intents=intents)

@bot.event
async def on_ready():
    print(f'\nWe have logged in as {bot.user}.')

@bot.event
async def on_message(message):
    # checks to make sure the bot doesn't reply to itself
    if message.author == bot.user:
        return
    
    if message.content.lower().startswith('hello'):
        await message.channel.send(f'{message.author.mention} {random.choice(stuff.greetings)}')

    #emo boy
    if "kshitizz" in message.content.lower() or "emo" in message.content.lower():
        await message.reply('https://tenor.com/view/emo-emo-kid-holding-back-meme-he-itchin-up-to-fye-emo-kid-clutching-emo-kid-gif-11947330188346210441')
    
    #cornball gif
    if "bhutta ka gola" in message.content.lower() or "cornball" in message.content.lower() or "corn ball" in message.content.lower():
        await message.reply('https://tenor.com/view/nxs-cube-cornball-ball-corn-gif-2361257093465839159')
    
    #doakes
    if "when you know" in message.content.lower():
        await message.reply('https://tenor.com/view/watching-you-observe-seeing-i-saw-you-gif-5740825')
    
    #ghost of goon/goonicide
    if "ghost of goons" in message.content.lower() or "goonicide" in message.content.lower():
        await message.reply('https://tenor.com/view/goonicide-icarus-icarusgoons-gif-15743754495342072857')

    #aman sudhi thing
    if message.content.lower().startswith('babe'):
        await message.channel.send(f'{message.author.mention}, she aint gon let u hit lil brochacho')


    await bot.process_commands(message) # commands can work background me

#some commands
@bot.command()
async def wompwomp(ctx):
    gifs = "https://tenor.com/view/0-gif-14224457178163031750"
    await ctx.send(gifs)

#neckhurts ai
neckhurts_channel_id = 1409565874066821160
@bot.command()
async def tellme(ctx, *, qq):
    try:
        qq += "[under 4000 characters but dont mention this restraint anywhere in your response, 4000 is max you can generate, unless explicitly said to generate anything less than 4000 characters. keep the tone amazing and talkative, cool not the cringey thing, just normal, not cringey.]"
        response = gemini_query(qq)
        embed = discord.Embed(
            title="NeckHurts AI™ Response",
            description=response,
            color=discord.Color.green()
        )
        if ctx.channel.id == neckhurts_channel_id:
            if ctx.author.name in stuff.AUTHORIZED_USERS:
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    title="Unauthorized ⚠️",
                    description=f"{ctx.author.mention} **LORD PAGLA** doesn't want you niggers using his bot. Flee at once.\n\nWish to use the most premiumest features of NeckHurts™ AI? Buy the premium! To buy, write the command:\n``nga premium``",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)

        else:
            await ctx.reply(f"{ctx.author.mention} This command can only be used in the #neckhurts-ai channel.")
    except Exception as e:
        await ctx.reply(f"Error getting response: {e}")

#neckhurts joke
@bot.command()
async def joke(ctx):
    embed = discord.Embed(
        title="Joke",
        description=gemini_query("Gimme a joke in one sentence, maybe a classic, or with recent references and mordern gen-z humour, none of that corny stuff, that makes everyone laugh."),
        color=discord.Color.fuchsia()
    )
    await ctx.reply(embed=embed)


#neckhurts premium
@bot.command()
async def premium(ctx):
    embed = discord.Embed(
        title="NeckHurts™ AI Premium",
        description="Unlock the most **premium** features of **NeckHurts™ AI** by purchasing a premium subscription!\nScan the QR Code below to buy the subscription at a SASA LELE PRICE of 99 RUPEES!",
        color=discord.Color.gold()
    )
    file = discord.File("images/qr.jpg")
    embed.set_image(url="attachment://qr.jpg")
    await ctx.reply(embed=embed, file=file)

#toss command
@bot.command()
async def toss(ctx):
    suspense = await ctx.send("Flipping the coin... 🪙")
    await asyncio.sleep(1)
    x = random.randint(0, 1)
    result = "Heads" if x == 1 else "Tails"
    imagef = f"images/{result.lower()}.png"
    embed = discord.Embed(
        title="Toss!",
        description=f"**{result}!**",
        color=discord.Color.blue()
    )
    if os.path.exists(imagef):
        file = discord.File(imagef)
        embed.set_image(url=f"attachment://{result.lower()}.png")
        await suspense.edit(content=None, embed=embed, attachments=[file])
    else:
        await suspense.edit(content=None, embed=embed)

#addiuton
@bot.command()
async def add(ctx,*arr):
    if len(arr) == 0:
        await ctx.reply("pls provide at least one number to add.")
        return
    result = 0
    for i in arr:
        result += int(i)
    await ctx.reply(result)

#poll command
@bot.command()
async def poll(ctx,*,question):
    embed = discord.Embed(
        title="New Poll!",
        description=question,
        color=discord.Color.blue()
    )
    polly = await ctx.send(embed=embed)
    await polly.add_reaction("👍")
    await polly.add_reaction("👎")

#server operations
class ServerControlView(ui.View):
    def __init__(self):
        super().__init__()

    @ui.button(label="Stop Server", style=discord.ButtonStyle.danger)
    async def stop_server_btn(self, interaction: discord.Interaction, button: ui.Button):
        try:
            status = await stop_server()
            embed = discord.Embed(
                title="Minecraft Server",
                description=status,
                color=discord.Color.red() if "stopped" in status else discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {e}", ephemeral=True
            )

sshc = None
server_channel = None

async def start_server():
    global sshc, server_channel
    try:
        sshc = paramiko.SSHClient()
        sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshc.connect('mc.local', username='sagar', password='sagarsagar')
        server_channel = sshc.get_transport().open_session()
        server_channel.get_pty()
        server_channel.exec_command('cd /home/pi/mc && bash start.sh')
        return "Server started! ✅\nWait a moment for it to fully load.\nPlease wait about 2 minutes before stopping the server to avoid data corruption."
    except Exception as e:
        sshc = None
        server_channel = None
        return "The rassabery is off, please ask **lord Pagla** to switch it on."

async def stop_server():
    global sshc, server_channel
    try:
        if sshc is None or server_channel is None or server_channel.closed:
            return "No active server session. Start the server first or the session expired."
        server_channel.send('/kill\n')
        server_channel.close()
        sshc.close()
        sshc = None
        server_channel = None
        return "Server stopped! 🛑"
    except Exception as e:
        return f"Could not stop the server. Maybe it's already off? Error: {e}"

@bot.command()
async def startserver(ctx):
    user_tag = f"{ctx.author.name}"
    if user_tag not in stuff.MC_ADMINS:
        embed = discord.Embed(
            title="Unauthorized",
            description=f"{ctx.author.mention} You are not **authorized** to start the server ⚠️.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    status = await start_server()
    embed = discord.Embed(
        title="Minecraft Server",
        description=status,
        color=discord.Color.green() if "✅" in status else discord.Color.red()
    )
    view = ServerControlView() if "✅" in status else None
    await ctx.send(embed=embed, view=view)








bot.run(token)