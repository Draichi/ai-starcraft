import sc2, random, cv2, time, os, keras, colorama
import numpy as np
from termcolor import *
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, \
GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, OBSERVER, ROBOTICSFACILITY
from src.ai_functions import build_workers

os.environ["SC2PATH"] = 'E:\Program Files\StarCraft II'
colorama.init()

MODEL_PATH = 'models/convnet-30-epochs-0.0001-LR-stage1'
HEADLESS = False

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
        await self.scout()
        await self.distribute_workers() #built-in method
        await build_workers(self)
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_building()
        await self.offensive_force_itself()
        await self.intel()
        await self.attack()

    def random_location_variance(self, enemy_start_location):
        # harrison mess
        x = enemy_start_location[0]
        y = enemy_start_location[1]

        x += ((random.randrange(-20, 20))/100) * enemy_start_location[0]
        y += ((random.randrange(-20, 20))/100) * enemy_start_location[1]

        if x < 0:
            x=0
        if y < 0:
            y=0
        if x > self.game_info.map_size[0]:
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            y = self.game_info.map_size[1]
        
        go_to = position.Point2(position.Pointlike((x,y)))
        return go_to

    async def scout(self):
        if len(self.units(OBSERVER)) > 0:
            scout = self.units(OBSERVER)[0]
            if scout.is_idle:
                enemy_location = self.enemy_start_locations[0]
                move_to = self.random_location_variance(enemy_location)
                cprint('> Scounting', 'green')
                await self.do(scout.move(move_to))
        else:
            for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
                if self.can_afford(OBSERVER) and self.supply_left > 0:
                    print('> Training observer')
                    await self.do(rf.train(OBSERVER))

    async def intel(self):
        game_data = np.zeros(
            (   # flipping the position
                self.game_info.map_size[1],
                self.game_info.map_size[0], 
                3
            ), 
            np.uint8
        )
        draw_dict = {
            # UNIT: [size, (BGR color)]
            NEXUS: [15, (0, 255, 0)],
            PYLON: [3, (20, 235, 0)],
            PROBE: [1, (55, 200, 0)],
            ASSIMILATOR: [2, (55, 200, 0)],
            GATEWAY: [3, (200, 100, 0)],
            CYBERNETICSCORE: [3, (150, 150, 0)],
            STARGATE: [5, (255, 0, 0)],
            ROBOTICSFACILITY: [5, (215, 155, 0)],
            VOIDRAY: [3, (255, 100, 0)],
        }
        for unit_type in draw_dict:
            for unit in self.units(unit_type).ready:
                pos = unit.position
                cv2.circle(
                    game_data, # where we ganna draw
                    (int(pos[0]), int(pos[1])), # where IN game_data we gonna draw
                    draw_dict[unit_type][0], # size
                    draw_dict[unit_type][1], # bgr color
                    -1 # line width
                )

        # harrison mess
        main_base_names = ['nexus', 'supplydepot', 'hatchery']
        for enemy_building in self.known_enemy_structures:
            pos = enemy_building.position
            if enemy_building.name.lower() not in main_base_names:
                cv2.circle(game_data, (int(pos[0]), int(pos[1])),5,(200,50,212),-1)
            if enemy_building.name.lower() in main_base_names: # just diferent colors
                cv2.circle(game_data, (int(pos[0]), int(pos[1])),15,(0,0,255),-1)
        
        for enemy_unit in self.known_enemy_units:
            if not enemy_unit.is_structure:
                worker_names = ['probe', 'scv', 'drone'] # if dat unit is a probe/scv/drone it's a worker
                pos = enemy_unit.position
                if enemy_unit.name.lower() in worker_names:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])),1,(55,0,155),-1)
                else:
                    cv2.circle(game_data, (int(pos[0]), int(pos[1])),3,(50,0,215),-1)
        
        for obs in self.units(OBSERVER).ready:
            pos = obs.position
            cv2.circle(game_data, (int(pos[0]), int(pos[1])),1,(255,255,255),-1)

        line_max = 50
        mineral_ratio = self.minerals / 1500
        if mineral_ratio > 1.0:
            mineral_ratio = 1.0
        
        vespene_ratio = self.vespene / 1500
        if vespene_ratio > 1.0:
            vespene_ratio = 1.0

        population_ratio = self.supply_left / self.supply_cap
        if population_ratio > 1.0:
            population_ratio = 1.0

        plausible_supply = self.supply_cap / 200

        military_weight = len(self.units(VOIDRAY)) / (self.supply_cap - self.supply_left)
        if military_weight > 1.0:
            military_weight = 1.0

        cv2.line(game_data, (0,19), (int(line_max*military_weight), 19), (250, 250, 200), 3)
        cv2.line(game_data, (0,15), (int(line_max*plausible_supply), 15), (220, 200, 200), 3)
        cv2.line(game_data, (0,11), (int(line_max*population_ratio), 11), (150, 150, 150), 3)
        cv2.line(game_data, (0,7), (int(line_max*vespene_ratio), 7), (210, 200, 0), 3)
        cv2.line(game_data, (0,3), (int(line_max*mineral_ratio), 3), (0, 255, 25), 3)
        
        self.flipped = cv2.flip(game_data, 0)

        if not HEADLESS:
            resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)
            cv2.imshow('Intel', resized)
            cv2.waitKey(1)

    

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    print('> Building pylon')
                    await self.build(PYLON, near=nexuses.first)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vaspene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                    print('> Building assimilator')
                    await self.do(worker.build(ASSIMILATOR, vaspene))

    async def expand(self):
        if self.units(NEXUS).amount < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.can_afford(NEXUS):
            cprint('> Expanding', 'green')
            await self.expand_now() # built-in method

    async def offensive_force_building(self):
        if self.units(PYLON).ready.exists:
            pyloon = self.units(PYLON).ready.random

            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    print('> Building cyberneticscore')
                    await self.build(CYBERNETICSCORE, near=pyloon)

            elif len(self.units(GATEWAY)) < 1:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    print('> Building gateway')
                    await self.build(GATEWAY, near=pyloon)

            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(ROBOTICSFACILITY)) < 1:
                    if self.can_afford(ROBOTICSFACILITY) and not self.already_pending(ROBOTICSFACILITY):
                        print('> Building roboticsfacility')
                        await self.build(ROBOTICSFACILITY, near=pyloon)

                if len(self.units(STARGATE)) < (self.iteration / self.ITERATIONS_PER_MINUTE):
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        print('> Building stargate')
                        await self.build(STARGATE, near=pyloon)

    async def offensive_force_itself(self):
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                print('> Training voidray')
                await self.do(sg.train(VOIDRAY))

    def find_target(self, state):
        print('> Finding targets')
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        if len(self.units(VOIDRAY).idle) > 10:
            target = False
            if self.iteration > self.do_something_after:
                if self.use_model:
                    prediction = self.model.predict([self.flipped.reshape([-1, 176, 200, 3])])
                    choice = np.argmax(prediction[0])
                    choice_dict = {
                        0: "No attack, wait",
                        1: "Attack closest enemy",
                        2: "Attack enemy structure",
                        3: "Attack enemy start"
                    }
                    cprint('> {}'.format(choice_dict[choice]), 'red')
                else:
                    choice = random.randrange(0,4)
                if choice == 0:
                    # no attack
                    wait = random.randrange(20,165)
                    self.do_something_after = self.iteration + wait
                elif choice == 1:
                    # attack_unit_closest_nexus
                    if len(self.known_enemy_units) > 0:
                        target = self.known_enemy_units.closest_to(random.choice(self.units(NEXUS)))
                elif choice == 2:
                    # attack enemy_structures
                    if len(self.known_enemy_structures) > 0:
                        target = random.choice(self.known_enemy_structures)
                elif choice == 3:
                    # attack_enemy_start
                    target = self.enemy_start_locations[0]
                if target:
                    for vr in self.units(VOIDRAY).idle:
                        await self.do(vr.attack(target))

                # [0,1,0,0]
                y = np.zeros(4)
                y[choice] = 1
                # cprint(y, 'cyan')
                self.train_data.append([y, self.flipped])

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