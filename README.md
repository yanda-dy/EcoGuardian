# EcoGuardian: LLM-Powered Wildlife Preservation Drones

## Setup (Windows only)
1. Install [Unreal Engine](https://www.unrealengine.com/en-US) and build [AirSim](https://microsoft.github.io/AirSim/build_windows).
2. Setup the [conda](https://www.anaconda.com/) environment with
```
conda env create -f environment.yml
conda activate ecoguardian
```
3. Get API keys for [OpenAI](https://openai.com/blog/openai-api) and/or [Claude](https://docs.anthropic.com/claude/reference/getting-started-with-the-api).
4. Download the AirSim zip file from [Releases](https://github.com/yanda-dy/EcoGuardian/releases), and unzip the package.

## Running
1. Run the AirSim simulation as `./run.bat` from the unzipped folder.
2. Run `python chatgpt_airsim.py` or `python manual_airsim.py` from the conda environment.