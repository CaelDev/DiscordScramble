# load bot token from hidden file
with open("token.txt") as f:
    TOKEN = f.read()

# imports
import discord  # https://pypi.org/project/discord.py/
from discord import app_commands
from discord.ext import commands, tasks
from better_profanity import (
    profanity,
)  # https://pypi.org/project/better-profanity/
import requests, os, time, json, math, random, os.path
from english_words import (
    get_english_words_set,
)  # https://pypi.org/project/english-words/
from random import shuffle
from random_word import RandomWords  # https://pypi.org/project/Random-Word/

r = RandomWords()

intents = discord.Intents.default()  # set intents

# create bot and tree
bot = commands.Bot(command_prefix="", intents=intents)


# check to make sure database json files exist
if not os.path.isfile("servers.json"):
    with open("servers.json", "w") as f:
        f.write("{}")
if not os.path.isfile("users.json"):
    with open("users.json", "w") as f:
        f.write("{}")


# basic functions for bot startup
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="the waves")
    )
    checkWordExpire.start()  # start background loop
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


# used to handle messages, not relevant as of now
@bot.event
async def on_message(message):
    return


# handles for when the bot is added to a server
@bot.event
async def on_guild_join(guild):
    addServer(guild.id)


# adds a server to the bots database
def addServer(serverid):
    with open("servers.json") as f:
        data = json.loads(f.read())
    if serverid not in data:  # make sure data isnt already saved
        data.update(
            {
                serverid: {
                    "solved": 0,
                    "wordChannel": "",
                    "currentWord": "",
                    "expires": 0,
                    "lastGuess": 0,
                }
            }
        )
        with open("servers.json", "w") as f:
            f.write(json.dumps(data, indent=3))


# generates a random English word no longer than maxLen
def getRandomWord(maxLen):
    word = r.get_random_word()  # get random lowercase word
    while (len(word) > maxLen or len(word) < 3) and (
        profanity.contains_profanity(word) != True
    ):  # make sure word isnt too long or too short AND ensure that word does not have profanity
        word = r.get_random_word()
    return word


# takes input to determine if a user guess was correct and adjusts accordingly
def solve(serverid, userid, guess):
    with open(f"servers.json") as f:  # load database data
        data = json.loads(f.read())
    serverid = str(serverid)
    if data[serverid]["currentWord"] == "" or data[serverid]["expires"] < int(
        time.time()
    ):  # make sure there is a word active
        embed = discord.Embed(
            title="No word",
            description="There is currently no active word, please try again later",
            color=0xFF0000,
        )
        return embed
    elif (
        int(time.time()) < int(data[serverid]["lastGuess"]) + 30
    ):  # make sure guess isnt on cooldown
        embed = discord.Embed(
            title="Cooldown",
            description=f"Guess on cooldown for {int(data[serverid]['lastGuess']) + 30 - int(time.time())} more seconds!",
            color=0xFFD60A,
        )
        return embed
    elif guess != data[serverid]["currentWord"]:  # check if the guess is incorrect
        data[serverid]["lastGuess"] = int(time.time())  # add cooldown
        with open("servers.json", "w") as f:  # write the new data to the database
            f.write(json.dumps(data, indent=3))
        embed = discord.Embed(
            title="Incorrect",
            description="Incorrect guess! 30 second guess cooldown starts now!",
            color=0xFF0000,
        )
        return embed
    else:  # if the guess was correct:
        data[serverid]["lastGuess"] = 0  # reset guess cooldown
        data[serverid]["currentWord"] = getRandomWord(
            random.randint(4, 8)
        )  # random word length 4-8
        data[serverid]["expires"] = (
            int(time.time()) + 1 * 60 * 15
        )  # 15 min expiration time
        data[serverid]["solved"] += 1
        with open("servers.json", "w") as f:  # write the new data to the database
            f.write(json.dumps(data, indent=3))

        x = list(data[serverid]["currentWord"])
        random.shuffle(x)
        embed = discord.Embed(
            title="Correct!",
            description=f"The word was {guess}. New word has been generated: **"
            + "".join(x)
            + f"** (expires <t:{data[serverid]['expires']}:R>)",
            color=0x0AFF54,
        )
        addPoint(userid, guess)
        return embed


def addPoint(userid, word):
    userid = str(userid)
    with open("users.json") as f:
        data = json.loads(f.read())
    if str(userid) not in data:
        data.update({str(userid): {"correct": 1, "words": [word]}})
    else:
        data[userid]["correct"] += 1
        if word not in data[userid]["words"]:
            data[userid]["words"].append(word)
    with open("users.json", "w") as f:
        f.write(json.dumps(data, indent=3))


