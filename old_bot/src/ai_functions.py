import sc2, random, cv2, time, colorama
import numpy as np
from termcolor import *
from sc2 import position
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, \
GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, OBSERVER, ROBOTICSFACILITY

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
            move_to = random_location_variance(self, enemy_location)
            cprint('> Scounting', 'green')
            await self.do(scout.move(move_to))
    else:
        for rf in self.units(ROBOTICSFACILITY).ready.noqueue:
            if self.can_afford(OBSERVER) and self.supply_left > 0:
                print('> Training observer')
                await self.do(rf.train(OBSERVER))

# def find_target(self, state):
#     print('> Finding targets')
#     if len(self.known_enemy_units) > 0:
#         return random.choice(self.known_enemy_units)
#     elif len(self.known_enemy_structures) > 0:
#         return random.choice(self.known_enemy_structures)
#     else:
#         return self.enemy_start_locations[0]

async def build_workers(self):
        if len(self.units(NEXUS))*16 > len(self.units(PROBE)):
            if len(self.units(PROBE)) < self.MAX_WORKERS:
                for nexus in self.units(NEXUS).ready.noqueue:
                    if self.can_afford(PROBE):
                        print('> Traning probe')
                        await self.do(nexus.train(PROBE))

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

async def attack(self):
        if len(self.units(VOIDRAY).idle) > 6:
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