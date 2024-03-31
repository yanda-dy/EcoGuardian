from airsim_wrapper import *
import scene_setup

# Predefined survey scene for demo

print(f"Initializing AirSim...")
aw = AirSimWrapper()
print(f"Done!")

color = [0, 0, 1]
width = 3
scene_setup.setup(aw, color, width)
time.sleep(1)

# Initiate Hover
aw.takeoff()
time.sleep(1)

# Fly to patrol center
aw.fly_to([140, 0, -10], 10)
time.sleep(2)

# Start patrol
aw.survey(101, 20, 15, 20)

# Land
aw.land()
