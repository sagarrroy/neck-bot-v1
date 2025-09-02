import asyncio, os, random, json, discord
from typing import Optional, Dict, Tuple
from discord.ext import commands

SETTINGS = {
    "round_options": [3, 5, 9],  # what players can vote on
    "funny_remark_chance": 0.30,  # 30% chance per round
    "surprise_chances": {
        "bomb": 0.05,          # one player gets an auto-win effect unless both somehow get it (handled as draw)
        "double_points": 0.05, # round winner earns 2 points instead of 1
        "reversal": 0.03,      # loser gets the win (after normal calc)
        "draw_bomb": 0.03,     # both lose 1 round point (floored at 0), round gives no winner
        "mirror_move": 0.04    # both choices are swapped before deciding winner
    },
    "leaderboard_file": "game_data/rpsboard.json",
    "allowed_channel_id": None,   # channel restriction (none -> no restrictuon)
    "challenge_timeout": 60,      # time in sec to accept/decline
    "vote_timeout": 60,           # time in sec for round count voting
    "choice_timeout": 60          # time in sec to pick R/P/S
}

FUNNY_REMARKS = [
    "Scissors turned {loser}’s confidence into confetti."
]


#keep track of who’s busy, so people can’t start overlapping matches
_IN_PROGRESS: set[int] = set()


# ----------------------------
# Files — tiny helpers

def _ensure_leaderboard_file() -> None:
    path = SETTINGS["leaderboard_file"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_leaderboard() -> Dict[str, Dict[str, int]]:
    _ensure_leaderboard_file()
    with open(SETTINGS["leaderboard_file"], "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
        except json.JSONDecodeError:
            return {}


def save_leaderboard(data: Dict[str, Dict[str, int]]) -> None:
    _ensure_leaderboard_file()
    with open(SETTINGS["leaderboard_file"], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_match_result(winner_id: int, loser_id: int) -> None:
    board = load_leaderboard()
    for uid in (winner_id, loser_id):
        s = str(uid)
        if s not in board:
            board[s] = {"wins": 0, "losses": 0}
    board[str(winner_id)]["wins"] += 1
    board[str(loser_id)]["losses"] += 1
    save_leaderboard(board)


# ----------------------------
# Game logic utilities
# ----------------------------
MOVES = ("rock", "paper", "scissors")
MOVE_EMOJI = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️"
}

def decide_winner(a: str, b: str) -> int:
    """
    Returns:
      1  if a beats b
      -1 if b beats a
      0  if draw
    """
    if a == b:
        return 0
    wins_against = {
        "rock": "scissors",
        "scissors": "paper",
        "paper": "rock"
    }
    return 1 if wins_against[a] == b else -1


def roll_surprise() -> Optional[str]:
    """
    Roll once per round; at most one surprise comes out.
    If multiple pass (rare), we randomly pick one among them.
    """
    chances = SETTINGS["surprise_chances"]
    triggered = [name for name, p in chances.items() if random.random() < p]
    if not triggered:
        return None
    return random.choice(triggered)


def maybe_remark(winner_name: str, loser_name: str) -> Optional[str]:
    if random.random() < SETTINGS["funny_remark_chance"]:
        template = random.choice(FUNNY_REMARKS)
        return template.format(winner=winner_name, loser=loser_name)
    return None


# ----------------------------
# Views — small, focused UI blocks
# ----------------------------
class ChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.Member, opponent: discord.Member):
        super().__init__(timeout=SETTINGS["challenge_timeout"])
        self.challenger = challenger
        self.opponent = opponent
        self.accepted: Optional[bool] = None

    async def on_timeout(self):
        # We just let the command handler detect None and handle messaging.
        pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("Not your challenge.", ephemeral=True)
        self.accepted = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("Not your challenge.", ephemeral=True)
        self.accepted = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()


class RoundVoteView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member, options: list[int]):
        super().__init__(timeout=SETTINGS["vote_timeout"])
        self.p1 = p1
        self.p2 = p2
        self.options = options
        self.votes: Dict[int, Optional[int]] = {p1.id: None, p2.id: None}
        self.tie: bool = False
        # we create buttons dynamically to match SETTINGS["round_options"]
        for opt in options:
            self.add_item(RoundVoteButton(opt, self))

    def voted_both(self) -> bool:
        return all(v is not None for v in self.votes.values())

    def result(self) -> Optional[int]:
        vals = list(self.votes.values())
        if None in vals:
            return None
        if vals[0] == vals[1]:
            return vals[0]
        return None

    async def on_timeout(self):
        # stop so the caller can handle timeout
        self.stop()


