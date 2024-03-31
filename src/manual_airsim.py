from airsim_wrapper import *
import os, tempfile, cv2, time
import create_ir_segmentation_map
import capture_ir_segmentation
import scene_setup
import external_camera

print(f"Initializing AirSim...")
aw = AirSimWrapper()
print(aw.client.simListAssets())
print(f"Done.")
print(aw.get_drone_position())
print(aw.get_yaw())
time.sleep(2)
aw.takeoff()
print(f"Done!")
scene_setup.setup(aw)

move_commands = ['fly', 'move', 'm']
up_commands = ['up', 'u']
down_commands = ['down', 'd']
left_commands = ['left', 'l']
right_commands = ['right', 'r']
forward_commands = ['forward', 'f']
backward_commands = ['backward', 'back', 'b']
turn_commands = ['turn', 't', 'yaw']
picture_commands = ['picture', 'take', 'image']
external_picture_commands = ['external', 'fixed']
infrared_commands = ['infrared', 'ir']
survey_commands = ['survey', 'patrol']
scene_commands = ['scene', 'setup']

while True:
    command = input("Enter Command >>> ").split()
    op = command[0]
    if op == "exit":
        break
    elif op == "exec":
        code = input("Enter code >>> ")
        if code[-1] != ";":
            print("Invalid code")
            continue
        code = code.split(";")[0]
        if not code.startswith("aw.client."):
            print("Invalid code")
            continue
        exec(code)
    elif op in scene_commands:
        scene_setup.setup(aw)
    elif op in external_picture_commands:
        external_camera.external_capture(aw)
    elif op in turn_commands:
        deg = float(command[1])
        aw.set_yaw((aw.get_yaw() + deg) % 360)
    elif op in picture_commands:
        responses = aw.client.simGetImages([
            airsim.ImageRequest("1", airsim.ImageType.DepthVis),
            airsim.ImageRequest("1", airsim.ImageType.DepthPerspective),
            airsim.ImageRequest("1", airsim.ImageType.Segmentation),
            airsim.ImageRequest("1", airsim.ImageType.Scene),
            airsim.ImageRequest("1", airsim.ImageType.DisparityNormalized),
            airsim.ImageRequest("1", airsim.ImageType.SurfaceNormals),
            airsim.ImageRequest("1", airsim.ImageType.Infrared)])
        print('Retrieved images: %d' % len(responses))

        tmp_dir = "../drone_images"
        print ("Saving images to %s" % tmp_dir)
        try:
            os.makedirs(tmp_dir)
        except OSError:
            if not os.path.isdir(tmp_dir):
                raise

        for idx, response in enumerate(responses):
            filename = os.path.join(tmp_dir, str(idx))
            if response.pixels_as_float:
                print("Type %d, size %d" % (response.image_type, len(response.image_data_float)))
                airsim.write_pfm(os.path.normpath(filename + '.pfm'), airsim.get_pfm_array(response))
            elif response.compress: #png format
                print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
                airsim.write_file(os.path.normpath(filename + '.png'), response.image_data_uint8)
            else: #uncompressed array
                print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
                img1d = np.fromstring(response.image_data_uint8, dtype=np.uint8)
                img_rgb = img1d.reshape(response.height, response.width, 3)
                cv2.imwrite(os.path.normpath(filename + '.png'), img_rgb)
    elif op in infrared_commands:
        create_ir_segmentation_map.main(aw)
        responses = \
            aw.client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Infrared, False, False),
                                    airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
                                    airsim.ImageRequest("0", airsim.ImageType.Segmentation, False, False)])

        # Change images into numpy arrays.
        img1d = np.fromstring(responses[0].image_data_uint8, dtype=np.uint8)
        im = img1d.reshape(responses[0].height, responses[0].width, 3) 

        img1dscene = np.fromstring(responses[1].image_data_uint8, dtype=np.uint8)
        imScene = img1dscene.reshape(responses[1].height, responses[1].width, 3)

        ir = im[:,:,:3]
        scene = imScene[:,:,:3]
        thermal_image = cv2.applyColorMap(ir, cv2.COLORMAP_JET)

        num = 1
        cv2.imwrite('../airsim_drone/ir_'+str(num)+'.png', ir)
        cv2.imwrite('../airsim_drone/thermal_'+str(num)+'.png', thermal_image)
        cv2.imwrite('../airsim_drone/scene_'+str(num)+'.png', scene)
    elif op in survey_commands:
        boxsize, stripewidth, altitude, velocity = map(float, command[1:])
        aw.survey(boxsize, stripewidth, altitude, velocity)
    else:
        pos = list(map(float, command[1:]))
        speed = pos[-1]
        disp = [0, 0, 0]
        if op in move_commands:
            disp = pos[0:3]
        elif op in up_commands:
            disp[2] = pos[0]
        elif op in down_commands:
            disp[2] = -pos[0]
        elif op in right_commands:
            disp[1] = pos[0]
        elif op in left_commands:
            disp[1] = -pos[0]
        elif op in forward_commands:
            disp[0] = pos[0]
        elif op in backward_commands:
            disp[0] = -pos[0]
        else:
            print("Invalid Command")
            continue

        disp[2] *= -1

        print(command, disp)
        print(aw.get_drone_position())
        new_pos = [aw.get_drone_position()[0]+disp[0], aw.get_drone_position()[1]+disp[1], aw.get_drone_position()[2]+disp[2]]
        aw.fly_to(new_pos, speed)
    
    print("Done!")