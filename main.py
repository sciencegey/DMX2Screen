#   _____    __  __  __   __  ___     _____                                     
#  |  __ \  |  \/  | \ \ / / |__ \   / ____|                                    
#  | |  | | | \  / |  \ V /     ) | | (___     ___   _ __    ___    ___   _ __  
#  | |  | | | |\/| |   > <     / /   \___ \   / __| | '__|  / _ \  / _ \ | '_ \ 
#  | |__| | | |  | |  / . \   / /_   ____) | | (__  | |    |  __/ |  __/ | | | |
#  |_____/  |_|  |_| /_/ \_\ |____| |_____/   \___| |_|     \___|  \___| |_| |_|
# 
# V0.3.0
# 
# Yo! This is a simple Python program that takes DMX data over Artnet and displays it as coloured squares.

# ~~~~How do I use it?~~~~
# Simply define your "lighting fixtures" in the fixtures.json file (filename and path can be set in the config file). The included 
# files gives you an example of how to setup both "sectors" (fixed-size blocks that make it quick and easy to position them) and "blocks" (blocks that can be any size).
# 
# The config.ini file is used to configure the program. An example is included that has all the options avalible. If the setting isn't set, or 
# the file isn't present, it will just use the built-in defaults :)
# 
# You can also use the parameters -C or --config to specify a config location and the parameters -F or --fixture to to specify a fixture file.
# 
# Requires Visual C++ 2015 redistributable (https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist) and 
# the Windows Media Feature Pack (for N and KN versions) (https://support.microsoft.com/en-us/topic/media-feature-pack-list-for-windows-n-editions-c1c6fffa-d052-8338-7a79-a4bb980a700a)
# 
# Once that's all done, just run main.py and watch it go :D
# 
# For more information, check out the Github repository at https://github.com/sciencegey/DMX2Screen

import sys
import json
import numpy as np
import configparser
import os.path
from python_artnet import python_artnet as Artnet

import cv2 as cv

debug = False

configFile = "config.ini"
fixtureFile = "fixtures/template.json"

# Checks to see if a config file has been specified as a command-line argument
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
canvasWidth = 1280
canvasHeight = 720
# and the parameters for the output grid
cellSize = 8
displayType = "sector"

# loads settings from the config file and overwrites the presets (if they're present)
if os.path.isfile(configFile):
    conf = configparser.ConfigParser(inline_comment_prefixes=";")
    conf.read(configFile)
    debug = conf.getboolean("General", "Debug", fallback=debug)
    fixtureFile = conf.get("General", "FixtureFile", fallback=fixtureFile)

    ARTNET_IP = conf.get("Artnet", "IP", fallback=ARTNET_IP)
    ARTNET_PORT = conf.getint("Artnet", "Port", fallback=ARTNET_PORT)
    ARTNET_UNI = conf.getint("Artnet", "Universe", fallback=ARTNET_UNI)

    canvasHeight = conf.getint("Output", "Height", fallback=canvasHeight)
    canvasWidth = conf.getint("Output", "Width", fallback=canvasWidth)
    cellSize = conf.getint("Output", "CellSize", fallback=cellSize)
    displayType = conf.get("Output", "DisplayType", fallback=displayType)


else:
    print("No config.ini file found! Using defaults...")

if debug:
    print(Artnet.version())

# Creates Artnet socket on the selected IP and Port
a = Artnet.Artnet(ARTNET_IP,ARTNET_PORT,DEBUG=debug)

# Checks to see if a fixtures file has been specified as a command-line argument
if "--fixture" in sys.argv:
    i = sys.argv.index("--fixture") + 1
    fixtureFile = sys.argv[i]
elif "-F" in sys.argv:
    i = sys.argv.index("-F") + 1
    fixtureFile = sys.argv[i]

#import and load fixtures JSON file
if os.path.isfile(fixtureFile):
    f = open(fixtureFile, "r")
    fixtures = json.load(f)
else:
    # unless it doesn't exist, then quit the program.
    print("Oops! The fixtures file wasn't found! Check the config.ini to make sure the path is defined correctly!")
    input("Press any key to exit...")
    sys.exit()

# get the grid type from the fixtures file
gridType = list(fixtures.keys())

# creates a blank (black) screen to start off with (is a 4 "wide" array; Red, Green, Blue and Alpha (required for NDI))
screenOutput = np.zeros((canvasHeight,canvasWidth,4), np.uint8)

# creates the window for the output
cv.namedWindow('DMXOutput', cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)

if displayType.lower() == "ndi":
    import NDIlib as ndi

    send_settings = ndi.SendCreate()
    send_settings.ndi_name = 'DMX2Screen'
    ndi_send = ndi.send_create(send_settings)
    video_frame = ndi.VideoFrameV2()

    windowWidth = 640
    windowHeight = 360

elif displayType.lower() == "opencv":
    windowWidth = canvasWidth
    windowHeight = canvasHeight

else:
    # unless it doesn't exist, then quit the program.
    print("Oops! No output specified! Check the config.ini to make sure the output type is defined correctly!")
    input("Press any key to exit...")
    sys.exit()

# shows the output (in this case blank)
cv.imshow('DMXOutput', screenOutput)
cv.resizeWindow('DMXOutput', windowWidth, windowHeight)
cv.waitKey(1)