class RoundVoteButton(discord.ui.Button):
    def __init__(self, value: int, parent: RoundVoteView):
        super().__init__(label=f"{value} Rounds", style=discord.ButtonStyle.primary)
        self.value = value
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.parent_view.votes:
            return await interaction.response.send_message("You’re not part of this vote.", ephemeral=True)
        self.parent_view.votes[interaction.user.id] = self.value

        # Build a little status line that shows who picked what so far
        p1_choice = self.parent_view.votes[self.parent_view.p1.id]
        p2_choice = self.parent_view.votes[self.parent_view.p2.id]
        status = (
            f"{self.parent_view.p1.display_name}: {p1_choice if p1_choice else '—'}\n"
            f"{self.parent_view.p2.display_name}: {p2_choice if p2_choice else '—'}"
        )

        if self.parent_view.voted_both():
            if self.parent_view.result() is not None:
                # lock buttons and move on
                for child in self.parent_view.children:
                    child.disabled = True
                await interaction.response.edit_message(content=f"Round count locked in.\n{status}", view=self.parent_view)
                self.parent_view.stop()
            else:
                # tie -> prompt retry; we keep this view but mark tie for the caller to reset
                self.parent_view.tie = True
                for child in self.parent_view.children:
                    child.disabled = True
                await interaction.response.edit_message(content=f"Tie in votes. You need to match.\n{status}", view=self.parent_view)
                self.parent_view.stop()
        else:
            await interaction.response.edit_message(content=f"Waiting for both votes…\n{status}", view=self.parent_view)


class ChoiceView(discord.ui.View):
    def __init__(self, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=SETTINGS["choice_timeout"])
        self.p1 = p1
        self.p2 = p2
        self.choices: Dict[int, Optional[str]] = {p1.id: None, p2.id: None}

        # Add the standard moves as buttons
        for move in MOVES:
            self.add_item(ChoiceButton(move, self))

    def both_chosen(self) -> bool:
        return all(c is not None for c in self.choices.values())

    async def on_timeout(self):
        self.stop()


class ChoiceButton(discord.ui.Button):
    def __init__(self, move: str, parent: ChoiceView):
        super().__init__(label=move.capitalize(), emoji=MOVE_EMOJI[move], style=discord.ButtonStyle.secondary)
        self.move = move
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.parent_view.choices:
            return await interaction.response.send_message("Not your game.", ephemeral=True)
        self.parent_view.choices[interaction.user.id] = self.move

        if self.parent_view.both_chosen():
            for child in self.parent_view.children:
                child.disabled = True
            await interaction.response.edit_message(content="Both players have chosen!", view=self.parent_view)
            self.parent_view.stop()
        else:
            await interaction.response.send_message("Choice locked. Waiting for opponent...", ephemeral=True)


