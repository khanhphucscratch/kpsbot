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
codeforces_verifying_account = {}
existed_account = set()
current_training_status = {}

@bot.tree.command(
    name="hello",
    description="Say hello to someone!"
)
async def say_hello(interaction: discord.Interaction, name: str):
    await interaction.response.send_message("Hello " + name)

import json
@bot.tree.command(
    name="backup",
    description="Backup the data. Admin only"
)
async def backup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You don't have permission to use this command!",
                ephemeral=True
            )
            return
    with open("backup_data.json", "w") as f:
        json.dump(
            {user_id: list(handles) for user_id, handles in codeforces_account.items()},
            f,
            indent=4
        )
    await interaction.response.send_message("Backup finished")

@bot.tree.command(
    name="load_backup",
    description="Load all backup data. Admin only"
)
async def load_backup(interaction: discord.Interaction):
    global codeforces_account
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You don't have permission to use this command!",
            ephemeral=True
        )
        return
    with open("backup_data.json", "r") as f:
        raw_data = json.load(f)
    codeforces_account = {
        int(user_id): set(handles)
        for user_id, handles in raw_data.items()
    }
    existed_account.clear()
    for id, handle_list in codeforces_account.items():
        for handle in handle_list:
            existed_account.add(handle)

    await interaction.response.send_message("Loaded all the data")

#Account manager
import time
import codeforces
@bot.tree.command(
    name="add_handle",
    description="Add a Codeforces handle"
)
async def add_handle(interaction: discord.Interaction, handle: str):
    await interaction.response.defer()
    user_id = interaction.user.id
    if user_id not in codeforces_account:
        codeforces_account[user_id] = set()
    if len(codeforces_account[user_id]) >= 3:
        await interaction.followup.send("No more than 3 accounts for each user")
        return
    if codeforces_verifying_account.get(user_id) is not None:
        ltime = codeforces_verifying_account[user_id][1]
        last_handle = codeforces_verifying_account[user_id][0]
        existed_account.discard(last_handle)
        if time.time() > ltime + 300:
            codeforces_verifying_account.pop(user_id, None)
            await interaction.followup.send("Verification expired. Try again.")
            return
        await interaction.followup.send("Be careful. You are verifying another account. This with nullify that process")
    if handle in existed_account:
        await interaction.followup.send("Registered handle / handle in the process of registration")
        return
    codeforces_verifying_account[user_id] = (handle, time.time())
    existed_account.add(handle)
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

    msg = "Sucessfully added handle " + handle + " to " + str(user)
    await interaction.followup.send(msg)


@bot.tree.command(
    name="delete_handle",
    description="Delete current handle"
)
async def delete_handle(interaction: discord.Interaction, handle: str):
    user = interaction.user
    user_id = interaction.user.id
    if user_id not in codeforces_account:
        await interaction.response.send_message("Find no such registered handle")
        return
    if handle not in codeforces_account[user_id]:
        await interaction.response.send_message("Find no such registered handle")
        return
    codeforces_account[user_id].discard(handle)
    existed_account.discard(handle)
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



@bot.tree.command(
    name = "train_getproblem",
    description="Recommend a problem"
)
async def train_getproblem(interaction: discord.Interaction, min_rating: int, max_rating: int, hide_rating: bool, minimum_id: int = 0):
    await interaction.response.defer()
    user_id = interaction.user.id
    if current_training_status.get(user_id) is not None:
        await interaction.followup.send("You are training on a problem. Keep training, or use train_giveup / train_completed")
        return
    
    handle_list = codeforces_account[user_id]
    recommended_problem = await codeforces.recommend_problems_for_user(handle_list, min_rating = min_rating, max_rating = max_rating, minimum_id = minimum_id)
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

@bot.tree.command(
    name = "current_problem",
    description="Your current problem"
)
async def current_problem(interaction: discord.Interaction):
    user = interaction.user
    user_id = interaction.user.id
    if current_training_status.get(user_id) is None:
        await interaction.response.send_message("You are not currently solving a problem")
        return

    problem = current_training_status.get(user_id)
    await interaction.response.send_message("User " + str(user) + " is solving problem " + problem.problem.url)
    return
bot.run(TOKEN)