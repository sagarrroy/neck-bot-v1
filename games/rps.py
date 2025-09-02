import discord
from discord.ext import commands
import random
import json
import os
from typing import Dict, List

# ===== Settings =====
SETTINGS = {
    "allowed_channel_id": None,          # Set to a channel ID to restrict, or None for any
    "round_options": [3, 5, 6, 7, 9],    # Voting options for total rounds (first to N points)
    "surprise_chances": {                # Weighted single-roll per round (in insertion order)
        "mirror_move": 0.05,             # Swaps choices before deciding
        "bomb": 0.03,                    # Auto-win to a random player
        "double_points": 0.07,           # Winner gets 2 points
        "reversal": 0.05,                # Flip winner after deciding
        "draw_bomb": 0.03,               # On draw: both lose 1 point (not below 0)
    },                                   # Total here: 0.23 (77% of rounds have no surprise)
    "funny_remark_chance": 0.25          # Chance to add a random funny remark when no surprise triggers
}

# ===== Persistence (leaderboard + remarks) =====
DATA_DIR = "data"
LB_PATH = os.path.join(DATA_DIR, "rps_leaderboard.json")
REMARKS_PATH = os.path.join(DATA_DIR, "rps_remarks.txt")

def _ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LB_PATH):
        with open(LB_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)
    # Remarks file is optional; only created if absent with defaults
    if not os.path.exists(REMARKS_PATH):
        with open(REMARKS_PATH, "w", encoding="utf-8") as f:
            f.write(
                "That was spicy!\n"
                "Did someone say mind games?\n"
                "Peak gaming energy right there.\n"
                "Respect the hustle.\n"
                "Plot twist of the century.\n"
            )

