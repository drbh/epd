<a href="https://www.aliexpress.us/item/3256804458201128.html">
<img src="https://github.com/user-attachments/assets/afe83db1-b2eb-48e1-92c2-445993f754f3" width="500"/>
</a>

# epaper driver

This is a driver for the WeAct Studio ePaper display. This is a simple single file driver that can be used to display text and images on the ePaper display. 

The driver is written in MicroPython and does not require any additional libraries/dependencies.

## Usage

Personally I just copy the `edp.py` file to the device and import it in my main script. The driver is very simple and only has a few functions:

```python
from machine import Pin, SPI
from edp import EPD_2_9

# Initialize SPI
spi = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(4), mosi=Pin(6))

# Initialize display
display = EPD_2_9(
    spi=spi,
    cs=Pin(7, Pin.OUT),
    dc=Pin(1, Pin.OUT),
    rst=Pin(2, Pin.OUT),
    busy=Pin(3, Pin.IN),
    landscape=True,
)

# fill the display with black color
display.framebuf.fill(1)

# Display text
display.text("Hello World!", 10, 10, 0)

# A full refresh is update
display.display(True)
```


## Debugging

This is just a small library I rolled to get the ePaper display working with a ESP32C3. It is not perfect and might not work with all ePaper displays. If you have any issues, feel free to open an issue or a pull request!

### Pinout with ESP32C3

| ePaper | ESP32C3 |
| ------ | ------- |
| VCC    | 3.3V    |
| GND    | GND     |
| DIN    | GPIO6   |
| CLK    | GPIO4   |
| CS     | GPIO7   |
| DC     | GPIO1   |
| RST    | GPIO2   |
| BUSY   | GPIO3   |
    
First I flash the board with `ESP32_GENERIC_C3-20240602-v1.23.0.bin` and then copy the `edp.py` file to the board. To test, you can connect to the serial port, start the REPL and copy and paste the code above. The display should show "Hello World!".
