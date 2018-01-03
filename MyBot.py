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

def populate_planet_grid(game_map):
    width = int(np.ceil(game_map.width / 15))
    height = int(np.ceil(game_map.height / 15))

    planet_grid = [[[] for j in range(width)] for i in range(height)]

    for planet in game_map.all_planets():
        x = int(np.ceil(planet.x / 15)) - 1
        y = int(np.ceil(planet.y / 15)) - 1

        planet_grid[y][x].append(planet)


    logging.info(planet_grid)

    return planet_grid

def initialize_stuff(game):
    game_map = game.initial_map
    return populate_planet_grid(game_map)

def closest_dockable_planet(ship, game_map, me):
    shortest_distance = 5000000
    best_planet = None
    planets = game_map.all_planets()

    for planet in game_map.dockable_planets(me):
        if planet.has_docking_spots():
            distance = ship.calculate_distance_between(planet)
            if distance < shortest_distance:
                shortest_distance = distance
                best_planet = planet

    return best_planet

def populate_ship_grid(game_map, me):
    width = int(np.ceil(game_map.width / 15))
    height = int(np.ceil(game_map.height / 15))

    ship_grid = [[[] for j in range(width)] for i in range(height)]

    for ship in game_map.get_me().all_ships():
        x = int(np.ceil(ship.x / 15)) - 1
        y = int(np.ceil(ship.y / 15)) - 1

        ship_grid[y][x].append(ship)


    logging.info(ship_grid)

    return ship_grid

# GAME START
game = hlt.Game("OneEyev2")
planet_grid = initialize_stuff(game)

# Then we print our start message to the logs
logging.info("Starting my OneEyev2 bot!")

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    me = game_map.get_me()

    my_ship_grid = populate_ship_grid(game_map, me)

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control
    for ship in game_map.get_me().all_ships():
        commanded = False

        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        planet = closest_dockable_planet(ship, game_map, me)
        logging.info(planet)
        if planet:
            # If we can dock, let's (try to) dock. If two ships try to dock at once, neither will be able to.
            if ship.can_dock(planet):
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

        if commanded == False:
            # If no unowned planets left, try to attack ships on competitor owned planets
            for planet in game_map.competitor_owned_planets(me):
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

                break

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END