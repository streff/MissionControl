import RPi.GPIO as GPIO
import time
import datetime
import feedparser
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import smbus
import threading
import krpc

#text handlers
def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
	
def split_every(n, s):
    return [ s[i:i+n] for i in xrange(0, len(s), n) ]

def mainMenu():
    global menuIndex1, menuIndex2, menuBounds1, menuBounds2, runmode, menuList, cancelFlag, selectFlag, runMode, draw, font, image
    runmode = 0
    if cancelFlag == 1:
       cancelFlag = 0
    menuList = {0: [vesselInfo,"Vessel Info"], 1:[flightInfo,"Flight info"], 2:[orbInfo, "Orbital Info"], 3:[progList,"Program List"]}
    menuIndex1 = 0
    menuIndex2 = 0
    menuBounds1 = [1,0]
    while selectFlag == 0:
        markery = ((menuIndex1+1) * line_height) + 5
        markerx = 6
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((posx, (0 * line_height)), "Select Application", fill=255)
        for x in range(0,len(menuList)):
            draw.text((posx + 10, ((x+1) * line_height)), menuList[x][1], font=font, fill=255)
        draw.ellipse((markerx,markery,markerx+3, markery+3), fill=255)
        print markerx
        print markery
        disp.image(image)
        disp.display()
        EVENT.wait(1200)
        consume_queue()
        EVENT.clear()

def mcpInterrupt(channel):
    if channel == 24:
        port_capture = bus.read_byte_data(MCP01, 0x10)
    if channel == 25:
        port_capture = bus.read_byte_data(MCP01, 0x11)
    handle_input(channel, port_capture)

def get_bit(x):
    return (x&-x).bit_length()-1

def handle_input(channel, port_capture):
    global port_data_1A
    global port_data_1B
    if channel == 25:
        portDiff = port_capture ^ port_data_1A 
        pinNum = get_bit(portDiff)
        invertedPort = '{:08b}'.format(port_capture)[::-1]
        pinVal = invertedPort[pinNum]
        pinName = "A"+str(pinNum)
        print(pinName)
        print(pinVal)
        instructionQueue.append([pinName,pinVal])
        port_data_1A = port_capture
        EVENT.set()
    if channel == 24:
        portDiff = port_capture ^ port_data_1B
        pinNum = get_bit(portDiff)
        pinVal = bin(port_capture)[pinNum]
        print(pinName)
        print(pinVal)
        instructionQueue.append([pinNum,pinVal])
        port_data_1B = port_capture
        EVENT.set()
    #if channel == INT2A:
        #port_data_2A == port_capture
    #if channel == INT2B:
        #port_data_2A == port_capture

def handle_rotation(channel, rot):
    instructionQueue.append([channel,rot])
    EVENT.set()

def consume_queue():
    while len(instructionQueue) > 0:
      input = instructionQueue.pop(0)
      print("consume queue")
      handle_queue(input)

def handle_queue(input):
    channel = input[0]
    data = input[1]
    input_dispatch = [{22:index1, "A4":index1Select},{22:index1, 17:index2, "A4":getWeather, "A5":cancel},{22:index1, 17:index2, "A4":select, "A5":cancel},{"A5":cancel}]
    if channel in input_dispatch[runmode]:
        f = input_dispatch[runmode].get(channel,"")
        print("handle queue")
        f(data)

def cancel(input):
    global cancelFlag
    if input == "0":
       cancelFlag = 1
	   
def zeroIndex():
    global menuIndex1, menuIndex2
    menuIndex1 = 0
    menuIndex2 = 0

def index1(input):
    global menuIndex1, menuBounds1
    if (menuIndex1 + input) < (menuBounds1[0]) and (menuIndex1 + input) > (menuBounds1[1] - 1):
        menuIndex1 = menuIndex1 + input
    elif menuIndex1 + input < menuBounds1[1]:
        menuIndex1 = menuBounds1[1]
    else:
        menuIndex1 = menuBounds1[0]


def select(input):
    if input == "0":
       global selectFlag
       selectFlag = 1

def index1Select(input):
    if input == "0":
       global menuList, menuIndex1
       f = menuList[menuIndex1][0]
       f()
        
