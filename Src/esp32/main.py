import machine
from machine import Pin, PWM, ADC
import time
import os
from servo import Servo
from time import sleep

class Logger:
    def info(self, message):
        print("[INFO]", message)
    
    def warning(self, message):
        print("[WARNING]", message)
        
    def signal(self, message):
        print("[SIGNAL]", message)
    
    def error(self, message):
        print("[ERROR]", message)
 
    def debug(self, message):
        print("[DEBUG]", message)
        
logger = Logger()

###############################################
### Video Class for OnePixelCamera
###############################################
class One_Pixel_Cam:
    def __init__(self, mot_pin_x, mot_pin_y, sensor_pin, carto_xmin, carto_xmax, carto_xstp, carto_ymin, carto_ymax, carto_ystp, timeout=0.1):
        self.mot_pin_x = mot_pin_x
        self.mot_pin_y = mot_pin_y
        self.sensor_pin = sensor_pin
        self.carto_xmin = carto_xmin
        self.carto_xmax = carto_xmax
        self.carto_xstp = carto_xstp
        self.carto_ymin = carto_ymin
        self.carto_ymax = carto_ymax
        self.carto_ystp = carto_ystp
        self.timeout = timeout
        self._is_running = False
        self._is_close = False
        self._is_connected = False
        self.carto_is_done = False

        # Init carto parameters
        #[start + i * step for i in range(int((stop - start) / step))]
        #self.x_range = np.arange(self.carto_xmin, self.carto_xmin + self.carto_xstp, self.carto_xstp)
        self.x_range = [x for x in range(int(self.carto_xmin), int(self.carto_xmax + self.carto_xstp), int(self.carto_xstp))]
        self.y_range = [y for y in range(int(self.carto_ymin), int(self.carto_ymax + self.carto_ystp), int(self.carto_ystp))]        

        # Create a 2D array: dimensions [len(y_range)][len(x_range)]
        self.grid = [[0 for _ in range(len(self.x_range))] for _ in range(len(self.y_range))]
        self.num_pts_total = len(self.x_range) * len(self.y_range)

        #self.time_init = "{0:%Y-%m-%d_%H%M%S}".format(datetime.datetime.now())

        logger.info("One Pixel Camera: init.")

    def start(self):
        self.sensor_start()
        if self._is_connected is True:
            logger.info("One Pixel Camera: already connected, restarting")
            self.close()
        try:
            # Hardware for scanning
            self.motor_start()
            self.sensor_start()
            self.isopened = True
            logger.info("One Pixel Camera: connection done")

        except:
            logger.debug("One Pixel Camera: failed connection")
            self.close()
            logger.debug("One Pixel Camera: connection closed")
            logger.debug("One Pixel Camera: you should retry connection")
        self._is_connected = True

    def motor_start(self):
        self.motor_x = Servo(pin=self.mot_pin_x)
        self.motor_y = Servo(pin=self.mot_pin_y)
        logger.info("Motors: starting complete")

    def motor_go_to(self, pos_x, pos_y):
        self.motor_x.move(pos_x)
        self.motor_y.move(pos_y)
        logger.info(f"Motors: going to x={pos_x}, y={pos_y}")

    def motor_get_pos(self):
        "Not implemented yet"
        pos_x = -1
        pos_y = -1
        return pos_x, pos_y

    def sensor_start(self):
        self.pot = ADC(Pin(self.sensor_pin))
        self.pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v
        logger.info("Sensor: starting complete")

    def sensor_read(self):
        sensor_val = self.pot.read()
        logger.debug(f"Sensor: measured at {sensor_val}")
        return sensor_val


    def get_signal(self, pos_x, i, pos_y, j):
        if self._is_connected:

            logger.info(5*'#' + 'Posx=' + str(pos_x) + ', Posy=' + str(pos_y))
            logger.info(3*'#' + '%d/%d' % (self.num_op, len(self.x_range)*len(self.y_range)-1))

            self.motor_go_to(pos_x, pos_y)
            time.sleep(0.2)

            #pos_x, pos_y = self.motor_get_pos()

            logger.signal(f'Motor: positioned at x={pos_x}, y={pos_y}')

            # Take measurement
            meas_val = self.sensor_read()
            logger.signal(f'Intensity: measured at {meas_val}')
            #Store in the grid using indices i (x) and j (y)
            self.grid[j][i] = meas_val

            time.sleep(0.2)
            self.num_op += 1
            # Emit the generated image to the main thread
            #self.carto_finished.emit(self.measurements)


    # The scanning method
    def scan(self, flip_direction=False):
        self.num_op = 0
        self.is_running = True

        start = time.time()
        if flip_direction:
            modulo = 2
        else:
            modulo = 1

        for j, y in enumerate(self.y_range):

            if j % modulo == 0:
                for i, x in enumerate(self.x_range):
                    self.get_signal(x, i, y, j)

            else:
                for i, x in reversed(list(enumerate(self.x_range))):
                    self.get_signal(x, i, y, j)

        self.close()

  
    def close(self):
        # Go back to the middle
        x_mid, y_mid = 45, 45 # TODO update it
        self.motor_go_to(x_mid, y_mid)

        logger.info("Scanning: Stop")
        
        # Final result printing
        print("\n--- Final Scanned Array ---")
        print("\n--- Copy data below ---")
        for row in self.grid:
            print(f"{row},")
        print("--- End of data ---")
        
        self.is_running = False
        self.standby = False

###############################################
### My Main
###############################################
def main_v01():
    print("Testing the One pixel camera prototype")
    scanner = One_Pixel_Cam(mot_pin_x=1, mot_pin_y=2, sensor_pin=0, carto_xmin=0, carto_xmax=50, carto_xstp=1, carto_ymin=0, carto_ymax=25, carto_ystp=1, timeout=0.5)
    scanner.start()
    time.sleep(0.5)

    scanner.scan()
    time.sleep(0.5)
  
    scanner.close()


def debug_sensor():
    led_sensor = ADC(Pin(0))
    led_sensor.atten(ADC.ATTN_11DB)  # Full range 0-3.6V

    while True:
        value = led_sensor.read()  # 0 to 4095
        print("Light level:", value)
        time.sleep(0.02)
      
###############################################
### Main
###############################################
if __name__ == "__main__":
    main_v01()
    #debug_sensor()