def _load_lb() -> Dict[str, Dict[str, int]]:
    _ensure_data_files()
    with open(LB_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {}

def _save_lb(data: Dict[str, Dict[str, int]]):
    _ensure_data_files()
    with open(LB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _load_remarks() -> List[str]:
    _ensure_data_files()
    try:
        with open(REMARKS_PATH, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]
            return [ln for ln in lines if ln]
    except Exception:
        return []

FUNNY_REMARKS: List[str] = _load_remarks()

def record_match_result(winner_id: int, loser_id: int):
    lb = _load_lb()
    w = str(winner_id)
    l = str(loser_id)
    if w not in lb:
        lb[w] = {"wins": 0, "losses": 0}
    if l not in lb:
        lb[l] = {"wins": 0, "losses": 0}
    lb[w]["wins"] += 1
    lb[l]["losses"] += 1
    _save_lb(lb)

def _safe_mention(guild: discord.Guild, user_id: int) -> str:
    member = guild.get_member(user_id)
    return member.mention if member else f"<@{user_id}>"

def build_leaderboard_embed(ctx: commands.Context) -> discord.Embed:
    lb = _load_lb()
    # Sort: wins desc, losses asc, user_id asc (stable)
    rows = [
        (int(uid), stats.get("wins", 0), stats.get("losses", 0))
        for uid, stats in lb.items()
    ]
    rows.sort(key=lambda t: (-t[1], t[2], t[0]))
    top = rows[:10]

    embed = discord.Embed(
        title="🏅 RPS Leaderboard",
        description=f"Server: {ctx.guild.name}",
        color=discord.Color.orange()
    )
    if not top:
        embed.add_field(name="No data yet", value="Play a match using the rps command to get on the board!", inline=False)
        return embed

    lines = []
    for idx, (uid, wins, losses) in enumerate(top, start=1):
        lines.append(f"**#{idx}:** {_safe_mention(ctx.guild, uid)} — {wins}W/{losses}L")
    embed.add_field(name="Top Players", value="\n".join(lines), inline=False)
    return embed

# ===== UI Components =====
class RoundVoteView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.p1 = p1
        self.p2 = p2
        self.votes: Dict[int, int] = {}  # user_id -> chosen rounds
        # Dynamically add buttons for each round option
        for opt in SETTINGS["round_options"]:
            self.add_item(self.RoundButton(opt))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message("Only the two players can vote.", ephemeral=True)
            return False
        return True

    class RoundButton(discord.ui.Button):
        def __init__(self, value: int):
            super().__init__(label=f"{value} Rounds", style=discord.ButtonStyle.primary)
            self.value = value

        async def callback(self, interaction: discord.Interaction):
            # Access the parent view via the read-only property provided by discord.py
            view: "RoundVoteView" = self.view  # type: ignore
            uid = interaction.user.id
            view.votes[uid] = self.value
            await interaction.response.send_message(f"You voted: {self.value} rounds.", ephemeral=True)
            if len(view.votes) == 2:
                view.stop()

class ChoiceView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.p1 = p1
        self.p2 = p2
        self.choices: Dict[int, str] = {}  # user_id -> "Rock"/"Paper"/"Scissors"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message("Only the two players can play this round.", ephemeral=True)
            return False
        return True

    async def _choose(self, interaction: discord.Interaction, move: str):
        uid = interaction.user.id
        if uid in self.choices:
            # Ignore repeated picks; keep first choice to prevent fishing
            await interaction.response.send_message("Choice already locked in.", ephemeral=True)
            return
        self.choices[uid] = move
        await interaction.response.send_message(f"You picked {move}.", ephemeral=True)
        if len(self.choices) == 2:
            self.stop()

    @discord.ui.button(label="Rock 🪨", style=discord.ButtonStyle.secondary)
    async def btn_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._choose(interaction, "Rock")

    @discord.ui.button(label="Paper 📄", style=discord.ButtonStyle.secondary)
    async def btn_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._choose(interaction, "Paper")

    @discord.ui.button(label="Scissors ✂️", style=discord.ButtonStyle.secondary)
    async def btn_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._choose(interaction, "Scissors")

# ===== Embeds =====
def build_match_embed(
    p1: discord.Member,
    p2: discord.Member,
    scores: Dict[int, int],
    round_num: int,
    total_rounds: int,
    title: str,
    subtitle: str | None = None,
    color: discord.Color = discord.Color.blurple()
) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    embed.description = f"{p1.mention} vs {p2.mention}"
    # Scoreboard
    p1_score = scores.get(p1.id, 0)
    p2_score = scores.get(p2.id, 0)
    embed.add_field(
        name="Scoreboard",
        value=f"{p1.display_name}: {p1_score}\n{p2.display_name}: {p2_score}",
        inline=False
    )
    # Status
    status = f"Round {round_num} / {total_rounds}"
    if subtitle:
        status += f"\n{subtitle}"
    embed.add_field(name="Status", value=status, inline=False)
    return embed

# ===== Moves and helpers (Part 2 starts here) =====
MOVES = ("Rock", "Paper", "Scissors")
MOVE_EMOJI = {"Rock": "🪨", "Paper": "📄", "Scissors": "✂️"}

def decide_winner(c1: str, c2: str, p1_id: int, p2_id: int):
    if c1 == c2:
        return None
    beats = {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}
    return p1_id if beats[c1] == c2 else p2_id

# Track in-progress users to prevent overlap
_IN_PROGRESS: set[int] = set()

# Simple yes/no view for continuing into tiebreakers
class ContinueView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=30)
        self.p1 = p1
        self.p2 = p2
        self.votes = {}  # user_id -> True/False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in (self.p1.id, self.p2.id)

    @discord.ui.button(label="Continue 🟢", style=discord.ButtonStyle.success)
    async def _yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = True
        await interaction.response.send_message("You voted to continue.", ephemeral=True)
        if len(self.votes) == 2:
            self.stop()

    @discord.ui.button(label="Stop 🔴", style=discord.ButtonStyle.danger)
    async def _no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.votes[interaction.user.id] = False
        await interaction.response.send_message("You voted to stop.", ephemeral=True)
        if len(self.votes) == 2:
            self.stop()

    def both_agreed(self) -> bool:
        return len(self.votes) == 2 and all(self.votes.values())

# ===== Game Command =====
@commands.command(name="rps")
async def rps(ctx, opponent: discord.Member):
    # Channel restriction
    if SETTINGS["allowed_channel_id"] and ctx.channel.id != SETTINGS["allowed_channel_id"]:
        return await ctx.reply("🚫 You can't start RPS in this channel.")
    # Opponent validation
    if opponent.bot or opponent.id == ctx.author.id:
        return await ctx.reply("Invalid opponent.")
    # Concurrency check
    if ctx.author.id in _IN_PROGRESS or opponent.id in _IN_PROGRESS:
        return await ctx.reply("⏳ One of you is already in a game.")

    p1, p2 = ctx.author, opponent
    _IN_PROGRESS.update({p1.id, p2.id})

    try:
        # ===== Voting for round count =====
        while True:
            vote_view = RoundVoteView(p1, p2)
            vote_embed = discord.Embed(
                title="🗳️ Round vote",
                description=f"{p1.mention} vs {p2.mention}\nPick how many rounds to play.",
                color=discord.Color.blurple()
            )
            vote_embed.add_field(
                name="Options",
                value=", ".join(str(o) for o in SETTINGS["round_options"]),
                inline=False
            )
            msg_vote = await ctx.reply(embed=vote_embed, view=vote_view)
            await vote_view.wait()
            if len(vote_view.votes) < 2:
                return await ctx.send("⏳ Match cancelled due to no votes.")
            votes = list(vote_view.votes.values())
            if votes[0] == votes[1]:
                total_rounds = votes[0]
                break
            else:
                await ctx.send("⚠️ Votes didn’t match. Re‑starting vote…")

        # ===== Initialize match state =====
        scores = {p1.id: 0, p2.id: 0}
        round_num = 1
        tiebreaker_mode = False
        streak = {p1.id: 0, p2.id: 0}

        # Create the single match message to edit each round
        match_msg = await ctx.send(
            embed=build_match_embed(p1, p2, scores, round_num, total_rounds, "Match Starting", color=discord.Color.gold())
        )

        # ===== Main game loop =====
        while True:
            # Ask for choices via buttons
            choice_view = ChoiceView(p1, p2)
            await match_msg.edit(
                embed=build_match_embed(
                    p1, p2, scores, round_num, total_rounds, f"Round {round_num} — Make your choice"
                ),
                view=choice_view
            )
            await choice_view.wait()
            if len(choice_view.choices) < 2:
                return await ctx.send("⏳ Match cancelled due to no choices.")

            c1 = choice_view.choices[p1.id]
            c2 = choice_view.choices[p2.id]

            # Roll a single surprise per round (weighted by chances)
            surprise = None
            r = random.random()
            for name, chance in SETTINGS["surprise_chances"].items():
                if r < chance:
                    surprise = name
                    break
                r -= chance

            # Pre-result surprise: mirror_move swaps choices before deciding
            pre_remark = None
            if surprise == "mirror_move":
                c1, c2 = c2, c1
                pre_remark = "🪞 Mirror Move! Choices were swapped before deciding."

            # Decide base winner
            winner = decide_winner(c1, c2, p1.id, p2.id)

            # Post-result surprises
            post_remark = None
            point_value = 1

            if surprise == "bomb":
                # Bomb: auto-winner randomly, overrides outcome
                target = random.choice([p1.id, p2.id])
                winner = target
                post_remark = f"💣 Bomb! {_safe_mention(ctx.guild, target)} detonated an auto‑win."
            elif surprise == "double_points" and winner is not None:
                point_value = 2
                post_remark = "✨ Double Points! Round winner gets 2 points."
            elif surprise == "reversal" and winner is not None:
                # Flip winner
                winner = p1.id if winner == p2.id else p2.id
                post_remark = "🔄 Reversal! The round winner has been flipped."
            elif surprise == "draw_bomb" and winner is None:
                # Both lose a point (not below 0), still a draw
                scores[p1.id] = max(0, scores[p1.id] - 1)
                scores[p2.id] = max(0, scores[p2.id] - 1)
                post_remark = "💥 Draw Bomb! Both players lose a point."

            # Apply points for the round
            if winner is not None and not (surprise == "draw_bomb"):
                scores[winner] += point_value

            # Build round result text
            p1_choice_txt = f"{MOVE_EMOJI[c1]} {c1}"
            p2_choice_txt = f"{MOVE_EMOJI[c2]} {c2}"
            if winner is None:
                last_result = (
                    f"🤝 Draw\n"
                    f"{p1.display_name}: {p1_choice_txt} | {p2.display_name}: {p2_choice_txt}"
                )
            else:
                last_result = (
                    f"🏆 {_safe_mention(ctx.guild, winner)} won the round\n"
                    f"{p1.display_name}: {p1_choice_txt} | {p2.display_name}: {p2_choice_txt}"
                )

            # Add surprise remark or random funny remark
            remark = pre_remark or post_remark
            if remark is None and FUNNY_REMARKS and random.random() < SETTINGS["funny_remark_chance"]:
                remark = random.choice(FUNNY_REMARKS)
            if remark:
                last_result += f"\n_{remark}_"

            # Update the single match embed
            await match_msg.edit(
                embed=build_match_embed(
                    p1, p2, scores, round_num, total_rounds, "Round Result", last_result, color=discord.Color.green()
                ),
                view=None
            )

            # ===== Win / Tiebreaker logic =====
            if not tiebreaker_mode:
                # Normal win condition: first to total_rounds (points)
                if scores[p1.id] == total_rounds or scores[p2.id] == total_rounds:
                    if scores[p1.id] == scores[p2.id]:
                        # Ask to continue with tiebreakers (both must agree)
                        cont_view = ContinueView(p1, p2)
                        cont_embed = discord.Embed(
                            title="⚖️ Match tied",
                            description="Do you want to continue with tiebreakers?\nWin 2 rounds in a row to take the match.",
                            color=discord.Color.purple()
                        )
                        msg_cont = await ctx.send(embed=cont_embed, view=cont_view)
                        await cont_view.wait()
                        if not cont_view.both_agreed():
                            return await ctx.send("🏁 Match ended in a draw.")
                        # Enter tiebreaker mode
                        tiebreaker_mode = True
                        scores = {p1.id: 0, p2.id: 0}
                        streak = {p1.id: 0, p2.id: 0}
                        await match_msg.edit(
                            embed=build_match_embed(
                                p1, p2, scores, 1, 2, "Tiebreakers starting", "Win 2 in a row to win 🏆", color=discord.Color.purple()
                            )
                        )
                        round_num = 1
                    else:
                        win_id = p1.id if scores[p1.id] > scores[p2.id] else p2.id
                        lose_id = p2.id if win_id == p1.id else p1.id
                        record_match_result(win_id, lose_id)
                        win_embed = discord.Embed(
                            title="🏆 Match Over",
                            description=f"Winner: {_safe_mention(ctx.guild, win_id)}\nFinal Score: {scores[p1.id]} - {scores[p2.id]}",
                            color=discord.Color.red()
                        )
                        return await ctx.send(embed=win_embed)
            else:
                # Tiebreaker mode: win 2 in a row
                if winner is None:
                    # Draw resets both streaks
                    streak[p1.id] = 0
                    streak[p2.id] = 0
                else:
                    loser = p1.id if winner == p2.id else p2.id
                    streak[winner] += 1
                    streak[loser] = 0
                    if streak[winner] >= 2:
                        record_match_result(winner, loser)
                        win_embed = discord.Embed(
                            title="🏆 Match Over (Tiebreakers)",
                            description=f"Winner: {_safe_mention(ctx.guild, winner)}\nStreak: 2 in a row",
                            color=discord.Color.red()
                        )
                        return await ctx.send(embed=win_embed)

            # Next round
            round_num += 1

    finally:
        _IN_PROGRESS.discard(p1.id)
        _IN_PROGRESS.discard(p2.id)

# ===== Leaderboard Command =====
@commands.command(name="rpsboard")
async def rpsboard(ctx):
    await ctx.send(embed=build_leaderboard_embed(ctx))

# ===== Rules Command =====
@commands.command(name="rpsrules")
async def rpsrules(ctx):
    embed = discord.Embed(title="📜 Rock Paper Scissors Rules", color=discord.Color.blue())
    embed.add_field(
        name="How to Play",
        value=f"Challenge someone with `{ctx.prefix}rps @user`. Vote on rounds, then pick Rock, Paper, or Scissors each round.",
        inline=False
    )
    embed.add_field(
        name="Surprise Mechanics",
        value="\n".join(
            f"**{name.replace('_', ' ').title()}** — {int(chance * 100)}% chance per round"
            for name, chance in SETTINGS["surprise_chances"].items()
        ),
        inline=False
    )
    await ctx.send(embed=embed)

# ===== Setup =====
def setup_rps(bot):
    bot.add_command(rps)
    bot.add_command(rpsboard)
    bot.add_command(rpsrules)
