import sc2, cv2
import numpy as np
from sc2 import run_game, maps, Race, Difficulty, position, Result
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, \
GATEWAY, CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY, OBSERVER, ROBOTICSFACILITY
HEADLESS = False

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