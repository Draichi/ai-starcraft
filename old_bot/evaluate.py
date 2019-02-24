import sc2, random, cv2, time, os, colorama, keras
import numpy as np
from termcolor import *
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.player import Bot, Computer
from src.ai_functions import build_workers, build_pylons, build_assimilators, expand, \
offensive_force_building, offensive_force_itself, attack, scout
from src.cv2_functions import intel

os.environ["SC2PATH"] = 'E:\Program Files\StarCraft II'
colorama.init()

MODEL_PATH = 'models/convnet-30-epochs-0.0001-LR-stage1'

class Ai(sc2.BotAI):
    def __init__(self, use_model=False):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 50
        self.do_something_after = 0
        self.train_data = []
        self.use_model = use_model
        if self.use_model:
            cprint('> Using model: {}'.format(MODEL_PATH), 'green')
            self.model = keras.models.load_model(MODEL_PATH)

    async def on_step(self, iteration):
        self.iteration = iteration
        await scout(self)
        await self.distribute_workers() #built-in method
        await build_workers(self)
        await build_pylons(self)
        await build_assimilators(self)
        await expand(self)
        await offensive_force_building(self)
        await offensive_force_itself(self)
        await intel(self)
        await attack(self)

    def on_end(self, game_result):
        cprint('DEBUG: --- on_end called ---', 'yellow')
        cprint('Game {}'.format(str(game_result)), 'green')

        if game_result == Result.Victory:
            cprint('> Saving this game data on: train_data/{}.npy'.format(str(int(time.time()))), 'green')
            np.save("train_data/{}.npy".format(str(int(time.time()))), np.array(self.train_data))

run_game(
    maps.get("AbyssalReefLE"),
    [
        Bot(Race.Protoss, Ai(use_model=True)),
        Computer(Race.Terran, Difficulty.Hard)
    ],
    realtime=False    
)