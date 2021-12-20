import sys
import json
import numpy as np
import cv2 as cv
import artnet_middleware as Artnet
# import NDIlib as ndi
# import time

#import and load fixtures JSON file
f = open("fixtures.json", "r")
fixtures = json.load(f)

# sets the variables for Artnet
ARTNET_IP = "192.168.1.21"
ARTNET_PORT = 6454
ARTNET_UNI = 0

# sets the variables for the output canvas
canvasHeight = 1080
canvasWidth = 1920
# and the parameters for the output grid
cellSize = 15

# creates a blank (black) screen to start off with
screenOutput = np.zeros((canvasHeight,canvasWidth,4), np.uint8)

# send_settings = ndi.SendCreate()
# send_settings.ndi_name = 'ndi-python'
# ndi_send = ndi.send_create(send_settings)
# video_frame = ndi.VideoFrameV2()

# shows the output (in this case blank)
cv.imshow('DMXOutput',cv.resize(screenOutput,(1280,720)))

while cv.getWindowProperty('DMXOutput', 0) >= 0:
    try:
        artNetPacket = Artnet.readPacket(ARTNET_IP,ARTNET_PORT)
        if artNetPacket is not None:
            if artNetPacket.universe == ARTNET_UNI:
                dmx = artNetPacket.data
                #print(packet.data[0])
                # screenOutput[:,0:canvasWidth//2] = (255,0,0)
                # screenOutput[:,canvasWidth//2:canvasWidth] = (0,255,0)
                
                for i in range(len(fixtures["sectors"])):
                    x = 15*(fixtures["sectors"][i]["x"])
                    y = 15*(fixtures["sectors"][i]["y"])
                    channels = fixtures["sectors"][i]["dmxChannels"]

                    screenOutput[y:y+15, x:x+15] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255

                # for i in range(len(fixtures["blocks"])):
                #     xStart = fixtures["blocks"][i]["xStart"]
                #     yStart = fixtures["blocks"][i]["yStart"]
                #     xWidth = fixtures["blocks"][i]["xWidth"]
                #     yWidth = fixtures["blocks"][i]["yWidth"]
                #     channels = fixtures["blocks"][i]["dmxChannels"]

                #     screenOutput[yStart:yStart+yWidth, xStart:xStart+xWidth] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1]

            cv.imshow('DMXOutput',cv.resize(screenOutput,(1280,720)))
            cv.waitKey(1)

            # screenOutput = cv.cvtColor(screenOutput, cv.COLOR_BGR2RGBA)
            # video_frame.data = screenOutput
            # video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_RGBX

            # ndi.send_send_video_v2(ndi_send, video_frame)

            # start = time.time()
            # while time.time() - start < 60 * 5:
            #     start_send = time.time()

            #     for _ in reversed(range(200)):
            #         ndi.send_send_video_v2(ndi_send, video_frame)

            #     print('200 frames sent, at %1.2ffps' % (200.0 / (time.time() - start_send)))
        
    except KeyboardInterrupt:
        break

cv.destroyAllWindows()
f.close()
#ndi.send_destroy(ndi_send)
#ndi.destroy()

sys.exit()