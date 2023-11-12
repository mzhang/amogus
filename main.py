import discord
import os
import random
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

# amogus discord bot
# handles timer logic and any interface with discord
class MyClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = None
        self.channel = None
        self.players = []        
        self.easy_tasks = []
        self.medium_tasks = []
        self.hard_tasks = []

        self.add_commands()

    async def on_ready(self):
        await self.timer.start()
    
    def check_game_existence(self, func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'game') and self.game is not None:
                return func(self, *args, **kwargs)
            else:
                print("Please create a game first!")
                if self.channel is not None:
                    self.channel.send("Please create a game first!")
        return wrapper

    def load_tasks(self):
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

        self.easy_tasks = easy_tasks
        self.medium_tasks = medium_tasks
        self.hard_tasks = hard_tasks

    def get_tasks_for_player(self):
        if self.easy_tasks is None or self.medium_tasks is None or self.hard_tasks is None:
            self.load_tasks()
        tasks = []
        while (len(tasks) < (self.game.tasks_per_person // 3) * 3):
            tasks.append(random.choice(self.easy_tasks))
            tasks.append(random.choice(self.medium_tasks))
            tasks.append(random.choice(self.hard_tasks))
        while (len(tasks) < self.game.tasks_per_person):
            difficulty = random.randint(0, 2)
            if difficulty == 0:
                tasks.append(random.choice(self.easy_tasks))
            elif difficulty == 1:
                tasks.append(random.choice(self.medium_tasks))
            else:
                tasks.append(random.choice(self.hard_tasks))
        return tasks

    @tasks.loop(seconds=1)
    async def timer(self):
        if self.game is not None and self.game.is_ended:
            await self.channel.send("@everyone Game has ended! Please return to the meeting room!")
            self.game = None
            return
        if self.game is None or self.channel is None:
            return
        
        await self.game.decrement_timer(
            lambda: self.channel.send(f"Crewmates have {self.game.timer} seconds left to finish {self.game.remaining_tasks} tasks!"),
            lambda: self.channel.send(f"@everyone The meeting is over! Vote for who you think the imposter is!"),
            lambda: self.channel.send(f"@everyone Crewmates have {self.game.timer}s to finish {self.game.remaining_tasks} tasks!")
        )

    def add_commands(self):
        @self.command(name="new", pass_context=True)
        async def newGame(ctx, *args):
            usage = "Usage: .new <tasks to win> <imposters> <tasks per person = 4> <game length(seconds) = 420> <meeting length(seconds) = 60>"
            if not 2 <= len(args) <= 5:
                await ctx.send(usage)
                return
            tasks_to_win = int(args[0])
            imposter_count = int(args[1])
            tasks_per_person = 4 if len(args) < 3 else int(args[2])
            game_length = 420 if len(args) < 4 else int(args[3])
            meeting_length = 50 if len(args) < 5 else int(args[4])
            self.game = Game(tasks_to_win, imposter_count, tasks_per_person, game_length, meeting_length)
            self.channel = ctx.message.channel
            self.load_tasks()
            
            await ctx.send(f"New game created with {tasks_to_win} tasks to win, {imposter_count} imposters!")

        @self.check_game_existence
        @self.command()
        async def join(ctx):
            self.players.append(ctx.author)
            await ctx.send(f"Added {ctx.author.name} to the game!")

        @self.check_game_existence
        @self.command(name="start", pass_context=True)
        async def startGame(ctx):
            if len(self.players) < self.game.imposter_count:
                await ctx.send(f"We can't start the game yet - {len(self.players)} players have joined, but we need at least {self.game.imposter_count} players to be imposters!")
                return
            imposters = self.game.get_imposters(self.players)
            imposter_names = "\n".join([imposter.name for imposter in imposters])
            for player in self.players:
                role_message = f"You are a crewmate. " if player not in imposters else f"You are an imposter. The imposters this game are: \n\n{imposter_names}"
                tasks = self.get_tasks_for_player()
                task_message = "Your tasks are:\n\n" + "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
                await player.send(role_message + "\n\n" + task_message)

            self.game.start_game()
            await ctx.send(f"Game has started! Crewmates have {self.game.timer}s to finish {self.game.remaining_tasks} tasks!")
        
        @self.check_game_existence
        @self.command()
        async def emergency(ctx):
            self.game.emergency()
            await ctx.send("@everyone Emergency meeting called! Drop what you're doing and go to the meeting room ASAP!")

        @self.check_game_existence
        @self.command(name="meeting", pass_context=True)
        async def start_meeting(ctx):
            self.game.start_meeting()
            await ctx.send(f"@everyone The meeting has started! Crewmates have {self.game.meeting_timer} seconds to discuss!")
        
        @self.check_game_existence
        @self.command(name="meetingdone", pass_context=True)
        async def resume_game(ctx):
            self.game.resume_game()
            await ctx.send(f"@everyone Timer resumed! Crewmates have {self.game.timer} seconds to finish {self.game.remaining_tasks} tasks!")

        @self.check_game_existence
        @self.command(name="task", pass_context=True)
        async def done_task(ctx, *args):
            if len(args) < 1:
                await ctx.send("Write 2-3 sentences about what you did to finish the task!")
                return

            self.game.done_task()
            if self.game.remaining_tasks == 0:
                await ctx.send(f"Crewmates have finished all their tasks!")
            await ctx.send(f"{ctx.author.name} has finished a task! Crewmates have {self.game.remaining_tasks} tasks left to finish!")

        @self.check_game_existence
        @self.command(name="end", pass_context=True)
        async def end_game(ctx):
            self.game.end_game()

        @self.command(name="commands", pass_context=True)
        async def commands(ctx):
            await ctx.send(
                """```\n
                Commands:
                .new -> create a new game
                .join -> join the game
                .start -> start the timer for the game
                .emergency -> call an emergency meeting
                .meeting -> start a meeting(when everyone is in the meeting room)
                .meetingdone -> resume the game after a meeting
                .task -> finish a task
                .end -> end the game
                .help -> show this message
                .rules -> show the rules
                \n```""".replace("    ", "")
            )
        
        @self.command(name="rules", pass_context=True)
        async def rules(ctx):
            await ctx.send(
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


# game data class
# basically, all it stores is the timer data and the current number of tasks done
# model the game of among us as a finite state machine, where the states are:
#   - game not started
#   - game started
#   - emergency called
#   - meeting in progress
#   - game over

class Game:
    def __init__(self, tasks_to_win, imposter_count, tasks_per_person, game_length, meeting_length):
        self.remaining_tasks = tasks_to_win
        self.imposter_count = imposter_count
        self.in_meeting = False
        self.timer_running = False
        self.tasks_per_person = tasks_per_person
        self.timer = game_length
        self.meeting_timer = meeting_length
        self.is_ended = False

    async def decrement_timer(self, tick_callback, meeting_over_callback, game_over_callback):
        if self.timer_running is False:
            return
        if self.in_meeting:
            self.meeting_timer -= 1
            if self.meeting_timer == 0:
                self.end_meeting()
                await meeting_over_callback()
        else:
            self.timer -= 1
            if self.timer == 0:
                self.end_game()
                await game_over_callback()
                return
            if self.timer % 60 == 0 or self.timer < 10:
                await tick_callback()

    
    def get_imposters(self, players):
        return random.sample(players, self.imposter_count)
    
    def emergency(self):
        self.timer_running = False

    def start_meeting(self):
        self.timer_running = True
        self.in_meeting = True
    
    def end_meeting(self):
        self.in_meeting = False
        self.timer_running = False

    def resume_game(self):
        self.timer_running = True

    def start_game(self):
        self.timer_running = True
    
    def end_game(self):
        self.timer_running = False
        self.is_ended = True

    def done_task(self):
        self.remaining_tasks -= 1
        if self.remaining_tasks == 0:
            self.end_game()
            return

bot = MyClient(command_prefix=".", intents=intents)
bot.run(os.getenv("SECRET_TOKEN"))
