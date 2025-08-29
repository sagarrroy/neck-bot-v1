import discord, random, os, asyncio , paramiko #timing,ssh
from modules import stuff
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv


#game imports
from games.trivia_game import setup_trivia
from games.tictactoe import setup_tictactoe


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
        await message.reply(f'{random.choice(stuff.greetings)}')

    #emo boy

    if message.author.id == 'kshitiz ka user id':
        await message.reply("move on krle bsdk\n\n - *kritanshi*")

    if "kshitizz" in message.content.lower() or "emo" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply('https://tenor.com/view/emo-emo-kid-holding-back-meme-he-itchin-up-to-fye-emo-kid-clutching-emo-kid-gif-11947330188346210441')

    #burger king
    if "nigger" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply("https://tenor.com/view/billybobbu-moment-gif-6181302910520403962")
    if ":)" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply("https://tenor.com/view/smiley-face-burger-king-burger-king-happy-burger-king-whopper-burger-king-racism-gif-935276361237906854")

    #cornball gif
    if "bhutta ka gola" in message.content.lower() or "cornball" in message.content.lower() or "corn ball" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply('https://tenor.com/view/nxs-cube-cornball-ball-corn-gif-2361257093465839159')
    
    #doakes
    if "when you know" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply('https://tenor.com/view/watching-you-observe-seeing-i-saw-you-gif-5740825')
    
    #ghost of goon/goonicide
    if "ghost of goon" in message.content.lower() or "goonicide" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply('https://tenor.com/view/goonicide-icarus-icarusgoons-gif-15743754495342072857')

    #aman sudhi thing
    if "babe" in message.content.lower():
        await asyncio.sleep(1)
        await message.reply(f'{message.author.mention}, she aint gon let u hit lil brochacho')


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
    embed.set_footer(text="Note: This is a ONE TIME subscription.")
    file = discord.File("images/qr.jpg")
    embed.set_image(url="attachment://qr.jpg")
    await ctx.reply(embed=embed, file=file)

#toss command
@bot.command()
async def toss(ctx):
    toss_image = discord.File("images/toss.png")
    suspense = await ctx.send("Flipping the coin... 🪙\n",file=toss_image)
    await asyncio.sleep(2)
    result = random.choice(["Heads", "Tails"])
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

# ------------------------ TICTACTOE GAME IMPORT
setup_tictactoe(bot)

#-------------------chelp command
@bot.command()
async def commands(ctx):
    embed = discord.Embed(
        title="📜 NGA Bot Commands & Interactions",
        description="Here’s everything you can do with this bot:",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="✨ Trigger Words",
        value="Saying any of these will trigger special replies & GIFs:\n`kshitizz, :), bhutta ka gola, cornball, when you know, ghost of goon`",
        inline=False
    )

    embed.add_field(
        name="📢 `nga tellme`",
        value="Sends a random fact, quote, or insight. Great for casual engagement.",
        inline=False
    )

    embed.add_field(
        name="😂 `nga joke`",
        value="Delivers a short, witty joke. Perfect for lightening the mood.",
        inline=False
    )

    embed.add_field(
        name="🪙 `nga toss`",
        value="Simulates a coin toss. Returns Heads or Tails with optional embed.",
        inline=False
    )

    embed.add_field(
        name="➕ `nga add <user> <score>`",
        value="Adds a score to a user. Useful for tracking points or leaderboard logic.",
        inline=False
    )

    embed.add_field(
        name="📊 `nga poll <question> | <option1> | <option2> | ...`",
        value="Creates a reaction-based poll. Users vote via emoji reactions.",
        inline=False
    )

    embed.add_field(
        name="🚀 `nga startserver`",
        value="Initializes server-specific settings or starts a session. Can be expanded to load configs, roles, or events.",
        inline=False
    )

    embed.add_field(
        name="ℹ️ `nga help`",
        value="Shows this help menu.",
        inline=False
    )
    embed.add_field(
        name="⭕ `nga challenge @user`",
        value="Challenge someone to a TicTacToe match with Accept/Reject buttons. Game plays on a 3×3 button grid with auto win/draw detection.",
        inline=False
    )

    embed.add_field(
        name="🏆 `nga leaderboard`",
        value="Shows the top 5 TicTacToe players ranked by wins. Includes 🥇🥈🥉 medals for top spots.",
        inline=False
    )

    embed.set_footer(text="Tip: Commands start with `nga `. Use them exactly as shown.")

    await ctx.send(embed=embed)


def setup(bot):
    @bot.command(name="help")
    async def help(ctx):
        await help_command(ctx)

#----------------------
# --------------------- trivia battleroyale game call
setup_trivia(bot)


bot.run(token)