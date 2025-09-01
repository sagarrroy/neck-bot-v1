import discord, asyncio, json, os, random
from discord.ext import commands
from typing import List, Set

# -------------------
# CONFIG
# -------------------
ALLOWED_CHANNEL_ID = 1409565874066821160  # neckhurts-ai channel id
# track active game
active_sessions: Set[int] = set()

# -------------------
# FILE PATHS
# -------------------
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "game_data", "questions.json")
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "game_data", "triviaboard.json")

# -------------------
# LOAD QUESTIONS
# -------------------
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    trivia_questions = json.load(f)

# FOR RANDOM QUESTIONS
question_pool = trivia_questions.copy()
random.shuffle(question_pool)

# -------------------
# LEADERBOARD
# -------------------
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_leaderboard():
    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# -------------------
# VIEWS
# -------------------
class JoinView(discord.ui.View):
    def __init__(self, ctx: commands.Context, release_channel_cb):
        super().__init__(timeout=120)  # TIME TO FILL LOBBY (2 MINS)
        self.ctx = ctx
        self.players: List[discord.User] = []
        self.release_channel_cb = release_channel_cb
        self.message: discord.Message | None = None

    async def on_timeout(self):
        # disable join if lobby times out and release the channel lock
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
        await self.ctx.send("⏳ Lobby timed out. Start again you nigah")
        self.release_channel_cb()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel_id != ALLOWED_CHANNEL_ID:  # NECKHURTS AI CHANNEL CONSTRAINT
            await interaction.response.send_message(
                f"This game can only be played in <#{ALLOWED_CHANNEL_ID}>.", ephemeral=True
            )
            return

        if interaction.user.bot:
            await interaction.response.send_message(
                "Bots can’t play.", ephemeral=True
            )  # PREVENTING BOTS FROM ACCIDENTALLY INTERACTING
            return

        if interaction.user in self.players:
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return

        if len(self.players) >= 5:
            await interaction.response.send_message("Lobby is already full!", ephemeral=True)
            return

        self.players.append(interaction.user)

        # UPDATE LOBBY EMBED
        names = ", ".join(p.display_name for p in self.players) if self.players else "None"
        embed = discord.Embed(
            title="🎯 Battle Royale Trivia",
            description=f"Players Joined: {len(self.players)}/5\n\nCurrent: {names}",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

        # AUTOSTART
        if len(self.players) == 5:
            for child in self.children:
                child.disabled = True
            try:
                await interaction.followup.send("Lobby full! Game starting in 3 seconds...")
                await asyncio.sleep(3)
                try:
                    await start_trivia(self.ctx, self.players)
                finally:
                    # ensure channel lock is released when game ends/crashes
                    self.release_channel_cb()
            except Exception:
                # error report
                await self.ctx.send("Something went wrong starting the game.")
                self.release_channel_cb()

class AnswerView(discord.ui.View):
    def __init__(self, players: List[discord.User], spectators_ids: Set[int]):
        super().__init__(timeout=None)
        self.players = players
        self.player_ids = {p.id for p in players}
        self.spectators_ids = spectators_ids
        self.answers: dict[int, str] = {}

    async def record_answer(self, interaction: discord.Interaction, choice: str):
        uid = interaction.user.id

        if uid in self.spectators_ids:
            await interaction.response.send_message("You're out! YOu can spectate! 👀", ephemeral=True)
            return

        if uid not in self.player_ids:
            await interaction.response.send_message("You're not in this game.", ephemeral=True)
            return

        # RECORD/overwrite the player’s choice (latest click counts until timer ends)
        self.answers[uid] = choice
        await interaction.response.send_message(f"You picked {choice}", ephemeral=True)

    @discord.ui.button(label="A", style=discord.ButtonStyle.blurple)
    async def a_button(self, i, b): await self.record_answer(i, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.blurple)
    async def b_button(self, i, b): await self.record_answer(i, "B")

    @discord.ui.button(label="C", style=discord.ButtonStyle.blurple)
    async def c_button(self, i, b): await self.record_answer(i, "C")

    @discord.ui.button(label="D", style=discord.ButtonStyle.blurple)
    async def d_button(self, i, b): await self.record_answer(i, "D")

# -------------------
# GAME LOGIC
# -------------------
async def start_trivia(ctx: commands.Context, players: List[discord.User]):
    global question_pool

    # TIME LIMITS PER PLAYERS REMAINING
    timer_map = {5: 12, 4: 10, 3: 9, 2: 8}
    default_time_limit = 6  # FINAL LIGHTNING ROUNDS

    round_number = 1
    spectators_ids: Set[int] = set()

    while len(players) > 1:
        # refill and reshuffle the pool if exhausted
        if not question_pool:
            question_pool = trivia_questions.copy()
            random.shuffle(question_pool)

        q = question_pool.pop(0)
        options_str = "\n".join(q["options"])
        time_limit = timer_map.get(len(players), default_time_limit)
        view = AnswerView(players, spectators_ids)

        # OG embed
        bar_length = 10
        embed = discord.Embed(
            title=f"⚔️ Round {round_number}",
            description=f"**{q['question']}**\n\n{options_str}\n\n⏳ Time Left: [{'█'*bar_length}] {time_limit}s",
            color=discord.Color.gold()
        )
        message = await ctx.send(embed=embed, view=view)

        # Visual countdown bar (updates once per second)
        for t in range(time_limit, 0, -1):
            filled = int((t / time_limit) * bar_length)
            bar = "█" * filled + "—" * (bar_length - filled)
            embed.description = f"**{q['question']}**\n\n{options_str}\n\n⏳ Time Left: [{bar}] {t}s"
            try:
                await message.edit(embed=embed, view=view)
            except Exception:
                pass
            await asyncio.sleep(1)

        # Disable buttons
        for child in view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await message.edit(view=view)
        except Exception:
            pass

        # ELIMINATE
        eliminated_names = []
        surviving: List[discord.User] = []
        for p in players:
            ans = view.answers.get(p.id)
            if ans == q["answer"]:
                surviving.append(p)
            else:
                spectators_ids.add(p.id)
                eliminated_names.append(p.display_name)
        players = surviving

        if eliminated_names:
            await ctx.send(f"❌ Eliminated: {', '.join(eliminated_names)}")
        else:
            await ctx.send("No eliminations this round!")

        round_number += 1

    # WINNER
    winner = players[0]
    await ctx.send(f"🏆 **Winner:** {winner.mention} — nigger you made it *sob sob*")
    leaderboard = load_leaderboard()
    leaderboard[str(winner.id)] = leaderboard.get(str(winner.id), 0) + 1
    save_leaderboard(leaderboard)

# -------------------
# LEADERBOARD COMMAND
# -------------------
@commands.command(name="trivialeader", help="Show the trivia leaderboard")
async def show_leaderboard(ctx: commands.Context):
    leaderboard = load_leaderboard()

    if not leaderboard:
        await ctx.send("📉 Leaderboard is empty. Play some games first!")
        return

    # sort by wins
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 Trivia Leaderboard",
        color=discord.Color.green()
    )

    for idx, (user_id, wins) in enumerate(sorted_lb, start=1):
        user = ctx.guild.get_member(int(user_id))
        name = user.display_name if user else f"User {user_id}"
        embed.add_field(
            name=f"{idx}. {name}",
            value=f"Wins: {wins}",
            inline=False
        )

    await ctx.send(embed=embed)

# -------------------
# LOBBY STARTER
# -------------------
@commands.command(name="trivia", help="Start a trivia game lobby")
async def start_lobby(ctx: commands.Context):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send(f"This game can only be played in <#{ALLOWED_CHANNEL_ID}>.")
        return

    if ctx.channel.id in active_sessions:
        await ctx.send("⚠️ A game is already active in this channel.")
        return

    active_sessions.add(ctx.channel.id)

    def release_channel():
        try:
            active_sessions.remove(ctx.channel.id)
        except KeyError:
            pass

    view = JoinView(ctx, release_channel)
    embed = discord.Embed(
        title="🎯 Trivia Royale — Join Now!",
        description="Click the button below to join.\nLobby closes in 2 minutes or when 5 players join.",
        color=discord.Color.blurple()
    )
    view.message = await ctx.send(embed=embed, view=view)

# ----------------
# SETUP
# -------------------
def setup_trivia(bot: commands.Bot):
    bot.add_command(start_lobby)
    bot.add_command(show_leaderboard)