import math

outFile = "fixtures/vrsl.json"    # The name and location of the output file
data = ""       # Used to hold the json data
length = 120    # How many columns to generate

channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]  # How many rows per column (and the order from top to bottom)

data += '{\n    "sectors":[\n'  # Start of the json data (Sectors)

# For each column
for u in range(length):
    offset = 13*u   # Multiply u by 13 (DMX channels per column)
    for i in range(len(channels)):
        # For each row
        data += '        {"x":' + str(u) + ","  # x is the current column
        data += '"y":' + str(i) + ","           # y is the current row
        # In this case each pixel is only one DMX channel
        data += '"dmxChannels":[' + str((channels[i]+offset)%512) + "," + str(
            (channels[i]+offset)%512) + "," + str((channels[i]+offset)%512) + "],"
        # if the DMX channel is over 512, it's in the next universe
        data += '"universe":' + str(math.floor((channels[i]+offset)/512)) + "},\n"

data = data[:-2]        # Removes the last comma
data += "\n    ]\n}\n"    # Adds nice formatting :)

# Prints to final output to the screen, and then saves it to a json file
print(data)
with open(outFile, 'w') as f:
    f.write(data)