def index2(input):
    global menuIndex2, menuBounds2
    if (menuIndex2 + input) < (menuBounds2[0]) and (menuIndex2 + input) > (menuBounds2[1] - 1):
        menuIndex2 = menuIndex2 + input
    elif menuIndex2 + input < menuBounds2[1]:
        menuIndex2 = menuBounds2[1]
    else:
        menuIndex2 = menuBounds2[0]

def index2Select(input):
    if input == "0":
       global menuList, menuIndex2
       f = menuList[menuIndex2][0]
       f()    

class RotaryEncoder:
    def __init__(self, Enc_A, Enc_B, callback=None):
        self.Enc_A = Enc_A
        self.Enc_B = Enc_B
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.Enc_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.Enc_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.Enc_A, GPIO.FALLING, callback=self.rotation_decode, bouncetime=2)
        self.callback = callback
        return


    def rotation_decode(self, channel):
        GPIO.setmode(GPIO.BCM)
        Switch_A = GPIO.input(self.Enc_A)
        Switch_B = GPIO.input(self.Enc_B)

        if (Switch_A == 0) and (Switch_B == 1) : # A then B ->
            self.callback(channel, 1)
            print "direction -> "
            # wait for B high
            while Switch_B == 1:
                Switch_B = GPIO.input(self.Enc_B)
            # wait for B drop
            while Switch_B == 0:
                Switch_B = GPIO.input(self.Enc_B)
            return

        elif (Switch_A == 0) and (Switch_B == 0): # B then A <-
            self.callback(channel, -1)
            print "direction <- "
             # wait for A drop
            while Switch_A == 0:
                Switch_A = GPIO.input(self.Enc_A)
            return

        else: # reject other combo
            return

def clearScreen():
    disp.clear()
    disp.display()
def telemetrySetup():
#telemetry streams
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')

#init encoder
GPIO.setmode(GPIO.BCM)
left_encoder = RotaryEncoder(22, 23, callback=handle_rotation)
right_encoder = RotaryEncoder(17, 18, callback=handle_rotation)
#init oled
RST = None
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()
clearScreen()
posx = int(2)
font = ImageFont.load_default()
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
line_height = 8

#init mcp23017
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)
MCP01 = 0x20
MCP02 = 0x21
global port_capture
port_capture = None
global port_data_1A
global port_data_1B
global port_data_2A
global port_data_2B
bus = smbus.SMBus(1)
bus.write_byte_data(MCP01, 0x00, 0xFF)
bus.write_byte_data(MCP01, 0x01, 0xFF)
bus.write_byte_data(MCP01, 0x0c, 0xFF)
bus.write_byte_data(MCP01, 0x0d, 0xFF)
bus.write_byte_data(MCP01, 0x04, 0xFF)
bus.write_byte_data(MCP01, 0x05, 0xFF)
bus.write_byte_data(MCP01, 0x0a, 0x5)
bus.write_byte_data(MCP01, 0x0b, 0x5)
port_data_1A = bus.read_byte_data(MCP01, 0x12)
port_data_1B = bus.read_byte_data(MCP01, 0x13)
GPIO.add_event_detect(24, GPIO.FALLING, callback=mcpInterrupt)
GPIO.add_event_detect(25, GPIO.FALLING, callback=mcpInterrupt)

#init menu
global cancelFlag, selectFlag, runMode, menuIndex1, menuIndex2, menuBounds1, menuBounds2, instructionQueue, menuList
cancelFlag = 0
selectFlag = 0
menuList = {}
menuIndex1 = 0
menuIndex2 = 0
menuBounds1 = [0,0]
menuBounds2 = [0,0]
instructionQueue = []
EVENT = threading.Event()




try:
    conn = krpc.connect(name='Mission Control', address='192.168.0.5', rpc_port=5000, stream_port=5001)
    vessel = conn.space_center.active_vessel
    mainMenu()


except KeyboardInterrupt: # Ctrl-C to terminate the program
        disp.clear()
        disp.display()
		GPIO.cleanup()

finally:
        disp.clear()
        disp.display()
		GPIO.cleanup()
