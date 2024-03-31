# EcoGuardian: Monitor endangered wildlife and assess potential threats using autonomous drones

## Inspiration

Poaching is the greatest current threat to tigers, rhinos, elephants, gorillas and other African and Asian species. This is a problem that typically goes unnoticed because few countries provide statistics related to poaching. Specifically, from 2022 to 2023, rhino fatalities from poaching in South Africa increased by over 10%. While helicopters and night vision equipment are being used in South Africa's Kruger National Park to successfully decrease poaching, activity is just being pushed to other provinces. Likewise, an estimated 2 anti-poaching rangers are killed each week, but that number could be higher.

This calls for a solution that can successfully deter poachers from more areas and make situations safer for anti-poachers with surveillance: EcoGuardian. 

## What it does

We have built software for autonomous drones that can be controlled with natural language for:

1. Autonomous patrols of endangered species
  - Using thermal imaging cameras, our autonomous drones can patrol large swaths of land at any time of day. Open-ended CV will identify and monitor species that are endangered or at risk of poaching.
2. Detecting poachers and notifying law enforcement
  - When a drone detects potential poachers, it notifies nearby rangers or law enforcement with critical textual and visual data, enabling rapid, effective responses.
3. High-level reasoning
  - By leveraging LLMs, our drones assess the environment for any potential hazards such as poachers or fire precursors. They can also understand and execute complex instructions, even from untrained operators.

## How we built it

We use AirSim, a drone simulator built on the Unreal Engine and we add MLLM integration with GPT-4 and Claude-Opus to interpret natural language instructions and call functions to control the drone. Through a custom programming sandbox, we create an environment that maximizes the reasoning capabilities of modern LLM agents to control a drone and yet still avoid any dangerous activity. With lightweight computation powering real-time decision making and long-term planning, we minimize the need of any human operator and make each drone operator 50x more powerful.

## Challenges we ran into

AirSim has been deprecated for over 2 years, so we ran into some issues with building it on macOS. Thankfully, we had some Windows laptops to run it on. We also ran into some issues with accuracy of computer vision models in the Unreal Engine environments but we were able to use the GPT-4 API instead to significantly improve performance.

## Accomplishments that we're proud of
Two of the biggest milestones were setting up natural language control systems and getting the infrared detector to identify humans (poachers) much better than the human eye.

## What we learned

It is incredible getting to watch LLMs to reason through codes and interact with each other. Having an LLM reason through the code and interact with another LLM that answers questions for it was an aha moment for getting better results for reasoning about scenes.

## What's next for EcoGuardian

Next steps are to test this software in the field and add stronger collision detection to improve drone routes. AirSim software is easily transferable to be run on real drones. Our simulation is in Africa and focused on rhinos, but this software can be extended to protecting endangered species from poachers in any country.

This software can also be extended to enable faster responses to disaster scenarios like earthquakes, falling bridges, floods, and/or wildfires. Specifically, EcoGuardian can be deployed quicker than humans and detect missing people with its infrared cameras.
