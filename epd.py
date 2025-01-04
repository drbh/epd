from machine import Pin
import time
import framebuf

# Reference:
# https://github.com/WeActStudio/WeActStudio.EpaperModule
# https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/epd29_ssd1680.py

class EPD_2_9:
    def __init__(self, spi, cs, dc, rst, busy, landscape=True):
        # Display resolution
        self.WIDTH = 128
        self.HEIGHT = 296
        self.LANDSCAPE = landscape

        # In landscape, we swap width and height
        self.DISPLAY_WIDTH = self.HEIGHT if self.LANDSCAPE else self.WIDTH
        self.DISPLAY_HEIGHT = self.WIDTH if self.LANDSCAPE else self.HEIGHT

        # Use MONO_VLSB for landscape as we need vertical byte orientation
        self.MODE = framebuf.MONO_VLSB if self.LANDSCAPE else framebuf.MONO_HLSB

        self.spi = spi
        self.cs = Pin(cs, Pin.OUT)
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.busy = Pin(busy, Pin.IN)
        self.cs.on()

        # Create frame buffer
        self.buffer = bytearray(self.DISPLAY_WIDTH * self.DISPLAY_HEIGHT // 8)
        self.framebuf = framebuf.FrameBuffer(
            self.buffer, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, self.MODE
        )

        self.power_is_on = False
        self.init_done = False

        # Initialize display
        self._init_display()

    def _wait_until_idle(self):
        time.sleep_ms(50)  # Initial delay before checking busy
        while self.busy.value() == 1:
            time.sleep_ms(100)

    def _reset(self):
        self.rst.on()
        time.sleep_ms(200)
        self.rst.off()
        time.sleep_ms(200)
        self.rst.on()
        time.sleep_ms(200)

    def _send_command(self, command):
        self.cs.off()
        self.dc.off()
        self.spi.write(bytes([command]))
        self.cs.on()

    def _send_data(self, data):
        self.cs.off()
        self.dc.on()
        if isinstance(data, int):
            self.spi.write(bytes([data]))
        else:
            self.spi.write(data)
        self.cs.on()

    def _init_display(self):
        # Hardware reset
        self._reset()
        self._wait_until_idle()

        # Initialize display
        self._send_command(0x01)  # Driver output control
        self._send_data(0x27)  # Y output from 0x27 to 0x00
        self._send_data(0x01)
        self._send_data(0x01)

        self._send_command(0x11)  # Data entry mode
        self._send_data(0x01)  # Y increment, X increment

        self._send_command(0x44)  # Set RAM X address
        self._send_data(0x00)  # Start addr
        self._send_data(0x0F)  # End addr (0x0F = (128-1)/8)

        self._send_command(0x45)  # Set RAM Y address
        self._send_data(0x27)  # Start addr 295
        self._send_data(0x01)
        self._send_data(0x00)  # End addr 0
        self._send_data(0x00)

        self._send_command(0x3C)  # Border waveform
        self._send_data(0x05)

        self._send_command(0x21)  # Display update control
        self._send_data(0x00)
        self._send_data(0x80)

        self._send_command(0x18)  # Temperature sensor
        self._send_data(0x80)  # Internal sensor

        self._send_command(0x4E)  # Set RAM X counter
        self._send_data(0x00)
        self._send_command(0x4F)  # Set RAM Y counter
        self._send_data(0x27)  # 295
        self._send_data(0x01)

        # Initialize buffer to white
        self.framebuf.fill(1)

        # Initial refresh
        self.display(True)

        self.init_done = True

    def display(self, full_refresh=False):
        """Update display with current frame buffer"""
        if not self.init_done:
            return

        mvb = memoryview(self.buffer)
        buf1 = bytearray(1)

        # Write display RAM
        self._send_command(0x24)  # Write RAM command

        if self.LANDSCAPE:
            # Landscape mode requires special handling of data
            wid = self.DISPLAY_WIDTH
            tbc = self.DISPLAY_HEIGHT // 8  # Vertical bytes per column
            iidx = wid * (tbc - 1)  # Initial index
            idx = iidx  # Index into framebuf
            vbc = 0  # Current vertical byte count
            hpc = 0  # Horizontal pixel count

            for _ in range(len(mvb)):
                buf1[0] = ~mvb[idx]  # Invert data
                self._send_data(buf1)
                idx -= wid
                vbc += 1
                if vbc == tbc:
                    vbc = 0
                    hpc += 1
                    idx = iidx + hpc
        else:
            # Portrait mode - direct write with inversion
            for b in mvb:
                buf1[0] = ~b  # Invert data
                self._send_data(buf1)

        # Update display
        self._send_command(0x22)  # Display update control
        if full_refresh:
            self._send_data(0xF7)  # Full update
        else:
            self._send_data(0xFF)  # Partial update

        self._send_command(0x20)  # Activate Display Update Sequence
        self._wait_until_idle()

    def sleep(self):
        """Enter deep sleep mode"""
        self._send_command(0x10)  # Enter deep sleep
        self._send_data(0x01)
        time.sleep_ms(100)

    def wake(self):
        """Wake up from deep sleep"""
        self._reset()
        self._init_display()

    # Framebuffer proxy methods for drawing
    def pixel(self, x, y, color):
        """Draw a pixel. color: 0 for black, 1 for white"""
        self.framebuf.pixel(x, y, color)

    def text(self, text, x, y, color=0):
        """Draw text. color: 0 for black, 1 for white"""
        self.framebuf.text(text, x, y, color)

    def rect(self, x, y, w, h, color):
        """Draw a rectangle. color: 0 for black, 1 for white"""
        self.framebuf.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color):
        """Draw a filled rectangle. color: 0 for black, 1 for white"""
        self.framebuf.fill_rect(x, y, w, h, color)

    def fill(self, color):
        """Fill entire display. color: 0 for black, 1 for white"""
        self.framebuf.fill(color)
