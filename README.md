# HikerDeck

# My inspiration: 
My Instagram feed inspired me to make a cyberdeck, offline computers housed in cute compartments one could access offline. My sister had her birthday just a few weeks ago, so I wanted to gift her a cyberdeck she'd love. User needs: she is into hiking, reading, and learning new languages (currently Chinese). So I made a multilingual e-reading environment-sensing cyberdeck that would be useful on a hike. For example, it can load up a "hiking survival guide" on an offline e-reader and also tell you the altitude you are at in the hike in Chinese numerals. 

<img width="1776" height="1022" alt="image" src="https://github.com/user-attachments/assets/40ca1345-b739-4456-bed3-6bcaf5c753b0" />

# What does the project do?
The project is a dual-display cyberdeck optimized for hiking. It is an offline "mini computer" which can scroll through files such as a hiking survival guide. At the same time, on another display it can display the current pressure and altitude a hiker is at in Chinese lettering. The cyberdeck itself is controlled by 3 CherryMX switches and is housed inside a sunglass case! 

# Schematic:
Please note! The hikerdeck is currently perfboarded not PCBed! The entire wiring is contained inside the casing and once spread out it looks like this:
<img width="1235" height="784" alt="image" src="https://github.com/user-attachments/assets/a1266ec9-c9fb-4093-b475-64de4d5bee3d" />



# Firmware
The firmware adds on top of pre-existing sensor and display libraries (most notably gc and framebuffer) to display sensor values (like altitude) onto the small display. Using a custom-made Chinese bitmap font library, the firmware prints to the smaller display in Chinese lettering. At the same time, it also coordinates SPI activation between both the large and small displays which are wired onto the same SPI bus. The firware also takes the external buttons as inputs for when to switch display or when to switch pages on the larger display. The firware additionally calculates how many pages of hiking survival guide text there are on the large display and renders them onto the large display in an appropriate manner (without breaking up too much text or going off the page). 
Usage of each file is as following:
+ Pico_ePaper_2_7_V2.py --> library for the ePaper 2.7in V2 display (pre-existing) 
+ bmp280.py --> library for environment sensor (pre-existing) 
+ bmpWithSmallDisp.py --> module I made (which includes some pre-existing library code for 1.54'' display) which displays environmental stats in
+ Chinese lettering on the small display 
+ ChineseNum.py --> bitmap library I refer to in bmpWithSmallDisp.py helps me map characters onto small display 
+ main.py --> accepts button input, calculates and renders text info for the large display, controls SPI activation/switching, imports bmpWithSmallDisp to also switch to small display rendering 

# Layout:
I drew a small diagram to help you understand where everything fits inside the casing! 


# Casing:
Currently not 3D printed yet, but the CAD files are ready and I am using a cardboard case right now! 
<img width="1108" height="900" alt="image" src="https://github.com/user-attachments/assets/01336b22-bec8-4ccc-ad4d-c275af80a395" />


# How does it all fit together? *NOTE ADD MORE HERE*
The sunglass case has different "layers": 
The top layer is the two displays which live on the lid 
Below that, there are 3 mounted CherryMX switches and a port to connect to the pico underneath. 
And on the very bottom under the switches there's the perfboard where the raspberry pico w, battery, and environment sensor live. 

<img width="678" height="972" alt="image" src="https://github.com/user-attachments/assets/e5e1e2ea-ae3e-4d67-8cb4-797d9b7f6b5b" />


**here is the link to my demo video!:** https://youtu.be/0BxvbPZM9zg
