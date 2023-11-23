import discord
import os
import random
from enum import Enum
from dotenv import load_dotenv
from discord.ext import tasks

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

class State(Enum):
    INIT = 'init'
    SETUP = 'setup'
    IN_PROGRESS = 'in_progress'
    PAUSED = 'paused'
    MEETING = 'meeting'

class Executor(discord.Bot):
    def __init__(self):
        super().__init__(intents = intents)
        self.state = State.INIT
        self.easy_tasks = []
        self.medium_tasks = []
        self.hard_tasks = []
        self.players = set()

        #internal state
        self.remaining_tasks = 0
        self.game_time = 0
        self.meeting_time = 0
        self.kill_start_countdown = 0
        self.kill_start_countdown_cur = self.kill_start_countdown

        #game parameters
        self.imposter_count = 0
        self.tasks_per_person = 0
        self.meeting_length = 0
        self.channel = None

        #load tasks
        with open("easy.txt", "r") as f:
            for line in f:
                self.easy_tasks.append(line.strip())
        with open("medium.txt", "r") as f:
            for line in f:
                self.medium_tasks.append(line.strip())
        with open("hard.txt", "r") as f:
            for line in f:
                self.hard_tasks.append(line.strip())
        
        self.add_commands()
        self.timer.start()
            
    def get_player_tasks(self):
        tasks = set()
        num_tasks = self.tasks_per_person

        # add equal number of tasks from each difficulty when possible
        if num_tasks >= 3:
            tasks.update(random.sample(self.easy_tasks, num_tasks // 3))
            tasks.update(random.sample(self.medium_tasks, num_tasks // 3))
            tasks.update(random.sample(self.hard_tasks, num_tasks // 3))
        
        while(len(tasks) < num_tasks):
            #add task of random difficulty to fill out rest of tasks
            difficulty = random.randint(0, 2)
            if difficulty == 0:
                tasks.add(random.choice(self.easy_tasks))
            elif difficulty == 1:
                tasks.add(random.choice(self.medium_tasks))
            else:
                tasks.add(random.choice(self.hard_tasks))

        return tasks

    @tasks.loop(seconds=1)
    async def timer(self):
        if self.state == State.IN_PROGRESS:
            self.game_time -= 1
            print("game time:", self.game_time)
            
            if self.game_time % 60 == 0 or self.game_time < 10:
                await self.channel.send(f"Crewmates have {self.game_time}s left to finish {self.remaining_tasks} tasks!")
            
            if self.game_time == 0:
                self.end()
                await self.channel.send("@everyone Game has finished!")
                return
            
            self.kill_start_countdown_cur -= 1
            if self.kill_start_countdown_cur == 0:
                await self.channel.send("@everyone Imposters can now kill!")
                return
            
        elif self.state == State.MEETING:
            self.meeting_time -= 1
            print("meeting time:", self.meeting_time)

            if self.meeting_time == 0:
                self.kill_start_countdown_cur = self.kill_start_countdown
                await self.channel.send("@everyone The meeting has ended! Vote out who you think is the imposter.")
                return
            elif self.meeting_time % 20 == 0:
                await self.channel.send(f"@everyone {self.meeting_time}s left in the meeting!")
                return
            
    def end(self):
        #reset game state
            self.players = set()

            self.remaining_tasks = 0
            self.game_time = 0
            self.meeting_time = 0

            self.imposter_count = 0
            self.tasks_per_person = 0
            self.meeting_length = 0
            self.channel = None

            self.state = State.INIT
        
    def add_commands(self):
        @self.command()
        async def test(ctx): 
            await ctx.respond("test")
    
        @self.command(description="Start a new game")
        async def new_game(ctx, 
                            tasks_to_win: int, 
                            imposter_count: int, 
                            tasks_per_person: discord.Option(int, default = 4, description="default 4"), 
                            game_length: discord.Option(int, default = 420, description="default 420s"), 
                            meeting_length: discord.Option(int, default = 60, description="default 60s"),
                            kill_start_countdown: discord.Option(int, default = 10, description="default 10s")
                        ):
            
            if self.state != State.INIT:
                await ctx.respond("Error: Game already in progress!")
                return
            
            self.state = State.SETUP
            self.remaining_tasks = tasks_to_win
            self.imposter_count = imposter_count
            self.tasks_per_person = tasks_per_person
            self.game_time = game_length
            self.meeting_length = meeting_length
            self.meeting_time = meeting_length
            self.kill_start_countdown = kill_start_countdown
            self.kill_start_countdown_cur = kill_start_countdown
            self.channel = ctx.channel
            await ctx.respond(f"New game created with {tasks_to_win} tasks to win, {imposter_count} imposters! The game will last {game_length} seconds, and meetings will last {meeting_length} seconds! {kill_start_countdown} seconds before imposters can kill!")
        
        @self.command(description="Join the game")
        async def join(ctx):
            if self.state != State.SETUP:
                await ctx.respond("Error: Game has not been created yet!")
                return
        
            self.players.add(ctx.author)
            await ctx.respond(f"Added {ctx.author.name} to the game! {len(self.players)} players have joined so far!")
        
        @self.command(description="Start the game")
        async def start_game(ctx):
            if self.state != State.SETUP:
                await ctx.respond("Error: Game has not been created yet!")
                return
            
            if len(self.players) < self.imposter_count:
                await ctx.respond(f"We can't start the game yet - {len(self.players)} players have joined, but we need at least {self.imposter_count} players to be imposters!")
                return
            
            self.state = State.IN_PROGRESS

            imposters = random.sample(self.players, self.imposter_count)
            imposter_names = "\n".join([imposter.name for imposter in imposters])

            #distribute roles
            for player in self.players:
                role_message = f"You are a crewmate. " if player not in imposters else f"You are an imposter. The imposters this game are: \n\n{imposter_names}"
                tasks = self.get_player_tasks()
                task_message = "Your tasks are:\n\n" + "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
                await player.send(role_message + "\n\n" + task_message)

            await ctx.respond(f"Game has started! Crewmates have {self.game_time}s to finish {self.remaining_tasks} tasks!")
        
        @self.command(name="task", description="Write 2-3 sentences about what you did to finish the task!")
        async def complete_task(ctx, task_writeup: str):
            if self.state != State.IN_PROGRESS:
                await ctx.respond("Error: Game not in progress!")
                return
            self.remaining_tasks -= 1
            if self.remaining_tasks == 0:
                await ctx.respond(f"Crewmates have finished all their tasks!")
                self.end()
                await ctx.respond("@everyone Game has finished!")
            
            await ctx.respond(f"{ctx.author.name} has finished a task! {ctx.author.name} wrote: \"{task_writeup}\". Crewmates have {self.remaining_tasks} tasks left to finish!")
        
        @self.command(description="Call an emergency meeting")
        async def emergency(ctx):
            if self.state != State.IN_PROGRESS:
                await ctx.respond("Error: Game not in progress!")
                return
            self.state = State.PAUSED
            await ctx.respond("@everyone Emergency meeting called! Drop what you're doing and go to the meeting room ASAP!")

        @self.command(description="Start the meeting")
        async def start_meeting(ctx):
            if self.state != State.PAUSED:
                await ctx.respond("Error: Emergency meeting has not been called!")
                return
            
            self.state = State.MEETING
            self.meeting_time = self.meeting_length
            await ctx.respond(f"@everyone The meeting has started! Crewmates have {self.meeting_time} seconds to discuss!")

        @self.command(description="End the meeting")
        async def end_meeting(ctx):
            if self.state != State.MEETING:
                await ctx.respond("Error: Meeting has not started!")
                return
            
            self.state = State.IN_PROGRESS
            await ctx.respond(f"@everyone The meeting has ended! Crewmates have {self.remaining_tasks} tasks left to finish with {self.game_time}s left!")
        
        @self.command(description="End the game")
        async def end_game(ctx):
            #reset game state
            self.players = set()

            self.remaining_tasks = 0
            self.game_time = 0
            self.meeting_time = 0

            self.imposter_count = 0
            self.tasks_per_person = 0
            self.meeting_length = 0
            self.channel = None

            self.state = State.INIT

            await ctx.respond(f"@everyone Game has ended! Please return to the meeting room!")

        @self.command(description="Get the rules of the game")
        async def rules(ctx):
            await ctx.respond(
                """```\n
                Rules:
                1. only imposter can run or open doors (to use staircases or elevators)
                2. no talking at all outside of meetings
                3. don't lie about tasks. when completing a task, write 3 sentences tangentially related about what you did
                4. if the crewmates finish all their tasks, they win. if the imposters kill everyone or the timer runs out, the imposters win.
                5. to kill someone, tap them 3 times
                6. you can call a meeting when you find someone dead or once when youre inside of the cafe
                7. an imposter can only kill once every 10 seconds
                8. if youre dead, stay in place (sitting down) until someone finds you and calls a meeting for you
                9. use common sense
                \n```""".replace("    ", "")
            )

bot = Executor()
bot.run(os.getenv("SECRET_TOKEN"))
