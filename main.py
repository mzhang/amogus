import discord
import os
import random
import asyncio
import time
from dotenv import load_dotenv
from discord.ext import commands

# Do some setup
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)


# amogus discord bot
class Game:
    def __init__(self, tasks_to_win, imposter_count):
        self.players = []
        self.tasks_to_win = tasks_to_win
        self.imposter_count = imposter_count

    async def _timer(self):
        print("here")
        while self.timer > 0:
            print("here")
            await asyncio.sleep(1)
            if self.timer_running:
                self.timer -= 1

            print(f"Time left: {self.timer} seconds")

        if self.timer == 0:
            print("Game over - time ran out!")

    async def send_roles(self):
        imposters = random.sample(self.players, self.imposter_count)
        imposter_names = []
        for imposter in imposters:
            imposter_names.append(imposter.name)

        for player in self.players:
            if player in imposters:
                await player.send(
                    f"You are an imposter. All the imposters are {imposter_names}"
                )
            else:

                await player.send("You are a crewmate.")
        print("sent roles")

    def add_player(self, player):
        self.players.append(player)

    def emergency(self):
        # Pause the timer
        self.timer_running = False
        print("emergency started")

    def meeting(self, ctx):
        # start 1 min python timer
        self.meeting_timer = 60
        while self.meeting_timer > 0:
            self.meeting_timer -= 1
            if self.meeting_timer % 10 == 0:
                ctx.send(f"Meeting time left: {self.meeting_timer} seconds")
            time.sleep(1)

    def resume(self):
        self.timer_running = True
        print("game resumed")

    async def start_game(self):
        print("game started")
        await self.send_roles()

        # init timer to 7 minutes
        self.timer = 7 * 60
        self.timer_running = False
        asyncio.run(self._timer())


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


# sign up for next game
# start game
#    - start timer
# meeting
# task counter
# reset game

game = None


@bot.command()
async def start(ctx):
    global game

    if game is None:
        print("game is none")
        return

    ctx.send("Game started!")
    await game.start_game()


@bot.command()
async def signup(ctx):
    global game

    if game is None:
        print("game is none")
        return

    game.add_player(ctx.author)
    await ctx.send("Added you!")


@bot.command()
async def reset(ctx):
    global game

    # Get the specified number of tasks/imposters from the message
    split_message = ctx.message.content.split(" ")
    tasks = int(split_message[1])
    imposters = int(split_message[2])

    game = Game(tasks, imposters)
    await ctx.send("Game reset!")


@bot.command()
async def emergency(ctx):
    global game
    game.emergency()
    await ctx.send("@everyone Emergency meeting called!")


@bot.command()
async def meeting(ctx):
    global game
    game.meeting(ctx)
    await ctx.send("Meeting timer started!")


@bot.command()
async def resume(ctx):
    global game
    game.resume()
    await ctx.send("Game resumed!")


bot.run(os.getenv("SECRET_TOKEN"))
