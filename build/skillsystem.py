import pygame

class Skill:
    def __init__(self, image, callback, active=False, cost=0):
        self.image = image
        self.callback = callback
        self.active = active
        self.cost = cost

class Skill_System:
    def __init__(self, pos, leaf_skills=None, stem_skills=None, root_skills=None, starch_skills=None):
        self.pos = pos
        self.leaf_skills = leaf_skills
        self.stem_skills = stem_skills
        self.root_skills = root_skills
        self.starch_skills = starch_skills

