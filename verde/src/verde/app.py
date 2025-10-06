"""
iGEM 2025 NYC Empire State app
"""
import asyncio
from datetime import datetime
from matplotlib import dates
import serial
import serial.tools.list_ports
import toga
from toga.style.pack import COLUMN, ROW
from toga.sources import ListSource
import toga_chart


class Verde(toga.App):

    def construct_serial(self):
        try:
            # Open the serial port
           self.ser = serial.Serial(self.device_port, 9600, timeout=1)
           self.sync_data()
        except serial.SerialException as e:
            print(f"Error setting up serial connection: {e}")

    async def sync_data(self):
        try:
            # Read data from the serial port
            while self.ser.readable():
                ph = self.ser.readline().decode('utf-8').strip()
                print(f"Received: {ph}")
                self.ph_indicator.value = ph
                self.time_indicator.value = None
                self.recreate_data()
                await asyncio.sleep(1)

        except serial.SerialException as e:
            print(f"Error reading from device: {e}")

    def destroy_serial(self):
        # Close the serial port
        if self.ser.is_open:
            self.ser.close()

    def handle_connection_button(self):
        if self.connection_button.text == 'Connect to Device':
            self.construct_serial()
            self.connection_button.text = 'Disconnect from Device'
        else:
            self.destroy_serial()
            self.connection_button.text = 'Connect to Device'

    def set_chart_data(self):
        if self.ph_indicator.value:
            # Set the time indicator minimum to 0:00:00 for starting x data point
            self.time_indicator.min = None
            self.x_data[0] = self.time_indicator.min

            # Set the min/max to the current time so that the widget can't be edited
            self.time_indicator.min = self.time_indicator.value
            self.time_indicator.max = self.time_indicator.value

            # Set next x data point
            self.x_data.append(self.time_indicator.value)
            
            # the serial message format is "ph: [number]\n", need to extract the number
            next_y = self.ph_indicator.value.split(": ")[1]
            self.y_data.append(float(next_y))

    def draw_chart(self, chart, figure, *args, **kwargs):
        ax = figure.add_subplot(1, 1, 1)

        # X-axis value range
        format_string = "%H:%M:%S"
        ax.set_xlim(
            datetime.strptime("00:00:00", format_string).isoformat(timespec='seconds'),
            datetime.strptime("23:59:59", format_string).isoformat(timespec='seconds'),
        )
        ax.xaxis.set_major_locator(dates.HourLocator(interval=3))
        ax.xaxis.set_major_formatter(dates.DateFormatter("%H:%M:%S"))
        # Y-axis value range
        ax.set_ylim(0, 14)
        ax.plot(self.x_data, self.y_data, 'o-')
        ax.set_xlabel("Time")
        ax.set_ylabel("pH")

        figure.tight_layout()

    def recreate_data(self):
        self.set_chart_data()
        self.chart.redraw()
        
    def startup(self):
        self.device_port = ""
        self.ser = None
        self.x_data = []
        self.y_data = []
        self.main_window = toga.MainWindow(title='Verde')
        main_box = toga.Box(direction=COLUMN)

        # scan_for_device_button.style.margin = 50
        # scan_for_device_button.style.flex = 1

        verde_label = toga.Label('Verde')
        main_box.add(verde_label)

        ports_info = serial.tools.list_ports.comports()

        # self.usb_device_names = [f"{port_info.description}: {port_info.device}" for port_info in ports_info]
        self.usb_device_names = ListSource(
            accessors=["desc", "port", "display"],
            data=[
                { 
                    "desc": port_info.description,
                    "port": port_info.device,
                    "display": f"{port_info.description}: {port_info.device}",
                } for port_info in ports_info
            ],
        )

        def set_device():
            self.destroy_serial()
            self.device_port = device_selector.value.port if device_selector.value else ""

        device_selector_label = toga.Label('Discovered USB Devices')
        device_selector = toga.Selection(
            items=self.usb_device_names,
            accessor="display",
            on_change=set_device,
        )

        main_box.add(device_selector_label)
        main_box.add(device_selector)

        self.connection_button = toga.Button(on_press=self.handle_connection_button)
        main_box.add(self.connection_button)

        self.ph_indicator = toga.TextInput(readonly=True)
        main_box.add(self.ph_indicator)

        time_label = toga.Label('Last updated at:')
        main_box.add(time_label)

        self.time_indicator = toga.TimeInput()
        self.time_indicator.min = self.time_indicator.value
        self.time_indicator.max = self.time_indicator.value
        main_box.add(self.time_indicator)

        self.set_chart_data()
        self.chart = toga_chart.Chart(style=toga.style.Pack(flex=1), on_draw=self.draw_chart)
        main_box.add(self.chart)

        self.main_window.content = main_box
        self.main_window.show()


def main():
    return Verde()