def getStats(serverid):  # gets server solve stats (pretty basic right now)
    with open("servers.json") as f:
        data = json.loads(f.read())
    embed = discord.Embed(
        title="Server Stats",
        description=f"The server has solved **{data[str(serverid)]['solved']} scrambles!**",
        color=0xFFD60A,
    )
    return embed


def getPersonalStats(userid, username):
    with open("users.json") as f:
        data = json.loads(f.read())
    if str(userid) in data:
        embed = discord.Embed(
            title=f"{username}'s Stats",
            description=f"Questions solved: {data[str(userid)]['correct']} \n{len(data[str(userid)]['words'])} / 146600 possible words solved",  # possible words determined by filtering database for words between 4 and 8 chars
            color=0xFFD60A,
        )
    else:
        embed = discord.Embed(
            title=f"{username}'s Stats",
            description=f"Questions solved: 0 \n0 / 146600 possible words solved",
            color=0xFFD60A,
        )
    return embed


def getCommandChannel(serverid):
    with open("servers.json") as f:
        data = json.loads(f.read())
    return data[str(serverid)]["wordChannel"]


# creates slash command for guess input
@bot.tree.command(name="unscramble", description="Unscramble a hidden word")
async def unscramble(interaction, unscrambled: str):  # handles slash command usage
    """Unscramble a hidden word

    Parameters
    -----------
    unscrambled: str
        the unscrambled word
    """
    if getCommandChannel(interaction.guild.id) == "":
        embed = discord.Embed(
            title="Error",
            description=f"No channel registered! Please use /setchannel to set the unscrambling channel!",
            color=0xFF0000,
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )
    elif interaction.channel.id != getCommandChannel(interaction.guild.id):
        embed = discord.Embed(
            title="Error",
            description=f"Wrong channel! Use <#{getCommandChannel(interaction.guild.id)}>",
            color=0xFF0000,
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=solve(interaction.guild.id, interaction.user.id, unscrambled)
        )


# creates slash command for stat retrieval
@bot.tree.command(name="serverstats", description="Display server unscramble stats")
async def serverstats(interaction):  # handles slash usage
    await interaction.response.send_message(embed=getStats(interaction.guild.id))


@bot.tree.command(name="stats", description="Display personal unscramble stats")
async def stats(interaction):
    await interaction.response.send_message(
        embed=getPersonalStats(interaction.user.id, interaction.user.name)
    )


@bot.tree.command(
    name="setchannel",
    description="Sets the current channel as the channel to register unscrambles",
)
@commands.has_permissions(manage_messages=True)
async def setChannel(interaction):
    if (
        interaction.user.top_role.permissions.administrator
        or interaction.user.guild_permissions.administrator
    ):
        with open("servers.json") as f:
            data = json.loads(f.read())
        data[str(interaction.guild.id)]["wordChannel"] = interaction.channel.id
        with open("servers.json", "w") as f:
            f.write(json.dumps(data, indent=3))
        embed = discord.Embed(
            title="Success",
            description=f"Channel has been set to <#{interaction.channel.id}>",
            color=0x0AFF54,
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description=f"Only admins can use this command!",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)


@tasks.loop(seconds=15)  # loops every 15 seconds
async def checkWordExpire():  # check if a server has expired words, and if so will randomly refresh them
    with open("servers.json") as f:
        data = json.loads(f.read())
    for i in data:
        if data[i]["wordChannel"] != "":
            if data[i]["expires"] < int(time.time()):  # run only for expired words
                # once a word has expired, create a random-ish time frame to start a new guess
                if (
                    random.randint(0, 100) == 50
                ):  # 01% chance to trigger... aka ~1500 seconds (25 mins) after expiration
                    data[i]["lastGuess"] = 0  # reset guess cooldown
                    data[i]["currentWord"] = getRandomWord(
                        random.randint(4, 8)
                    )  # random word length 4-8
                    data[i]["expires"] = (
                        int(time.time()) + 1 * 60 * 15
                    )  # 15 min expiration time
                    data[i]["solved"] += 1

                    with open("servers.json", "w") as f:
                        f.write(json.dumps(data, indent=3))

                    x = list(data[i]["currentWord"])
                    random.shuffle(x)
                    channel = bot.get_channel(data[i]["wordChannel"])
                    embed = discord.Embed(
                        title="New Word",
                        description="New word has been generated: **"
                        + "".join(x)
                        + f"** (expires <t:{data[i]['expires']}:R>)",
                        color=0xFFD60A,
                    )
                    await channel.send(embed=embed)


bot.run(TOKEN)  # run the bot
