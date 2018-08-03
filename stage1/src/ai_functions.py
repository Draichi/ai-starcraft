import sc2, random, cv2, time, os, keras, colorama
import numpy as np
from termcolor import *
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, \
GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, OBSERVER, ROBOTICSFACILITY

async def build_workers(self):
        if len(self.units(NEXUS))*16 > len(self.units(PROBE)):
            if len(self.units(PROBE)) < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:
                    if self.can_afford(PROBE):
                        print('> Traning probe')
                        await self.do(nexus.train(PROBE))