# --------------------------
# Main game command
# ----------------------------
async def play_rps(ctx: commands.Context, opponent: discord.Member):
    # Channel restriction check
    if SETTINGS["allowed_channel_id"] and ctx.channel.id != SETTINGS["allowed_channel_id"]:
        return await ctx.send("This game can only be played in the designated channel.")

    if opponent.bot or opponent.id == ctx.author.id:
        return await ctx.send("Invalid opponent.")

    if ctx.author.id in _IN_PROGRESS or opponent.id in _IN_PROGRESS:
        return await ctx.send("One of you is already in a game.")

    _IN_PROGRESS.update({ctx.author.id, opponent.id})

    try:
        # Challenge phase
        view = ChallengeView(ctx.author, opponent)
        msg = await ctx.send(f"{opponent.mention}, you have been challenged by {ctx.author.mention}!", view=view)
        await view.wait()
        if view.accepted is None:
            return await ctx.send("Challenge timed out.")
        if not view.accepted:
            return await ctx.send(f"{opponent.display_name} declined the challenge. nga wompwomp")

        # Round voting loop until agreement
        rounds = None
        while rounds is None:
            vote_view = RoundVoteView(ctx.author, opponent, SETTINGS["round_options"])
            vote_msg = await ctx.send("Vote for the number of rounds:", view=vote_view)
            await vote_view.wait()
            if vote_view.tie:
                await ctx.send("Votes tied. Remaking Votes..")
                continue
            rounds = vote_view.result()
            if rounds is None:
                return await ctx.send("Voting timed out.")

        # Match loop
        scores = {ctx.author.id: 0, opponent.id: 0}
        for current_round in range(1, rounds + 1):
            # Surprise roll
            surprise = roll_surprise()
            surprise_notice = None
            if surprise:
                # Randomly pick who gets it
                target = random.choice([ctx.author, opponent])
                surprise_notice = f"💥 Looks like **{target.display_name}** got a surprise thing!"
                await ctx.send(surprise_notice)

            # Choice phase
            choice_view = ChoiceView(ctx.author, opponent)
            choice_msg = await ctx.send(
                embed=discord.Embed(
                    title=f"Round {current_round} of {rounds}",
                    description=f"{ctx.author.display_name}: {scores[ctx.author.id]} | "
                                f"{opponent.display_name}: {scores[opponent.id]}"
                ),
                view=choice_view
            )
            await choice_view.wait()
            if not choice_view.both_chosen():
                return await ctx.send("Round cancelled due to timeout.")

            p1_choice = choice_view.choices[ctx.author.id]
            p2_choice = choice_view.choices[opponent.id]

            #-------------------------------------------------------------------------------------------surprise effects
            if surprise == "mirror_move":
                p1_choice, p2_choice = p2_choice, p1_choice
            result = decide_winner(p1_choice, p2_choice)
            if surprise == "bomb":
                # Bomb beats all unless both have it
                if p1_choice != p2_choice:
                    result = 1 if p1_choice == "bomb" else -1
                else:
                    result = 0
            elif surprise == "reversal":
                result = -result
            elif surprise == "draw_bomb":
                scores[ctx.author.id] = max(0, scores[ctx.author.id] - 1)
                scores[opponent.id] = max(0, scores[opponent.id] - 1)
                result = 0

            # Update scores
            if result == 1:
                scores[ctx.author.id] += 2 if surprise == "double_points" else 1
            elif result == -1:
                scores[opponent.id] += 2 if surprise == "double_points" else 1

            # Round result embed
            desc = f"{ctx.author.display_name} chose {MOVE_EMOJI[p1_choice]} | {opponent.display_name} chose {MOVE_EMOJI[p2_choice]}"
            if result == 1:
                desc += f"\n**{ctx.author.display_name} wins the round!**"
                remark = maybe_remark(ctx.author.display_name, opponent.display_name)
                if remark:
                    desc += f"\n_{remark}_"
            elif result == -1:
                desc += f"\n**{opponent.display_name} wins the round!**"
                remark = maybe_remark(opponent.display_name, ctx.author.display_name)
                if remark:
                    desc += f"\n_{remark}_"
            else:
                desc += "\n**It's a draw!**"

            await ctx.send(embed=discord.Embed(
                title=f"Round {current_round} of {rounds}",
                description=desc
            ))

        # Match end
        if scores[ctx.author.id] > scores[opponent.id]:
            winner, loser = ctx.author, opponent
        elif scores[ctx.author.id] < scores[opponent.id]:
            winner, loser = opponent, ctx.author
        else:
            return await ctx.send("Match ended in a draw!")

        record_match_result(winner.id, loser.id)
        await ctx.send(embed=discord.Embed(
            title="🏆 Match Over!",
            description=f"**Winner:** {winner.display_name}\nFinal Score: {scores[winner.id]} - {scores[loser.id]}"
        ))

    finally:
        _IN_PROGRESS.discard(ctx.author.id)
        _IN_PROGRESS.discard(opponent.id)


# ----------------------------\
# Leaderboard command
# ----------------------------
async def show_leaderboard(ctx: commands.Context):
    board = load_leaderboard()
    if not board:
        return await ctx.send("No games played yet.")

    sorted_board = sorted(board.items(), key=lambda x: (-x[1]["wins"], x[1]["losses"]))
    embed = discord.Embed(title="🏆 Rock Paper Scissors Leaderboard", color=discord.Color.gold())
    for i, (uid, stats) in enumerate(sorted_board[:5], start=1):
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else f"User {uid}"
        embed.add_field(name=f"{i}. {name}", value=f"Wins: {stats['wins']} | Losses: {stats['losses']}", inline=False)
    embed.set_footer(text="Keep playing to climb the ranks!")
    await ctx.send(embed=embed)


# --------------------------
# Rules command
# ----------------------------
async def show_rules(ctx: commands.Context):
    embed = discord.Embed(title="📜 Rock Paper Scissors Rules", color=discord.Color.blue())
    embed.add_field(name="How to Play", value="Challenge someone with `nga rps @user`. Vote on rounds, then pick Rock, Paper, or Scissors each round.", inline=False)
    embed.add_field(name="Surprise Mechanics", value="\n".join(
        f"**{name.replace('_', ' ').title()}** — {int(chance*100)}% chance per round"
        for name, chance in SETTINGS["surprise_chances"].items()
    ), inline=False)
    await ctx.send(embed=embed)


# ----------------------------
# Setup function
# ----------------------------
def setup_rps(bot: commands.Bot):
    @bot.command(name="rps")
    async def _rps(ctx, opponent: discord.Member):
        await play_rps(ctx, opponent)

    @bot.command(name="rpsboard")
    async def _rpsboard(ctx):
        await show_leaderboard(ctx)

    @bot.command(name="rpsrules")
    async def _rpsrules(ctx):
        await show_rules(ctx)
