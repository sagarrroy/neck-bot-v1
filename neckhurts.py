from asyncio import timeout
import discord
from discord.ext import commands
from discord import ui
import random
import os 
from dotenv import load_dotenv
import stuff
import paramiko #ssh wala
import asyncio #time wala 
import csv

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



LEADERBOARD_FILE = "leaderboard.csv"

if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "wins", "losses"])


def update_stats(player_name: str, won: bool):
    rows = []
    found = False

    with open(LEADERBOARD_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["name"] == player_name:
                found = True
                row["wins"] = str(int(row["wins"]) + (1 if won else 0))
                row["losses"] = str(int(row["losses"]) + (0 if won else 1))
            rows.append(row)

    if not found:
        rows.append({"name": player_name, "wins": "1" if won else "0", "losses": "0" if won else "1"})

    with open(LEADERBOARD_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "wins", "losses"])
        writer.writeheader()
        writer.writerows(rows)


#------------------------ buttons n shit
class ChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.Member, challenged: discord.Member, message: discord.Message):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.challenged = challenged
        self.message = message
        self.finished = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.challenged:
            await interaction.response.send_message("You're not the one being challenged!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.finished = True
        embed = self.message.embeds[0].copy()
        embed.description = f"🎯 {self.challenged.mention} **accepted** the challenge from {self.challenger.mention}!"
        await interaction.response.edit_message(embed=embed, view=None)

        # Start TicTacToe
        game = TicTacToe(self.challenger, self.challenged)
        await interaction.followup.send(f"{self.challenger.mention} (X) vs {self.challenged.mention} (O)", view=game)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.finished = True
        embed = self.message.embeds[0].copy()
        embed.description = f"🚫 {self.challenged.mention} **rejected** the challenge from {self.challenger.mention}."
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        if self.finished:
            return
        embed = self.message.embeds[0].copy()
        embed.description = f"⌛ Challenge expired! {self.challenged.mention} didn’t respond in time."
        await self.message.edit(embed=embed, view=None)


#------------------------ GAME
class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(label="\u200b", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        if interaction.user != view.current_player:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return
        if self.label != "\u200b":
            await interaction.response.send_message("That spot is taken!", ephemeral=True)
            return

        self.label = "X" if view.current_player == view.player_x else "O"
        self.style = discord.ButtonStyle.danger if self.label == "X" else discord.ButtonStyle.primary
        view.board[self.y][self.x] = self.label
        view.moves += 1

        winner = view.check_winner()
        if winner or view.moves >= 9:
            for child in view.children:
                child.disabled = True
            if winner:
                content = f"🎉 {view.current_player.mention} ({self.label}) wins!"
                update_stats(view.current_player.name, True)
                loser = view.player_o if view.current_player == view.player_x else view.player_x
                update_stats(loser.name, False)
            else:
                content = "🤝 It's a draw!"

            await interaction.response.edit_message(content=content, view=view)
            view.stop()
        else:
            view.current_player = view.player_o if view.current_player == view.player_x else view.player_x
            await interaction.response.edit_message(content=f"{view.current_player.mention}'s turn", view=view)


class TicTacToe(discord.ui.View):
    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=None)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.board = [[" "]*3 for _ in range(3)]
        self.moves = 0

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        b = self.board
        lines = (
            b[0], b[1], b[2],
            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]]
        )
        for line in lines:
            if line[0] != " " and line.count(line[0]) == 3:
                return line[0]
        return None


# ------------------- command for GAME
@bot.command()
async def tictactoe(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("You can't challenge yourself!")
        return

    embed = discord.Embed(
        title="🎮 TicTacToe Challenge",
        description=f"{ctx.author.mention} challenged {member.mention} to a showdown!",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="You have 30 seconds to respond.")

    msg = await ctx.send(embed=embed)
    await msg.edit(view=ChallengeView(ctx.author, member, msg))

# tictactoe leaderboard
@bot.command()
async def leaderboard(ctx):
    with open(LEADERBOARD_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = sorted(reader, key=lambda x: int(x["wins"]), reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    embed = discord.Embed(title="🏆 TicTacToe Leaderboard", color=discord.Color.gold())

    for i, row in enumerate(data[:5], start=1):
        name = row["name"]
        wins = row["wins"]
        medal = medals[i-1] if i <= 3 else ""
        embed.add_field(name=f"{i}. {medal} {name}", value=f"Wins: {wins}", inline=False)

    await ctx.send(embed=embed)

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
    async def _help(ctx):
        await help_command(ctx)




bot.run(token)