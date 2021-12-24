import sys
import json
import numpy as np
import cv2 as cv
import artnet_middleware as Artnet
import configparser
import os.path
# import NDIlib as ndi
# import time

debug = False

configFile = "config.ini"
fixtureFile = "fixtures.json"

if "--config" in sys.argv:
    i = sys.argv.index("--config") + 1
    configFile = sys.argv[i]
elif "-C" in sys.argv:
    i = sys.argv.index("-C") + 1
    configFile = sys.argv[i]

# sets the variables for Artnet
ARTNET_IP = "0.0.0.0"
ARTNET_PORT = 6454
ARTNET_UNI = 0

# sets the variables for the output canvas
canvasWidth = 1920
canvasHeight = 1080
# and the parameters for the output grid
cellSize = 15

# loads settings from the config file and overwrites the presets (if they're present)
if os.path.isfile(configFile):
    conf = configparser.ConfigParser()
    conf.read(configFile)
    debug = conf.getboolean("General", "Debug", fallback=debug)
    fixtureFile = conf.get("General", "FixtureFile", fallback=fixtureFile)

    ARTNET_IP = conf.get("Artnet", "IP", fallback=ARTNET_IP)
    ARTNET_PORT = conf.getint("Artnet", "Port", fallback=ARTNET_PORT)
    ARTNET_UNI = conf.getint("Artnet", "Universe", fallback=ARTNET_UNI)

    canvasHeight = conf.getint("Output", "Height", fallback=canvasHeight)
    canvasWidth = conf.getint("Output", "Width", fallback=canvasWidth)
    cellSize = conf.getint("Output", "CellSize", fallback=cellSize)


else:
    print("No config.ini file found! Using defaults...")

# Sets debug in Artnet module. I know it's janky; it works so I don't care ;) 
# (unless YOU know a better way, then please tell me or fix it :])
Artnet.debug = debug

#import and load fixtures JSON file
if os.path.isfile(fixtureFile):
    f = open(fixtureFile, "r")
    fixtures = json.load(f)
else:
    # unless it doesn't exist, then quit the program.
    print("Oops! The fixtures file wasn't found! Check the config.ini to make sure the path is defined correctly!")
    input("Press any key to exit...")
    sys.exit()

# creates a blank (black) screen to start off with (is a 4 "wide" array; Red, Green, Blue and Alpha (required for NDI))
screenOutput = np.zeros((canvasHeight,canvasWidth,4), np.uint8)

# send_settings = ndi.SendCreate()
# send_settings.ndi_name = 'ndi-python'
# ndi_send = ndi.send_create(send_settings)
# video_frame = ndi.VideoFrameV2()

# shows the output (in this case blank)
cv.imshow('DMXOutput', screenOutput)
cv.waitKey(1)

while cv.getWindowProperty('DMXOutput', cv.WND_PROP_VISIBLE) > 0:
    # runs infinitaly while the opencv window is open (until it either gets closed or crashes or ctrl-c'd)
    try:
        # Grabs the Artnet packet then checks to see if something is in it (otherwise, don't do anything and keep showing the last screen)
        artNetPacket = Artnet.readPacket(ARTNET_IP,ARTNET_PORT)
        if artNetPacket is not None:
            # Checks to see if the current packet is for the specified DMX Universe
            if artNetPacket.universe == ARTNET_UNI:
                # Stores the packet data array
                dmx = artNetPacket.data
                
                # For each fixture in the sectors section
                for i in range(len(fixtures["sectors"])):
                    # Gets the sector x and y "position" and converts it to the real x and y position (times by cellSize)
                    x = cellSize*(fixtures["sectors"][i]["x"])
                    y = cellSize*(fixtures["sectors"][i]["y"])
                    # And gets the DMX channels for that sector
                    channels = fixtures["sectors"][i]["dmxChannels"]

                    # Then takes all that data and puts it out to the screen :)
                    # Each sector starts at y (defined above) and goes to y plus cell size. Same with x. Basically created one large pixel of a fixed size.
                    # 
                    # Then gets the DMX data from each channel defined in the fixtures file, gets it from the Artnet array, then sets each colour of the 
                    # pixel to whatever the data is (DMX is 0-255, directly translated into R G or B which is also 0-255). Also sets the Alpha to 255 (fully opaque).
                    screenOutput[y:y+cellSize, x:x+cellSize] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255
                
                # # For each fixture in the blocks section
                # for i in range(len(fixtures["blocks"])):
                #     # Defines the start pixel of x and y and the end pixels of x and y.
                #     xStart = fixtures["blocks"][i]["xStart"]
                #     yStart = fixtures["blocks"][i]["yStart"]
                #     xWidth = fixtures["blocks"][i]["xWidth"]
                #     yWidth = fixtures["blocks"][i]["yWidth"]
                #     # And the DMX channels for each block
                #     channels = fixtures["blocks"][i]["dmxChannels"]
                #
                #     # Then takes all that data and puts it out to the screen :)
                #     # Each sector starts at yStart (defined above) and goes to yStart plus yWidth. Same with x. Basically created one large pixel of a custom size.
                #     # 
                #     # Then gets the DMX data from each channel defined in the fixtures file, gets it from the Artnet array, then sets each colour of the 
                #     # pixel to whatever the data is (DMX is 0-255, directly translated into R G or B which is also 0-255). Also sets the Alpha to 255 (fully opaque).
                #     screenOutput[yStart:yStart+yWidth, xStart:xStart+xWidth] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255

        # Outputs the screenOutput array to the screen (...output :))
        cv.imshow('DMXOutput', screenOutput)
        # Then waits a single millisecond
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
        # Break out of the while loop if the KeyboardInterrupt is received
        break

# Cleanup bit at the end :)
# 
# Get rid of the opencv window objects
cv.destroyAllWindows()
# Close the JSON file
f.close()
# And destroy the NDI object
# ndi.send_destroy(ndi_send)
# ndi.destroy()

# Goodbye forever o/
sys.exit()