import sc2, random, cv2, time, os, math
import numpy as np
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, \
GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, OBSERVER, ROBOTICSFACILITY

os.environ["SC2PATH"] = 'E:\Program Files\StarCraft II'

HEADLESS = False

class Ai(sc2.BotAI):
    def __init__(self):
        # self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 50
        self.do_something_after = 0
        self.train_data = []
        self.scouts_and_spots = {} # {unit tag : location}

    def on_end(self, game_result):
        print('--- on_end called ---')
        print(game_result)

        if game_result == Result.Victory:
            np.save("train_data/{}.npy".format(str(int(time.time()))), np.array(self.train_data))

    async def on_step(self, iteration):
        # self.iteration = iteration
        self.time = (self.state.game_loop/22.4) / 60
        await self.build_scout()
        await self.scout()
        await self.distribute_workers() #built-in method
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_building()
        await self.offensive_force_itself()
        await self.intel()
        await self.attack()

    async def build_scout(self): # build a scout for every 3 minutes
        if len(self.units(OBSERVER)) < math.floor(self.time/3):
            for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
                if self.can_afford(OBSERVER) and self.supply_left > 0:
                    await self.do(rf.train(OBSERVER))

    def random_location_variance(self, enemy_start_location):
        # harrison mess
        x = enemy_start_location[0]
        y = enemy_start_location[1]

        x += random.randrange(-5,5)
        y += random.randrange(-5,5)

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
        self.expand_dis_dir = {} # {distance to enemy: expansion location}

        for el in self.expansion_locations:
            distance_to_enemy_start = el.distance_to(self.enemy_start_locations[0])
            self.expand_dis_dir[distance_to_enemy_start] = el
            
        self.ordered_exp_distances = sorted(k for k in self.expand_dis_dir)
        existing_ids = [unit.tag for unit in self.units]
        to_be_removed = []
        for noted_scout in self.scouts_and_spots:
            if noted_scout not in existing_ids:
                to_be_removed.append(noted_scout)

        for scout in to_be_removed:
            del self.scouts_and_spots[scout]

        if len(self.units(ROBOTICSFACILITY).ready) == 0:
            unit_type = PROBE
            unit_limit = 1
        else:
            unit_type = OBSERVER
            unit_limit = 15

        assign_scout = True

        if unit_type == PROBE:
            for unit in self.units(PROBE):
                if unit.tag in self.scouts_and_spots:
                    assign_scout = False

        if assign_scout:
            if len(self.units(unit_type).idle) > 0:
                for obs in self.units(unit_type).idle[:unit_limit]:
                    if obs.tag not in self.scouts_and_spots:
                        for dis in self.ordered_exp_distances:
                            try:
                                location = self.expand_dis_dir[dis] #next(value for key, value in self.expand_dis_dir.items if key == dis)
                                active_locations = [self.scouts_and_spots[k] for k in self.scouts_and_spots]

                                if location not in active_locations:
                                    if unit_type == PROBE:
                                        for unit in self.units(PROBE):
                                            if unit.tag in self.scouts_and_spots:
                                                continue
                                    await self.do(obs.move(location))
                                    self.scouts_and_spots[obs.tag] = location
                                    break
                            except Exception as e:
                                print(str(e))

        for obs in self.units(unit_type):
            if obs.tag in self.scouts_and_spots:
                if obs in [probe for probe in self.units(PROBE)]:
                    await self.do(obs.move(self.random_location_variance(self.scouts_and_spots[obs.tag])))

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
        main_base_names = ['nexus', 'commandcenter', 'hatchery']
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

    async def build_workers(self):
        if len(self.units(NEXUS))*16 > len(self.units(PROBE)):
            if len(self.units(PROBE)) < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:
                    if self.can_afford(PROBE):
                        await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
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
                    await self.do(worker.build(ASSIMILATOR, vaspene))

    async def expand(self):
        if self.units(NEXUS).amount < self.time/2 and self.can_afford(NEXUS):
            await self.expand_now() # built-in method

    async def offensive_force_building(self):
        if self.units(PYLON).ready.exists:
            pyloon = self.units(PYLON).ready.random

            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pyloon)

            elif len(self.units(GATEWAY)) < 1:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pyloon)

            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(ROBOTICSFACILITY)) < 1:
                    if self.can_afford(ROBOTICSFACILITY) and not self.already_pending(ROBOTICSFACILITY):
                        await self.build(ROBOTICSFACILITY, near=pyloon)

                if len(self.units(STARGATE)) < self.time:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        await self.build(STARGATE, near=pyloon)

    async def offensive_force_itself(self):
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        if len(self.units(VOIDRAY).idle) > 0:
            choice = random.randrange(0,4)
            # no attack
            # attack_unit_closest_nexus
            # attack_known_enemy_structures
            # attack_enemy_start
            target = False
            if self.time > self.do_something_after:
                if choice == 0:
                    # no attack
                    wait = random.randrange(7, 100) / 100 # 7% to 100% of a minute
                    self.do_something_after = self.time + wait
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
                print(y)
                self.train_data.append([y, self.flipped])

run_game(
    maps.get("AbyssalReefLE"),
    [
        Bot(Race.Protoss, Ai()),
        Computer(Race.Terran, Difficulty.Easy)
    ],
    realtime=False    
)