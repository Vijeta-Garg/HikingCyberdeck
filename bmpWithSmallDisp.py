import time
import framebuf 
from machine import Pin, SPI, Timer, I2C
import bmp280
import gc

# Pin definitions directly from your schematic
PIN_CS   = 21 
PIN_DC   = 22  
PIN_RST  = 26 
PIN_BUSY = 27  

EPD_WIDTH  = 200
EPD_HEIGHT = 200
BUFFER_SIZE = 5000  # 200x200 / 8 bits

sensor_needs_read = False    

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100000)
bmp = bmp280.BMP280(i2c)
bmp.oversample(bmp280.BMP280_OS_HIGH)
bmp.use_case(bmp280.BMP280_CASE_WEATHER)

gc.collect()

class EPD_1Inch54_3Color:
    def __init__(self):
        self.cs   = Pin(PIN_CS, Pin.OUT, value=1)
        self.dc   = Pin(PIN_DC, Pin.OUT, value=0)
        self.rst  = Pin(PIN_RST, Pin.OUT, value=1)
        self.busy = Pin(PIN_BUSY, Pin.IN, Pin.PULL_DOWN)
        
        # Hardware SPI1 matching your layout
        self.spi = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)
        
    def write_data(self, value):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytes([value]))
        self.cs.value(1)
        
    def chkstatus(self):
        while self.busy.value() == 1:
            time.sleep_ms(50)
        
    def reset(self):
        self.rst.value(0)
        time.sleep_ms(200)
        self.rst.value(1)
        time.sleep_ms(200)
        
    def hw_init(self):
        self.reset()
        self.chkstatus()
        self.write_cmd(0x12) # SWRESET
        self.chkstatus()
        
        self.write_cmd(0x01) 
        self.write_data(0xC7)
        self.write_data(0x00)
        self.write_data(0x00)

        # --- FIX HERE: Changed from 0x01 to 0x03 to make text write forwards ---
        self.write_cmd(0x11) 
        self.write_data(0x03) # 0x03 = X increment, Y increment (Standard Orientation)
        
        self.write_cmd(0x44) 
        self.write_data(0x00)
        self.write_data(0x18) 
        
        self.write_cmd(0x45) 
        self.write_data(0xC7)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        
        self.write_cmd(0x3C) 
        self.write_data(0x05)
        
        self.write_cmd(0x18) 
        self.write_data(0x80)
        
        self.write_cmd(0x4E) 
        self.write_data(0x00)
        self.write_cmd(0x4F) 
        self.write_data(0xC7)
        self.write_data(0x00)
        self.chkstatus()
        
    def update(self):
        self.write_cmd(0x22)
        self.write_data(0xF7)
        self.write_cmd(0x20)
        time.sleep(5) 
        self.chkstatus()

    def display_frame(self, black_buffer, red_buffer=None):
        self.write_cmd(0x24)
        for i in range(BUFFER_SIZE):
            self.write_data(black_buffer[i])
            
        self.write_cmd(0x26)
        for i in range(BUFFER_SIZE):
            if red_buffer is not None:
                self.write_data(red_buffer[i])
            else:
                self.write_data(0x00) 
                
        self.update()

    def display_clear(self):
        self.write_cmd(0x24)
        for i in range(BUFFER_SIZE):
            self.write_data(0xFF) 
        self.write_cmd(0x26)
        for i in range(BUFFER_SIZE):
            self.write_data(0x00) 
        self.update()

    def sleep(self):
        self.write_cmd(0x10)
        self.write_data(0x01)
        time.sleep_ms(10)
        

def timer_sensor_cb(t):
    global sensor_needs_read
    sensor_needs_read = True

timer_b = Timer(period=1000, mode=Timer.PERIODIC, callback=timer_sensor_cb)

def senseAlt():
    print("pressure: {}Pa".format(bmp.pressure))
    print("altitude: {}".format(bmp.altitude))

# --- Main Program Execution ---
if __name__ == '__main__':
    print("Initializing Display...")
    epd = EPD_1Inch54_3Color()
    epd.hw_init()
    
    print("Clearing display cleanly...")
    epd.display_clear()
    time.sleep(1)
    
    # FIX: Pre-fill raw memory blocks to match target baseline configurations
    black_data = bytearray([0xFF] * BUFFER_SIZE)
    red_data   = bytearray([0x00] * BUFFER_SIZE)
    
    fb_black = framebuf.FrameBuffer(black_data, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HMSB)
    fb_red   = framebuf.FrameBuffer(red_data, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HMSB)
    
    fb_black.fill(1) # 1 = White background
    fb_red.fill(0)   # 0 = Transparent/No red background
    
    # Read fresh sensor data before drawing to screen
    try:
        stPss = "pressure: {:.0f}Pa".format(bmp.pressure)
    except Exception:
        stPss = "Sensor Error"

    # Draw Text on the Black Layer
    print("Writing text to memory...")
    # Shifted X position from 80 to 10 so long pressure strings do not clip off-screen
    fb_black.text(stPss, 10, 95, 0) # 0 = Black text
    
    print("Refreshing screen panels properly...")
    epd.display_frame(black_data, red_data)
    
    print("Done! Putting hardware to sleep.")
    epd.sleep()
