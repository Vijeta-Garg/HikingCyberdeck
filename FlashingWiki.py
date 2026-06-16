import time
from machine import I2C, Pin, Timer
import Pico_ePaper_2_7_V2
import gc 
import bmp280

# ==========================================
# 1. INITIALIZE HARDWARE CONFIGURATION
epd = Pico_ePaper_2_7_V2.EPD_2in7_V2()

CHARS_PER_LINE = 21         
LINES_PER_PAGE = 19         
current_page = 0 
page_needs_update = False  
sensor_needs_read = False    # New flag for sensor timing
pages = []

i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100000)
bmp = bmp280.BMP280(i2c)
bmp.oversample(bmp280.BMP280_OS_HIGH)
bmp.use_case(bmp280.BMP280_CASE_WEATHER)



# Run this right before calling create_pages_from_file <-- should I be unning this? echeck ! 
gc.collect() 

# ==========================================
# 2. STRING LAYOUT PAGINATION ENGINE
def create_pages_from_file():
    global pages
    try:
        with open("longDistanceTrails.txt", "r", encoding="utf-8") as f:
            full_text = f.read(800)
    except OSError:
        pages = ["Error: article.txt not found!"]
        return

    words = full_text.split()
    all_lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= CHARS_PER_LINE:
            current_line += (word + " ")
        else:
            all_lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        all_lines.append(current_line.strip())

    current_page_text = []
    for line in all_lines:
        current_page_text.append(line)
        if len(current_page_text) == LINES_PER_PAGE:
            pages.append("\n".join(current_page_text))
            current_page_text = []
            
    if current_page_text:
        pages.append("\n".join(current_page_text))
        
    if not pages:
        pages.append("--- Empty Document ---")

create_pages_from_file()
print(f"File processed! Total Pages generated: {len(pages)}")


# ==========================================
# 3. INTERRUPT HANDLERS (Ultra-fast, no allocation)
# ==========================================
def next_page_handler(pin):
    global current_page, page_needs_update
    if not page_needs_update:
        if current_page + 1 < len(pages):
            current_page += 1
            page_needs_update = True

def prev_page_handler(pin):
    global current_page, page_needs_update
    if not page_needs_update:
        if current_page > 0:
            current_page -= 1
            page_needs_update = True

key_next = Pin(2, Pin.IN, Pin.PULL_UP)
key_next.irq(trigger=Pin.IRQ_FALLING, handler=next_page_handler)

key_prev = Pin(3, Pin.IN, Pin.PULL_UP)
key_prev.irq(trigger=Pin.IRQ_FALLING, handler=prev_page_handler)

# Timer callbacks ONLY change flags
def timer_sensor_cb(t):
    global sensor_needs_read
    sensor_needs_read = True

# Trigger sensor reading flag every 1000ms
timer_b = Timer(period=1000, mode=Timer.PERIODIC, callback=timer_sensor_cb)

# ==========================================
# 4. EXECUTION FUNCTIONS (Run safely in main loop)
# ==========================================
def senseAlt():
    print("pressure: {}Pa".format(bmp.pressure))
    print("altitude: {}".format(bmp.altitude))

def render_page(page_num):
    print(f"Sending Page {page_num + 1} over 8-pin SPI lines...")
    epd.image1Gray_Portrait.fill(0xff) 
    epd.image1Gray_Portrait.text(f"PAGE {page_num + 1} of {len(pages)}", 5, 5, epd.black)
    epd.image1Gray_Portrait.hline(5, 15, 166, epd.black)
    
    text_to_draw = pages[page_num]
    lines = text_to_draw.split("\n")
    
    current_y = 22
    for line in lines:
        epd.image1Gray_Portrait.text(line, 5, current_y, epd.black)
        current_y += 12 
    
    epd.clear() 
    time.sleep(0.3) # Safe to sleep here because we are in the main execution loop!
    epd.display(epd.buffer_1Gray_Portrait) 
    print("Page update finished successfully.")

# ==========================================
# 5. EXECUTION RUNTIME ROUTINE
# ==========================================
# Force render Page 1 on boot up
render_page(current_page)

while True:
    # Handle safe screen updates
    if page_needs_update:
        render_page(current_page)
        time.sleep(1.0)          # Hardware cooldown & debouncing window
        page_needs_update = False  # Correctly resets the global variable

    # Handle safe sensor readings
    if sensor_needs_read:
        senseAlt()
        sensor_needs_read = False

    time.sleep(0.05) # Tiny sleep to keep the Pico W running cool
