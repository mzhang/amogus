import discord
import os
import random
from dotenv import load_dotenv

# Do some setup
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

#amogus discord bot
class Game: 
    def __init__(self, tasks_to_win, imposter_count):
        self.players = []
        self.tasks_to_win = tasks_to_win
        self.imposter_count = imposter_count
    
    async def send_roles(self):
        imposters = random.sample(self.players, self.imposter_count)
        for player in self.players:
            if player in imposters:
                await player.send(f"You are an imposter. All the imposters are {imposters}")
            else:
                await player.send("You are a crewmate.")
        print("sent roles")
    
    def add_player(self, player):
        self.players.append(player)

    def start_timer(self):
        # start 7 min python timer
        print("timer started")


def get_tasks():
    # Returns 4 tasks, one easy, one medium, one hard, and one random
    easy_tasks = []
    medium_tasks = []
    hard_tasks = []
    with open("easy.txt", "r") as f:
        for line in f:
            easy_tasks.append(line.strip())

    with open("medium.txt", "r") as f:
        for line in f:
            medium_tasks.append(line.strip())

    with open("hard.txt", "r") as f:
        for line in f:
            hard_tasks.append(line.strip())

    tasks = easy_tasks + medium_tasks + hard_tasks

    easy_task = random.choice(easy_tasks)
    medium_task = random.choice(medium_tasks)
    hard_task = random.choice(hard_tasks)
    random_task = random.choice(tasks)

    return [easy_task, medium_task, hard_task, random_task]

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# sign up for next game
# start game
#    - start timer
# meeting
# task counter
# reset game

game = Game()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('.getRole'):
        await message.channel.send('Hello!')
    

client.run(os.getenv("SECRET_TOKEN"))
