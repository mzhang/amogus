import discord
import os
from dotenv import load_dotenv
load_dotenv()

#amogus discord bot
class Game: 
    def __init__(self, players, tasks_to_win, imposter_count):
        self.players = players
        self.tasks_to_win = tasks_to_win
        self.imposter_count = imposter_count
    
    def send_roles():
        pass

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# sign up for next game
# start game
#    - start timer
# meeting
# task counter
# reset game

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('.getRole'):
        await message.channel.send('Hello!')

client.run(os.getenv("SECRET_TOKEN"))
