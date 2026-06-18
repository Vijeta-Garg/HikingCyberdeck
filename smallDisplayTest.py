import time
import framebuf 
from machine import Pin, SPI

# Pin definitions directly from your schematic
PIN_CS   = 21 
PIN_DC   = 22  
PIN_RST  = 26 
PIN_BUSY = 27  

EPD_WIDTH  = 200
EPD_HEIGHT = 200
BUFFER_SIZE = 5000  # 200x200 / 8 bits

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

        self.write_cmd(0x11) 
        self.write_data(0x01)
        
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
        # Proper refresh: Wait 5 seconds for particles to cycle before sleeping
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
                self.write_data(0x00) # Keep red off in standard logic
                
        self.update()

    def display_clear(self):
        self.write_cmd(0x24)
        for i in range(BUFFER_SIZE):
            self.write_data(0xFF) # Standard White for Black channel
        self.write_cmd(0x26)
        for i in range(BUFFER_SIZE):
            self.write_data(0x00) # Standard White for Red channel
        self.update()

    def sleep(self):
        self.write_cmd(0x10)
        self.write_data(0x01)
        time.sleep_ms(10)

# --- Main Program Execution ---
if __name__ == '__main__':
    print("Initializing Display...")
    epd = EPD_1Inch54_3Color()
    epd.hw_init()
    
    print("Clearing display cleanly...")
    epd.display_clear()
    time.sleep(1)
    
    # Create two raw byte memory spaces for our canvases
    black_data = bytearray(BUFFER_SIZE)
    red_data   = bytearray(BUFFER_SIZE)
    
    # Link MicroPython's framebuf to our memory blocks
    # MONO_HMSB tells it to pack pixels into bytes horizontally
    fb_black = framebuf.FrameBuffer(black_data, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HMSB)
    fb_red   = framebuf.FrameBuffer(red_data, EPD_WIDTH, EPD_HEIGHT, framebuf.MONO_HMSB)
    
    # Fill background with standard White
    fb_black.fill(1) # 1 = White
    fb_red.fill(0)   # 0 = White (No red ink active)
    
    # Draw Text on the Black Layer
    # Syntax: .text("string", x_position, y_position, color)
    print("Writing text to memory...")
    fb_black.text("olleh", 80, 95, 0) # 0 = Black ink pixel
    
    print("Refreshing screen panels properly...")
    epd.display_frame(black_data, red_data)
    
    print("Done! Putting hardware to sleep.")
    epd.sleep()

