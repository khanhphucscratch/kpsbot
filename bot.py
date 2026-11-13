import os
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()
codeforces_account = {}
@bot.tree.command(
    name="hello",
    description="Say hello to someone!"
)
async def say_hello(interaction: discord.Interaction, name: str):
    await interaction.response.send_message("Hello " + name)


#Account manager
import time
import codeforces
codeforces_verifying_account = {}
@bot.tree.command(
    name="add_handle",
    description="Add a Codeforces handle"
)
async def add_handle(interaction: discord.Interaction, handle: str):
    await interaction.response.defer()
    user = interaction.user
    user_id = interaction.user.id
    if user_id not in codeforces_account:
        codeforces_account[user_id] = set()
    if len(codeforces_account[user_id]) >= 3:
        await interaction.followup.send("No more than 3 accounts for each user")
        return
    if handle in codeforces_account[user_id]:
        await interaction.followup.send("Registered handle")
        return
    if codeforces_verifying_account.get(user_id) is not None:
        ltime = codeforces_verifying_account[user_id][1]
        if time.time() > ltime + 300:
            codeforces_verifying_account.pop(user_id, None)
            await interaction.followup.send("Verification expired. Try again.")
            return
        await interaction.followup.send("Be careful. You are verifying another account. This with nullify that process")
    codeforces_verifying_account[user_id] = (handle, time.time())
    msg = f"{handle}, you have 5 minutes to submit a compile error to this problem: https://codeforces.com/problemset/problem/4/A"
    await interaction.followup.send(msg)

@bot.tree.command(
    name="verify_handle",
    description="Verify a Codeforces handle"
)
async def verify_handle(interaction: discord.Interaction):
    await interaction.response.defer()

    user = interaction.user
    user_id = interaction.user.id
    if codeforces_verifying_account.get(user_id) is None:
        await interaction.followup.send("You are verifying no handle. Use /add_handle first")
        return
    handle, ltime = codeforces_verifying_account[user_id]
    result = await codeforces.verifying_account(handle, ltime, ltime + 300)
    if result == False:
        await interaction.followup.send("Find no submission to verify " + handle)
        return

    if user_id not in codeforces_account:
        codeforces_account[user_id] = set()
    codeforces_account[user_id].add(handle)
    codeforces_verifying_account[user_id] = None

    info_data = await codeforces.get_user_info(handle)
    rating = info_data["result"][0].get("rating", "Unrated")
    msg = "Sucessfully added handle " + handle + " to " + str(user) + "\nRating: " + str(rating)
    await interaction.followup.send(msg)


@bot.tree.command(
    name="delete_handle",
    description="Delete current handle"
)
async def clear_handle(interaction: discord.Interaction, handle: str):
    user = interaction.user
    user_id = interaction.user.id
    if user_id not in codeforces_account:
        await interaction.response.send_message("Find no such registered handle")
        return
    if handle not in codeforces_account[user_id]:
        await interaction.response.send_message("Find no such registered handle")
        return
    codeforces_account[user_id].remove(handle)
    await interaction.response.send_message("Clear handle for user " + str(user))


@bot.tree.command(
    name="show_handle_list",
    description="See all current handle"
)
async def show_handle_list(interaction: discord.Interaction):
    user = interaction.user
    user_id = interaction.user.id
    if user_id not in codeforces_account:
        codeforces_account[user_id] = set()

    msg = ""
    for handle in codeforces_account[user_id]:
        msg += handle + " "
    await interaction.response.send_message("All handle of user " + str(user) + ": " + msg)

#Actually recommend problem
from dataclasses import dataclass
from typing import Any
@dataclass
class Problem:
    oj: str
    problem: Any


current_training_status = {}

@bot.tree.command(
    name = "train_getproblem",
    description="Recommend a problem"
)
async def train_getproblem(interaction: discord.Interaction, min_rating: int, max_rating: int, hide_rating: bool):
    await interaction.response.defer()
    user_id = interaction.user.id
    if current_training_status.get(user_id) is not None:
        await interaction.followup.send("You are training on a problem. Keep training, or use train_giveup / train_completed")
        return
    
    handle_list = codeforces_account[user_id]
    recommended_problem = await codeforces.recommend_problems_for_user(handle_list, min_rating = min_rating, max_rating = max_rating)
    if len(recommended_problem) == 0:
        await interaction.followup.send("Found no problem")
        return

    chosen_problem = recommended_problem[0]
    current_training_status[user_id] = Problem(oj = "codeforces", problem = chosen_problem)

    await interaction.followup.send(f"Found a problem for you! \nProblem link: {chosen_problem.url}, rating = {chosen_problem.rating if hide_rating == False else '?'}")
    return
@bot.tree.command(
    name = "train_giveup",
    description="Giveup your current problem"
)
async def train_giveup(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    if current_training_status.get(user_id) is None:
        await interaction.followup.send("Find no ongoing problem")
        return

    problem = current_training_status[user_id].problem
    msg = f"Give up on problem {str(problem)} \nrating: {problem.rating}" 
    current_training_status[user_id] = None
    await interaction.followup.send(msg)
    return

@bot.tree.command(
    name = "train_completed",
    description="Completed your current problem"
)
async def train_completed(interaction: discord.Interaction):
    await interaction.response.defer()
    user = interaction.user
    user_id = interaction.user.id
    if current_training_status.get(user_id) is None:
        await interaction.followup.send("Find no ongoing problem")
        return

    problem = current_training_status[user_id].problem
    problem_code = (problem.contestId, problem.index)
    handle_list = codeforces_account[user_id]

    result = await codeforces.check_if_accepted(handle_list, problem_code)
    if result == True:
        msg = f"{user} got Accepted on problem: {str(problem)} \nrating: {problem.rating}"
        current_training_status[user_id] = None
        await interaction.followup.send(msg)
    else:
        await interaction.followup.send("Found no Accepted submission. Continue your training!")
    return
bot.run(TOKEN);