#load bot token from hidden file
with open("token.txt") as f:
    TOKEN = f.read()

# imports
import discord
from discord import app_commands
from discord.ext import commands, tasks
from better_profanity import (
    profanity,
)
import requests, os, time, json, math, random
from english_words import get_english_words_set
from random import shuffle

intents = discord.Intents.default()  # set intents
intents.messages = True

#create bot and tree
bot = commands.Bot(command_prefix="", intents=intents)
tree = app_commands.CommandTree(bot)

#basic functions for bot startup
@bot.event
async def on_ready():
    checkWordExpire.start() #start background loop
    await tree.sync(guild=discord.Object()) #add slash commands to tree
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

#used to handle messages, not relevant as of now
@bot.event
async def on_message(message):
    return

#handles for when the bot is added to a server
@bot.event
async def on_guild_join(guild):
    addServer(guild.id)

#adds a server to the bots database
def addServer(serverid):
    with open("servers.json") as f:
        data = json.loads(f.read())
    data.update({serverid: {"solved": 0, "wordChannel": "", "currentWord": "", "expires": 0, "lastGuess": 0}})
    with open("servers.json", "w") as f:
        f.write(json.dumps(data, indent=3))

#generates a random English word no longer than maxLen
def getRandomWord(maxLen):
    x = 999
    while x > maxLen:
        word = random.choice(get_english_words_set(["web2"], lower=True)) #get random lowercase word
        x = len(word)
    return word 

#takes input to determine if a user guess was correct and adjusts accordingly
def solve(serverid, userid, guess):
    with open(f"servers.json") as f: #load database data
        data = (json.loads(f.read()))
    if data[serverid]["currentWord"] or data[serverid]["expires"] < int(time.time()) == "": #make sure there is a word active
        return "No word currently!"
    if int(time.time()) < int(data[serverid]["lastGuess"]) + 30: #make sure guess isnt on cooldown
        return f"Guess on cooldown for {int(data[serverid]["lastGuess"]) + 30 - int(time.time())} more seconds!"
    if guess != data[serverid]["currentWord"]: #check if the guess is incorrect
        data[serverid]["lastGuess"] = int(time.time()) #add cooldown
        return "Incorrect guess! 30 second guess cooldown starts now!"
    else: #if the guess was correct:
        data[serverid]["lastGuess"] = 0 #reset guess cooldown
        data[serverid]["currentWord"] = getRandomWord(random.randint(4,8)) #random word length 4-8
        data[serverid]["expires"] = int(time.time()) + 1*60*15 #15 min expiration time
        data[serverid]["solved"] += 1
    with open("servers.json", "w") as f: #write the new data to the database
        f.write(json.dumps(data, indent=3))
    return "Correct! New word has been generated: " + ''.join(shuffle(list(data[serverid]["currentWord"])))

def getStats(serverid): #gets server solve stats (pretty basic right now)
    with open("servers.json") as f:
        data = json.loads(f.read())
    return f"The server has solved {data[serverid]["solved"]} scrambles!"

#creates slash command for guess input
@tree.command(
    name="Unscramble!",
    description="Unscramble a hidden word"
)
async def unscramble(interaction, unscrambled: str): #handles slash command usage
    """Unscramble a hidden word

    Parameters
    -----------
    unscrambled: str
        the unscrambled word
    """
    interaction.response.send_message(solve(interaction.guild.id, interaction.user.id, unscrambled))

#creates slash command for stat retrieval
@tree.command(
    name="Stats",
    description="Display server unscramble stats"
)
async def stats(interaction): #handles slash usage
    interaction.reponse.send_message(getStats(interaction.guild.id))

@tasks.loop(seconds=15) #loops every 15 seconds
async def checkWordExpire(): #check if a server has expired words, and if so will randomly refresh them
    with open("servers.json") as f:
        data = json.loads(f.read())
    for i in data:
        if i["expires"] < int(time.time()): #run only for expired words
            #once a word has expired, create a random-ish time frame to start a new guess
            if random.randint(0, 200) == 100: # 0.5% chance to trigger... aka ~3000 seconds (50 mins) after expiration
                data[i]["lastGuess"] = 0 #reset guess cooldown
                data[i]["currentWord"] = getRandomWord(random.randint(4,8)) #random word length 4-8
                data[i]["expires"] = int(time.time()) + 1*60*15 #15 min expiration time
                data[i]["solved"] += 1

                channel = discord.get_channel(data[i]["wordChannel"])
                await channel.send("New word has been generated: " + ''.join(shuffle(list(data[i]["currentWord"]))))



bot.run(TOKEN)  # run the bot