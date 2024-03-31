import airsim
import base64, json, math, os, random
import threading, time, sys, requests
import numpy as np
import matplotlib.pyplot as plt
import cv2
import anthropic
import openai
from google.cloud import vision
import scene_setup


objects_dict = {
    "poacher": "African_Poacher_2_WalkwRifle_Anim3_14",
    "rhino": "ANIM_Rhinoceros_IdleGraze_28",
    "hippo": "ANIM_Hippopotamus_Swim_2"
}


class AirSimWrapper:
    def __init__(self):
        self.client = airsim.MultirotorClient()
        self.client.confirmConnection()
        self.client.enableApiControl(True)
        self.client.armDisarm(True)
        scene_setup.setup(self, [0, 0, 1], 5)

    def takeoff(self):
        self.client.takeoffAsync().join()

    def land(self):
        self.client.landAsync().join()

    def get_drone_position(self):
        pose = self.client.simGetVehiclePose()
        return [pose.position.x_val, pose.position.y_val, pose.position.z_val]

    def fly_to(self, point, speed=5):
        self.client.moveToPositionAsync(point[0], point[1], point[2], speed).join()

    def fly_path(self, points):
        airsim_points = []
        for point in points:
            if point[2] > 0:
                airsim_points.append(airsim.Vector3r(point[0], point[1], -point[2]))
            else:
                airsim_points.append(airsim.Vector3r(point[0], point[1], point[2]))
        self.client.moveOnPathAsync(airsim_points, 5, 120, airsim.DrivetrainType.ForwardOnly, airsim.YawMode(False, 0), 20, 1).join()

    def set_yaw(self, yaw):
        self.client.rotateToYawAsync(yaw, 5).join()

    def get_yaw(self):
        orientation_quat = self.client.simGetVehiclePose().orientation
        yaw = airsim.to_eularian_angles(orientation_quat)[2]
        return yaw

    def get_position(self, object_name):
        query_string = objects_dict[object_name] + ".*"
        object_names_ue = []
        while len(object_names_ue) == 0:
            object_names_ue = self.client.simListSceneObjects(query_string)
        pose = self.client.simGetObjectPose(object_names_ue[0])
        return [pose.position.x_val, pose.position.y_val, pose.position.z_val]

    def survey(self, boxsize, stripewidth, altitude, velocity):
        print("arming the drone...")
        self.client.armDisarm(True)

        landed = self.client.getMultirotorState().landed_state
        if landed == airsim.LandedState.Landed:
            print("taking off...")
            self.client.takeoffAsync().join()

        landed = self.client.getMultirotorState().landed_state
        if landed == airsim.LandedState.Landed:
            print("takeoff failed - check Unreal message log for details")
            return
        
        # AirSim uses NED coordinates so negative axis is up.
        origin = self.get_drone_position()
        x = -boxsize
        z = origin[2] - altitude

        print("climbing to altitude: " + str(altitude))
        self.client.moveToPositionAsync(origin[0], origin[1], z, velocity).join()

        print("flying to first corner of survey box")
        self.client.moveToPositionAsync(origin[0] + x, origin[1] - boxsize, z, velocity).join()
        
        # let it settle there a bit.
        self.client.hoverAsync().join()
        time.sleep(2)

        # after hovering we need to re-enabled api control for next leg of the trip
        self.client.enableApiControl(True)

        # now compute the survey path required to fill the box 
        path = []
        distance = 0
        while x < boxsize:
            distance += boxsize 
            path.append(airsim.Vector3r(origin[0] + x, origin[1] + boxsize, z))
            x += stripewidth            
            distance += stripewidth 
            path.append(airsim.Vector3r(origin[0] + x, origin[1] + boxsize, z))
            distance += boxsize 
            path.append(airsim.Vector3r(origin[0] + x, origin[1] - boxsize, z)) 
            x += stripewidth  
            distance += stripewidth 
            path.append(airsim.Vector3r(origin[0] + x, origin[1] - boxsize, z))
            distance += boxsize
        
        print("starting survey, estimated distance is " + str(distance))
        trip_time = distance / velocity
        print("estimated survey time is " + str(trip_time))
        try:
            result = self.client.moveOnPathAsync(path, velocity, trip_time, airsim.DrivetrainType.ForwardOnly, 
                airsim.YawMode(False,0), velocity + (velocity/2), 1).join()
        except:
            errorType, value, traceback = sys.exc_info()
            print("moveOnPath threw exception: " + str(value))
            pass

        print("flying back home")
        self.client.moveToPositionAsync(origin[0], origin[1], z, velocity).join()
        
        if z < -5:
            print("descending")
            self.client.moveToPositionAsync(origin[0], origin[1], -5, 2).join()

        print("landing...")
        self.client.landAsync().join()

        print("disarming.")
        self.client.armDisarm(False)

    @staticmethod
    def is_within_boundary(start_pos, current_pos, limit_radius):
        """Check if the drone is within the spherical boundary"""
        distance = math.sqrt(
            (current_pos.x_val - start_pos.x_val) ** 2
            + (current_pos.y_val - start_pos.y_val) ** 2
            + (current_pos.z_val - start_pos.z_val) ** 2
        )
        return distance <= limit_radius

    def flutter(self, speed=5, change_interval=1, limit_radius=10):
        """Simulate Brownian motion /fluttering with the drone"""
        # Takeoff and get initial position
        self.client.takeoffAsync().join()
        start_position = self.client.simGetVehiclePose().position

        while not self.stop_thread:
            pitch = random.uniform(-1, 1) 
            roll = random.uniform(-1, 1)
            yaw = random.uniform(-1, 1)

            self.client.moveByRollPitchYawrateThrottleAsync(
                roll, pitch, yaw, 0.5, change_interval
            ).join()

            current_position = self.client.simGetVehiclePose().position

            if not self.is_within_boundary(
                start_position, current_position, limit_radius
            ):
                self.client.moveToPositionAsync(
                    start_position.x_val,
                    start_position.y_val,
                    start_position.z_val,
                    speed,
                ).join()

            time.sleep(change_interval)

    def start_fluttering(self, speed=5, change_interval=1, limit_radius=10):
        self.stop_thread = False
        self.flutter_thread = threading.Thread(
            target=self.flutter, args=(speed, change_interval, limit_radius)
        )
        self.flutter_thread.start()

    def stop_fluttering(self):
        self.stop_thread = True
        if self.flutter_thread is not None:
            self.flutter_thread.join()

    def generate_circular_path(self, center, radius, height, segments=12):
        path = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            z = height
            path.append(x, y, z)
        return path

    def take_photo(self, filename="image.png", image_type=airsim.ImageType.Scene, display=False):
        if display:
            responses = self.client.simGetImages([
                airsim.ImageRequest("1", airsim.ImageType.Scene, False, False),
                airsim.ImageRequest("1", airsim.ImageType.Infrared, False, False),
                airsim.ImageRequest("1", airsim.ImageType.Segmentation, False, False)])
            
            fig, axs = plt.subplots(len(responses), 1, figsize=(5, 15))
            for idx, response in enumerate(responses):
                img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
                img_rgb = img1d.reshape(response.height, response.width, 3)
                img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)
                axs[idx].imshow(img_rgb)
                axs[idx].axis('off')
            
            plt.tight_layout()
            plt.show()
            return
        
        responses = self.client.simGetImages(
            [airsim.ImageRequest("0", image_type, False, False)]
        )
        response = responses[0]
        img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
        img_rgb = img1d.reshape(response.height, response.width, 3)
        filename = os.path.normpath(filename + ".png")
        cv2.imwrite(filename, img_rgb)
        with open(filename, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        return base64_image

    def VQA_int(self, question, lower_bound, upper_bound):
        prompt = f"This input is part of a production system and immediately cast to an int. Any response to this query must be an integer\
        Otherwise the code will crash. Your response must only contain numbers and must be an integer bounded between {lower_bound} and {upper_bound} inclusive\
        . I stress this again because it is production critical, you must respond with only an integer between {lower_bound} and {upper_bound}, nothing else \
        No comments or acknowledgements, only return an integer so that casting works. Here is the question: "
        return self.VQA(prompt + question)


    def VQA_Claude(self, question, image_type=airsim.ImageType.Scene):
        base64_image = self.take_photo(image_type=image_type)

        with open("config.json", "r") as f:
            config = json.load(f)
        claude_api_key = config["CLAUDE_API_KEY"]
        anthro_client =  anthropic.Anthropic(api_key=claude_api_key)

        message = anthro_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ],
            }
          ],
        )
        # print(message.content[0])
        return message.content[0].text
        
        

    def VQA(self, question, image_type=airsim.ImageType.Scene):
        base64_image = self.take_photo(image_type=image_type)
        with open("config.json", "r") as f:
            config = json.load(f)
        openai.api_key = config["OPENAI_API_KEY"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {config["OPENAI_API_KEY"]}'
            }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": question
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 300
            }
        

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        # print(response.json())
        # print(response.json()["choices"][0]["message"]["content"]) 
        return(response.json()["choices"][0]["message"]["content"])
        # try:
        #     response = openai.Completion.create(
        #         model="gpt-4-vision-preview",  # Placeholder model name, replace with the actual vision model name
        #         prompt=question,
        #         attachments=[{
        #             "data": base64_image,
        #             "type": "image"
        #         }],
        #         formats=["data_to_text"],  # This specifies that the input is data (image) and we expect text output
        #     )
        #     return response['choices'][0]['text']
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        #     return None


    def search(self, object_name):
        arr  = self.get_position(object_name)
        arr2 = self.get_drone_position()
        self.fly_to([0.9 * arr[0] + 0.1 * arr2[0], 0.9 * arr[1] + 0.1 * arr2[1], min(arr[2], -10)])

    def get_latitude_longitude(self, object_name):
        self.fly_to(self.get_position(object_name))
        return (
            self.get_position(object_name)[0],
            self.get_drone_position(object_name)[1],
        )
    

    def patrol_and_report_fixed(self):
        hazards_list = "poachers, unattended fires, traps, illegal logging activities, people"
        prompt = f"You will be given a thermal segmented image, which highly contrasting colours. Here are a list of hazards: [{hazards_list}]. Identify if \
                   there are any hazards by the shapes of objects. Please provide a comma separated list of hazards in the image, or respond None if there are none"
        response = self.VQA(prompt, image_type=airsim.ImageType.Segmentation)
        print(response)

        if any(hazard in response.lower() for hazard in hazards_list.split(', ')):
            # Move towards the identified threat
            self.client.moveByVelocityBodyFrameAsync(5, 0, 0, 1)

            # Query for a detailed report if a hazard is detected
            detailed_prompt = f"We have been contracted by the natural wildlife reserve and animal sanctuary to report on the following thermal segmented image taken at daytime. This image has {response}, which are known hazards and marked in green. Write a brief report on the image to help save the animals."
                        
            #"You are a professional threat assessment provider for environmental purposes. There are the following hazard(s) in this image: {response}. \
            #                  Please provide a report on the identified threat, including its nature, number of entities involved, their actions, and any other relevant details."
            detailed_response = self.VQA_Claude(detailed_prompt, image_type=airsim.ImageType.Segmentation)
            print(f"Threat detected. Detailed report: {detailed_response}")


    def patrol_and_report(self):
        """
        Performs an enhanced patrol operation synchronously, within a box that extends 30 units in each direction from the starting point.
        At each of the 10 sampled points within this box, the drone lowers to a Z altitude of -10 before checking for threats from three different yaw angles.
        """
        
        starting_position = self.get_drone_position()
        hazards_list = "poachers, unattended fires, traps, illegal logging activities, people"
        
        # Define the patrol box area
        box_range = 30

        # Sample 10 points within the box
        patrol_points = [[starting_position[0] + random.uniform(-box_range, box_range), 
                        starting_position[1] + random.uniform(-box_range, box_range), 
                        -5] for _ in range(6)]  # Z set to -10 units for closer inspection

        yaw_angles = [0, 120, 240]  # Yaw angles for comprehensive inspection

        self.takeoff()

        for point in patrol_points:
            drone_pos = self.get_drone_position()
            self.fly_to([drone_pos[0],drone_pos[1],drone_pos[2] - 20])
            self.fly_to(point)
            for yaw in yaw_angles:
                self.set_yaw(yaw)
                # Construct and send the prompt for hazard detection
                prompt = f"You will be given a thermal segmented image, which highly contrasting colours. Here are a list of hazards: [{hazards_list}]. Identify if \
                           there are any hazards by the shapes of objects. Please provide a comma separated list of hazards in the image, or respond None if there are none"
                response = self.VQA(prompt, image_type=airsim.ImageType.Segmentation)

                if any(hazard in response.lower() for hazard in hazards_list.split(', ')):
                    # Move towards the identified threat
                    self.client.moveByVelocityBodyFrameAsync(5, 0, 0, 1)

                    # Query for a detailed report if a hazard is detected
                    detailed_prompt = f"We have been contracted by the natural wildlife reserve and animal sanctuary to report on the following thermal segmented image taken at daytime. This image has {response}, which are known hazards and marked in green. Write a brief report on the image to help save the animals."
                                
                    #"You are a professional threat assessment provider for environmental purposes. There are the following hazard(s) in this image: {response}. \
                    #                  Please provide a report on the identified threat, including its nature, number of entities involved, their actions, and any other relevant details."
                    detailed_response = self.VQA_Claude(detailed_prompt, image_type=airsim.ImageType.Segmentation)
                    print(f"Threat detected. Detailed report: {detailed_response}")
                    break
                else:
                    # This else belongs to the for-loop, executed only if no break occurs (no threat detected at any yaw angle)
                    print("No threats detected at the current point.")
        