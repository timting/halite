"""
Welcome to your first Halite-II bot!

Changes from previous: Rank planets by closest dockable, and try to
dock to the closest dockable planet first
This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
import numpy as np
import time

MAX_DOCKING_SLOTS = 6

def populate_planet_grid(game_map):
    width = int(np.ceil(game_map.width / 15))
    height = int(np.ceil(game_map.height / 15))

    planet_grid = [[[] for j in range(width)] for i in range(height)]

    for planet in game_map.all_planets():
        coords = []
        x = int(np.ceil((planet.x - planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y - planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x - planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y + planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x + planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y - planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x + planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y + planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x + planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x - planet.radius) / 15)) - 1
        y = int(np.ceil((planet.y) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x) / 15)) - 1
        y = int(np.ceil((planet.y + planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x) / 15)) - 1
        y = int(np.ceil((planet.y - planet.radius) / 15)) - 1
        coords.append((y, x))
        x = int(np.ceil((planet.x) / 15)) - 1
        y = int(np.ceil((planet.y) / 15)) - 1
        coords.append((y, x))

        coords = set(coords)

        for coord in coords:
            planet_grid[coord[0]][coord[1]].append(planet)

    # logging.info(planet_grid)
    return planet_grid

# Planet intrinsic value (max 3) = docking slots (max 2) + distance from edge (max 0.5)
# 0 if owned and full
# -1 if enemy
def calculate_planet_intrinsic_value(game_map):
    max_distance_from_edge = ((game_map.width ** 2 + game_map.height ** 2) ** 0.5) / 2
    return np.array([[planet.id, planet.x, planet.y, planet_value(planet, game_map, max_distance_from_edge)] for planet in game_map.all_planets()])

def planet_value(planet, game_map, max_distance_from_edge):
    intrinsic_value = 2 * (planet.num_docking_spots / MAX_DOCKING_SLOTS) + 0.5 * (1 - distance_from_edge(game_map, planet) / max_distance_from_edge)
    if planet.owner == game_map.get_me() and planet.is_full():
        return 0
    elif planet.owner == None:
        return intrinsic_value
    elif planet.owner != game_map.get_me():
        return intrinsic_value - 1
    else:
        return intrinsic_value


# Planet actual value (max 2.25) = planet intrinsic value (max 2.25) - distance between (max 1.5)
def calculate_planet_actual_value(planet_intrinsic_value, ships):
    ship_locations = np.array([[ship.x, ship.y] for ship in ships])
    logging.info("Ship Locations")
    logging.info(ship_locations)
    max_distance = (game_map.width ** 2 + game_map.height ** 2) ** 0.5
    distances = 2.5 * (((ship_locations[:, 0][np.newaxis] - planet_intrinsic_value[:, 1][np.newaxis].transpose()) ** 2 + (ship_locations[:, 1][np.newaxis] - planet_intrinsic_value[:, 2][np.newaxis].transpose()) ** 2) ** 0.5 / max_distance)
    distances[distances > 0.8] *= 2
    logging.info("Distance Values")
    logging.info(distances)
    planet_actual_values = planet_intrinsic_value[:, 3][np.newaxis].transpose() - distances
    logging.info("Planet Actual Values")
    logging.info(planet_actual_values)
    best_planets = np.argmax(planet_actual_values, axis=0)
    logging.info("Best Planets")
    logging.info(best_planets)
    return best_planets


def distance_from_edge(game_map, planet):
    return min(planet.x, planet.y, game_map.width - planet.x, game_map.height - planet.y)

def closest_dockable_planet(ship, game_map, me):
    shortest_distance = 5000000
    best_planet = None

    # If only one dockable planet left, don't fight over it
    if len(game_map.dockable_planets(me)) == 1:
        return best_planet

    for planet in game_map.dockable_planets(me):
        if planet.has_docking_spots():
            distance = ship.calculate_distance_between(planet)
            if distance < shortest_distance:
                shortest_distance = distance
                best_planet = planet

    return best_planet

def highest_value_enemy_planet(ship, game_map, me):
    shortest_distance = 5000000

    for planet in game_map.competitor_owned_planets(me):
        distance = ship.calculate_distance_between(planet)
        if distance < shortest_distance:
            shortest_distance = distance
            best_planet = planet

    return best_planet

def populate_my_ship_grid(game_map, me):
    width = int(np.ceil(game_map.width / 15))
    height = int(np.ceil(game_map.height / 15))

    ship_grid = [[[] for j in range(width)] for i in range(height)]

    for ship in game_map.get_me().all_ships():
        x = int(np.ceil(ship.x / 15)) - 1
        y = int(np.ceil(ship.y / 15)) - 1

        ship_grid[y][x].append(ship)

    return ship_grid

def populate_enemy_ship_grid(game_map, me):
    width = int(np.ceil(game_map.width / 15))
    height = int(np.ceil(game_map.height / 15))

    ship_grid = [[[] for j in range(width)] for i in range(height)]

    for ship in game_map._all_ships():
        if ship.owner.id == me.id:
            continue

        x = int(np.ceil(ship.x / 15)) - 1
        y = int(np.ceil(ship.y / 15)) - 1

        ship_grid[y][x].append(ship)

    return ship_grid


# GAME START
game = hlt.Game("OneEyev4")
game_map = game.initial_map
planet_grid = populate_planet_grid(game_map)
# Then we print our start message to the logs
logging.info("Starting my OneEyev4 bot!")

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    me = game_map.get_me()

    t0 = time.time()
    my_ship_grid = populate_my_ship_grid(game_map, me)
    enemy_ship_grid = populate_enemy_ship_grid(game_map, me)
    ships = game_map.get_me().all_undocked_ships()
    if len(ships) > 0:
        planet_intrinsic_value = calculate_planet_intrinsic_value(game_map)
        best_planets = calculate_planet_actual_value(planet_intrinsic_value, ships)
    t1 = time.time()

    logging.info("Time to calculate best planets: %f" % (t1 - t0))

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control
    for idx, ship in enumerate(ships):
        planet_id = planet_intrinsic_value[best_planets[idx], 0]
        planet = game_map.get_planet(planet_id)

        if planet.owner == None or (planet.owner.id == me.id and planet.has_docking_spots()):
            # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
            x = int(np.ceil(ship.x / 15)) - 1
            y = int(np.ceil(ship.y / 15)) - 1
            logging.info(len(enemy_ship_grid[y][x]))
            if ship.can_dock(planet) and len(enemy_ship_grid[y][x]) == 0:
                # We add the command by appending it to the command_queue
                command_queue.append(ship.dock(planet))
                commanded = True
            else:
                # If we can't dock, we move towards the closest empty point near this planet (by using closest_point_to)
                # with constant speed. Don't worry about pathfinding for now, as the command will do it for you.
                # We run this navigate command each turn until we arrive to get the latest move.
                # In order to execute faster we also choose to ignore ship collision calculations during navigation.
                # This will mean that you have a higher probability of crashing into ships, but it also means you will
                # make move decisions much quicker. As your skill progresses and your moves turn more optimal you may
                # wish to turn that option off.
                navigate_command = ship.new_navigate(
                    ship.closest_point_to(planet),
                    game_map,
                    int(hlt.constants.MAX_SPEED),
                    my_ship_grid,
                    planet_grid)
                # If the move is possible, add it to the command_queue (if there are too many obstacles on the way
                # or we are trapped (or we reached our destination!), navigate_command will return null;
                # don't fret though, we can run the command again the next turn)
                if navigate_command:
                    command_queue.append(navigate_command)
                    commanded = True
        elif planet.owner != me.id:
            docked_ships = planet.all_docked_ships()
            if len(docked_ships) > 0:
                navigate_command = ship.new_navigate(
                    ship.closest_point_to(docked_ships[0]),
                    game_map,
                    int(hlt.constants.MAX_SPEED),
                    my_ship_grid,
                    planet_grid)

                if navigate_command:
                    command_queue.append(navigate_command)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END