while cv.getWindowProperty('DMXOutput', cv.WND_PROP_VISIBLE) > 0:
    # runs infinitaly while the opencv window is open (until it either gets closed or crashes or ctrl-c'd)
    try:
        # First get the latest Art-Net data 
        artNetBuffer = a.readBuffer()
        # And make sure we actually got something
        if artNetBuffer is not None:
            # For each grid type
            for g in range(len(gridType)):
                # For each fixture in the sectors section
                if gridType[g].lower() == "sectors":
                    for i in range(len(fixtures["sectors"])):
                        # Gets the sector x and y "position" and converts it to the real x and y position (times by cellSize)
                        x = cellSize*(fixtures["sectors"][i]["x"])
                        y = cellSize*(fixtures["sectors"][i]["y"])

                        # And gets the DMX channels for that sector
                        channels = fixtures["sectors"][i]["dmxChannels"]

                        # If a universe is defined, use that, otherwise use the default
                        if "universe" in fixtures["sectors"][i]:
                            universe = fixtures["sectors"][i]["universe"]
                        else:
                            universe = ARTNET_UNI

                        # Make sure the packet has some data
                        if artNetBuffer[universe].data is not None:
                            # Stores the packet data array
                            dmx = artNetBuffer[universe].data

                            # Then takes all that data and puts it out to the screen :)
                            # Each sector starts at y (defined above) and goes to y plus cell size. Same with x. Basically created one large pixel of a fixed size.
                            # 
                            # Then gets the DMX data from each channel defined in the fixtures file, gets it from the Artnet array, then sets each colour of the 
                            # pixel to whatever the data is (DMX is 0-255, directly translated into R G or B which is also 0-255). Also sets the Alpha to 255 (fully opaque).
                            screenOutput[y:y+cellSize, x:x+cellSize] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255
                
                # For each fixture in the absolute section
                elif gridType[g].lower() == "absolute":
                    for i in range(len(fixtures["absolute"])):
                        # Gets the sector x and y "position" and converts it to the real x and y position (times by cellSize)
                        x = fixtures["absolute"][i]["x"]
                        y = fixtures["absolute"][i]["y"]

                        # And gets the DMX channels for that sector
                        channels = fixtures["absolute"][i]["dmxChannels"]

                        # If a universe is defined, use that, otherwise use the default
                        if "universe" in fixtures["absolute"][i]:
                            universe = fixtures["absolute"][i]["universe"]
                        else:
                            universe = ARTNET_UNI

                        # Make sure the packet has some data
                        if artNetBuffer[universe].data is not None:
                            # Stores the packet data array
                            dmx = artNetBuffer[universe].data

                            # Then takes all that data and puts it out to the screen :)
                            # Each sector starts at y (defined above) and goes to y plus cell size. Same with x. Basically created one large pixel of a fixed size.
                            # But this time, the x and y are absolute, so they can be anywhere on the screen
                            # 
                            # Then gets the DMX data from each channel defined in the fixtures file, gets it from the Artnet array, then sets each colour of the 
                            # pixel to whatever the data is (DMX is 0-255, directly translated into R G or B which is also 0-255). Also sets the Alpha to 255 (fully opaque).
                            screenOutput[y:y+cellSize, x:x+cellSize] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255
                
                # For each fixture in the blocks section
                elif gridType[g].lower() == "blocks":
                    for i in range(len(fixtures["blocks"])):
                        # Defines the start pixel of x and y and the end pixels of x and y.
                        xStart = fixtures["blocks"][i]["xStart"]
                        yStart = fixtures["blocks"][i]["yStart"]
                        xWidth = fixtures["blocks"][i]["xWidth"]
                        yWidth = fixtures["blocks"][i]["yWidth"]
                        
                        # And the DMX channels for each block
                        channels = fixtures["blocks"][i]["dmxChannels"]

                        # If a universe is defined, use that, otherwise use the default
                        if "universe" in fixtures["blocks"][i]:
                            universe = fixtures["blocks"][i]["universe"]
                        else:
                            universe = ARTNET_UNI

                        # Make sure the packet has some data
                        if artNetBuffer[universe].data is not None:
                            # Stores the packet data array
                            dmx = artNetBuffer[universe].data
                    
                            # Then takes all that data and puts it out to the screen :)
                            # Each sector starts at yStart (defined above) and goes to yStart plus yWidth. Same with x. Basically created one large pixel of a custom size.
                            # 
                            # Then gets the DMX data from each channel defined in the fixtures file, gets it from the Artnet array, then sets each colour of the 
                            # pixel to whatever the data is (DMX is 0-255, directly translated into R G or B which is also 0-255). Also sets the Alpha to 255 (fully opaque).
                            screenOutput[yStart:yStart+yWidth, xStart:xStart+xWidth] = dmx[channels[2]-1], dmx[channels[1]-1], dmx[channels[0]-1], 255

        # Outputs the screenOutput array to the screen (...output :))
        cv.imshow('DMXOutput', screenOutput)
        # cv.resizeWindow('DMXOutput', windowWidth, windowHeight) if displayType.lower() == "opencv" else None

        if displayType.lower() == "ndi":
            ndiOutput = cv.cvtColor(screenOutput, cv.COLOR_BGR2RGBA)
            video_frame.data = ndiOutput
            video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_RGBX

            ndi.send_send_video_v2(ndi_send, video_frame)
        
        # Then waits a few milliseconds
        cv.waitKey(16)
        
    except KeyboardInterrupt:
        # Break out of the while loop if the KeyboardInterrupt is received
        break

# Cleanup bit at the end :)
# 
# Close the Artnet socket
a.close()
# Get rid of the opencv window objects
cv.destroyAllWindows()
# Close the JSON file
f.close()
# And destroy the NDI object
if displayType.lower() == "ndi":
    ndi.send_destroy(ndi_send)
    ndi.destroy()

# Goodbye forever o/
sys.exit()