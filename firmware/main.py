import time
from machine import I2C, Pin, Timer, SPI
import framebuf
import gc 
import bmp280
from chineseNum import CHINESE_NUM_FONTS

# saving the following just to interact with ampy later on if I need to 
# $env:PATH += ";$env:USERPROFILE\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts"
my_spi_bus = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))

# muting small disp
cs_small = Pin(21, Pin.OUT, value=1)

import Pico_ePaper_2_7_V2
from bmpWithSmallDisp import EPD_1Inch54_3Color, draw_hybrid_text, num_to_chinese_digits

#  I2C Sensor config
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=100000)
bmp = bmp280.BMP280(i2c)
bmp.oversample(bmp280.BMP280_OS_HIGH)
bmp.use_case(bmp280.BMP280_CASE_WEATHER)

EPD_WIDTH_SMALL  = 200
EPD_HEIGHT_SMALL = 200
BUFFER_SIZE_SMALL = 5000 

active_display_mode = 0 
display_mode_changed = False
page_needs_update = False  
current_page = 0 
total_pages = 0              
CHARS_PER_LINE = 21         
LINES_PER_PAGE = 19         


last_sensor_update_time = 0

# Instantiating screens 
epd_large = Pico_ePaper_2_7_V2.EPD_2in7_V2()
epd_small = EPD_1Inch54_3Color(my_spi_bus)
gc.collect()


def stream_words_from_file(filename="longDistanceTrails.txt"):
    try:
        with open(filename, "r") as f:
            buffer = ""
            while True:
                chunk = f.read(64)
                if not chunk:
                    if buffer:
                        yield buffer
                    break
                buffer += chunk
                words = buffer.split()
                if not chunk.endswith((" ", "\n", "\r", "\t")):
                    buffer = words.pop() if words else ""
                else:
                    buffer = ""
                for word in words:
                    yield word
    except OSError:
        print("File not found!")

def get_page_content(target_page_num):
    current_line = ""
    current_page_lines = []
    page_counter = 0
    gc.collect()
    for word in stream_words_from_file():
        if len(current_line) + len(word) + (1 if current_line else 0) <= CHARS_PER_LINE:
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                current_page_lines.append(current_line)
            current_line = word
            if len(current_page_lines) == LINES_PER_PAGE:
                if page_counter == target_page_num:
                    return "\n".join(current_page_lines)
                page_counter += 1
                current_page_lines = []
                gc.collect()
    if current_line:
        current_page_lines.append(current_line)
    if current_page_lines and page_counter == target_page_num:
        return "\n".join(current_page_lines)
    return "--- End of Document ---"

def precalculate_total_pages():
    global total_pages
    current_line = ""
    line_count = 0
    page_count = 0
    has_words = False
    for word in stream_words_from_file():
        has_words = True
        if len(current_line) + len(word) + (1 if current_line else 0) <= CHARS_PER_LINE:
            current_line += (" " if current_line else "") + word
        else:
            line_count += 1
            current_line = word
            if line_count == LINES_PER_PAGE:
                page_count += 1
                line_count = 0
    if current_line:
        line_count += 1
    if line_count > 0 or (page_count == 0 and not has_words):
        page_count += 1
    total_pages = page_count
    print(f"File scanned! Total Pages: {total_pages}")

precalculate_total_pages()

#page handles (buttons!)
def next_page_handler(pin):
    global current_page, page_needs_update
    if active_display_mode == 0 and not page_needs_update:
        if current_page + 1 < total_pages:
            current_page += 1
            page_needs_update = True

def prev_page_handler(pin):
    global current_page, page_needs_update
    if active_display_mode == 0 and not page_needs_update:
        if current_page > 0:
            current_page -= 1
            page_needs_update = True

def toggle_display_handler(pin):
    global active_display_mode, display_mode_changed
    if not display_mode_changed:
        active_display_mode = 1 if active_display_mode == 0 else 0
        display_mode_changed = True

key_next = Pin(7, Pin.IN, Pin.PULL_UP)
key_next.irq(trigger=Pin.IRQ_FALLING, handler=next_page_handler)

key_prev = Pin(6, Pin.IN, Pin.PULL_UP)
key_prev.irq(trigger=Pin.IRQ_FALLING, handler=prev_page_handler)

key_mode = Pin(28, Pin.IN, Pin.PULL_UP)
key_mode.irq(trigger=Pin.IRQ_FALLING, handler=toggle_display_handler)


def render_page(page_num):
    cs_small.value(1) # Ensure small display is completely locked out 
    print(f"Streaming Page {page_num + 1} onto SPI lines...")
    
    epd_large.image1Gray_Portrait.fill(0xff) 
    epd_large.image1Gray_Portrait.text(f"PAGE {page_num + 1} of {total_pages}", 5, 5, epd_large.black)
    epd_large.image1Gray_Portrait.hline(5, 15, 166, epd_large.black)
    
    text_to_draw = get_page_content(page_num)
    lines = text_to_draw.split("\n")
    
    current_y = 22
    for line in lines:
        epd_large.image1Gray_Portrait.text(line, 5, current_y, epd_large.black)
        current_y += 12 
    
    epd_large.clear() 
    time.sleep(0.3) 
    epd_large.display(epd_large.buffer_1Gray_Portrait) 
    gc.collect()

def render_small_sensor_display():
    print("Writing sharp English labels with Chinese Numerals to 1.54in Display...")
    epd_small.hw_init()
    
    black_data = bytearray([0xFF] * BUFFER_SIZE_SMALL)
    
    fb_black = framebuf.FrameBuffer(black_data, EPD_WIDTH_SMALL, EPD_HEIGHT_SMALL, framebuf.MONO_HMSB)
    fb_black.fill(0xFF) 
    
    try:
        raw_pressure = "{:.0f}".format(bmp.pressure)
        print(raw_pressure)
        raw_altitude = "{:.1f}".format(bmp.altitude) 
        print(raw_altitude)
    except Exception:
        raw_pressure = "0"
        raw_altitude = "0"

    chinese_pressure_num = num_to_chinese_digits(raw_pressure)  
    chinese_altitude_num = num_to_chinese_digits(raw_altitude)  
    print(chinese_altitude_num)
    print(chinese_pressure_num)
    
    # rev string
    pressure_output = "".join(reversed(chinese_pressure_num))
    altitude_output = "".join(reversed(chinese_altitude_num))

    draw_hybrid_text(fb_black, pressure_output, 16, 50, 0, scale=1) 
    draw_hybrid_text(fb_black, altitude_output, 16, 110, 0, scale=1)
    
    epd_small.display_frame(black_data)
    epd_small.sleep()
    gc.collect()

render_page(current_page)


while True:
    if display_mode_changed:
        time.sleep(0.4) 
        if active_display_mode == 0:
            print("Switched Mode: Returning to 2.7-inch Book Reader...")
            render_page(current_page)
        else:
            print("Switched Mode: Launching 1.54-inch Sensor Panel...")
            render_small_sensor_display()
            last_sensor_update_time = time.ticks_ms()
        display_mode_changed = False

    # only reader mode 
    if page_needs_update and active_display_mode == 0:
        render_page(current_page)
        time.sleep(0.2) 
        page_needs_update = False  
    current_time = time.ticks_ms()
    
    if active_display_mode == 1:
        if time.ticks_diff(current_time, last_sensor_update_time) > 8000:
            if not display_mode_changed: 
                render_small_sensor_display()
                last_sensor_update_time = time.ticks_ms()
    else:
        if time.ticks_diff(current_time, last_sensor_update_time) > 3000:
            last_sensor_update_time = time.ticks_ms()

    time.sleep(0.01) 

