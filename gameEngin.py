# Some constants you can modify
import pygame
from gameobjects.vector2 import Vector2
from random import randint, choice
from pygame.locals import *

SCREEN_SIZE = (640, 480)
NEST_POSITION = (320, 240)
ANT_COUNT = 20
NEST_SIZE = 100.


class GameEntity(object):
    def __init__(self, world, name, image):
        self.world = world
        self.name = name
        self.image = image
        self.location = Vector2(0, 0)
        self.destination = Vector2(0, 0)
        self.speed = 0.
        self.brain = StateMachine()
        self.id = 0

    def render(self, surface):
        x, y = self.location
        w, h = self.image.get_size()
        surface.blit(self.image, (x-w/2, y-h/2))

    def process(self, time_passed):
        self.brain.think()
        if self.speed > 0 and self.location != self.destination:

            vec_to_destination = self.destination - self.location
            distance_to_destination = vec_to_destination.get_length()
            heading = vec_to_destination.get_normalized()
            travel_distance = min(distance_to_destination,
                                  time_passed * self.speed)
            self.location += travel_distance * heading


# -- world class work for only nest
class World(object):
    def __init__(self):
        self.entities = {}  # Store all the entities
        self.entity_id = 0  # Last entity id assigned
        # Draw the nest (a circle) on the background
        self.background = pygame.surface.Surface(SCREEN_SIZE).convert()
        self.background.fill((255, 255, 255))
        pygame.draw.circle(self.background, (200, 255, 200),
                           NEST_POSITION, int(NEST_SIZE))

    def add_entity(self, entity):
        # Stores the entity then advances the current id
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def remove_entity(self, entity):
        del self.entities[entity.id]

    def get(self, entity_id):
        # Find the entity, given its id (or None if it is not found)
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def process(self, time_passed):
        # Process every entity in the world
        time_passed_seconds = time_passed / 1000.0
        for entity in self.entities.itervalues():
            entity.process(time_passed_seconds)

    def render(self, surface):
        # Draw the background and all the entities
        surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)

    def get_close_entity(self, name, location, range=100.):
        # Find an entity within range of a location
        location = Vector2(*location)
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_distance_to(entity.location)
                if distance < range:
                    return entity
        return None


# # # # # # # # # # ant entity class
class Ant(GameEntity):
    def __init__(self, world, image):
        # Call the base class constructor
        GameEntity.__init__(self, world, "ant", image)
        # Create instances of each of the states
        exploring_state = AntStateExploring(self)
        seeking_state = AntStateSeeking(self)
        delivering_state = AntStateDelivering(self)
        hunting_state = AntpStateHunting(self)
        # Add the states to the state machine (self.brain)
        self.brain.add_state(exploring_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(delivering_state)
        self.brain.add_state(hunting_state)
        self.carry_image = None

    def carry(self, image):
        self.carry_image = image

    def drop(self, surface):
        # Blit the 'carry' image to the background and reset it
        if self.carry_image:
            x, y = self.location
            w, h = self.carry_image.get_size()
            surface.blit(self.carry_image, (x-w, y-h/2))
            self.carry_image = None

    def render(self, surface):
        # Call the render function of the base class
        GameEntity.render(self, surface)
    # Extra code to render the 'carry' image
        if self.carry_image:
            x, y = self.location
            w, h = self.carry_image.get_size()
            surface.blit(self.carry_image, (x-w, y-h/2))

# # # # # # # class for state of ant


class State(object):
    def __init__(self, name):
        self.name = name

    def do_actions(self):
        pass

    def check_conditions(self):
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass

# # # # The State Machine Class


class StateMachine(object):
    def __init__(self):
        self.states = {}  # Stores the states
        self.active_state = None  # The currently active state

    def add_state(self, state):
        # Add a state to the internal dictionary
        self.states[state.name] = state

    def think(self):
        # Only continue if there is an active state
        if self.active_state is None:
            return
        # Perform the actions of the active state, and check conditions
        self.active_state.do_actions()
        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        # Change states and perform any exit / entry actions
        if self.active_state is not None:
            self.active_state.exit_actions()
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()


# # # # # # # # The Exploring State for Ants (AntStateExploring)
class AntStateExploring(State):
    def __init__(self, ant):
        # Call the base class constructor to initialize the State
        State.__init__(self, "exploring")
        # Set the ant that this State will manipulate
        self.ant = ant

    def random_destination(self):
        # Select a point in the screen
        w, h = SCREEN_SIZE
        self.ant.destination = Vector2(randint(0, w), randint(0, h))

    def do_actions(self):
        # Change direction, 1 in 20 calls
        if randint(1, 20) == 1:
            self.random_destination()

    def check_conditions(self):
        # If there is a nearby leaf, switch to seeking state
        leaf = self.ant.world.get_close_entity("leaf", self.ant.location)
        if leaf is not None:
            self.ant.leaf_id = leaf.id
            return "seeking"
        # If there is a nearby spider, switch to hunting state
        spider = self.ant.world.get_close_entity(
            "spider", NEST_POSITION, NEST_SIZE)
        if spider is not None:
            if self.ant.location.get_distance_to(spider.location) < 100.:
                self.ant.spider_id = spider.id
                return "hunting"
        return None

    def entry_actions(self):
        # Start with random speed and heading
        self.ant.speed = 120. + randint(-30, 30)
        self.random_destination()


# Start the game
def run():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    world = World()
    w, h = SCREEN_SIZE
    clock = pygame.time.Clock()
    ant_image = pygame.image.load("ant.png").convert_alpha()
    leaf_image = pygame.image.load("leaf.png").convert_alpha()
    spider_image = pygame.image.load("spider.png").convert_alpha()
    # Add all our ant entities
    for ant_no in range(ANT_COUNT):

        ant = Ant(world, ant_image)
        ant.location = Vector2(randint(0, w), randint(0, h))
        ant.brain.set_state("exploring")
        world.add_entity(ant)
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
        time_passed = clock.tick(30)
        # Add a leaf entity 1 in 20 frames
        if randint(1, 10) == 1:
            leaf = Leaf(world, leaf_image)
            leaf.location = Vector2(randint(0, w), randint(0, h))
            world.add_entity(leaf)
        # Add a spider entity 1 in 100 frames
        if randint(1, 100) == 1:
            spider = Spider(world, spider_image)
            spider.location = Vector2(-50, randint(0, h))
            spider.destination = Vector2(w+50, randint(0, h))
            world.add_entity(spider)
        world.process(time_passed)
        world.render(screen)
        pygame.display.update()


if __name__ == "__main__":
    run()
