import discord, os, json
from discord.ext import commands


# ------------------------
# FILE PATHS

LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "game_data", "tictacboard.json")


if not os.path.exists(LEADERBOARD_FILE):
    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

# ------------------------
# LEADERBOARD HELPERS READ/WRITE
def load_leaderboard():
    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def update_stats(player_name: str, won: bool):
    data = load_leaderboard()
    if player_name not in data:
        data[player_name] = {"wins": 0, "losses": 0}

    if won:
        data[player_name]["wins"] += 1
    else:
        data[player_name]["losses"] += 1

    save_leaderboard(data)

# ------------------------
# CHALLENGE VIEW

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

# ------------------------
# GAME BUTTON

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

# ------------------------
# GAME VIEW

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

# ------------------------
# COMMANDS

@commands.command(name="tictactoe", help="Challenge someone to TicTacToe")
async def tictactoe_cmd(ctx, member: discord.Member):
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

@commands.command(name="tictacboard", help="Show the TicTacToe leaderboard")
async def tictacboard_cmd(ctx):
    data = load_leaderboard()
    if not data:
        await ctx.send("📉 Leaderboard is empty. Play some games first!")
        return

    sorted_data = sorted(data.items(), key=lambda x: x[1]["wins"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    embed = discord.Embed(title="🏆 TicTacToe Leaderboard", color=discord.Color.gold())

    for i, (name, stats) in enumerate(sorted_data[:5], start=1):
        medal = medals[i-1] if i <= 3 else ""
        embed.add_field(
            name=f"{i}. {medal} {name}",
            value=f"Wins: {stats['wins']} | Losses: {stats['losses']}",
            inline=False
        )

    await ctx.send(embed=embed)

# ------------------------
# SETUP FUNCTION

def setup_tictactoe(bot: commands.Bot):
    bot.add_command(tictactoe_cmd)
    bot.add_command(tictacboard_cmd)