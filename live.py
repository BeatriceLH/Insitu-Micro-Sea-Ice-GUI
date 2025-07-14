

import tkinter as tk
from tkinter import HORIZONTAL, Label, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from simple_pyspin import Camera
from PIL import Image, ImageTk
import threading
import serial
import os
import time
import sys
import tifffile
from matplotlib_scalebar.scalebar import ScaleBar

bgColor = 'powderblue'
def CreateGUI():
    global window, FileFrame, SettingsFrame, imageFrame, AcqFrame
    bgColor = 'powderblue'
    window = tk.Tk()
    window.wm_title("SeaIceMicro")
    window.configure(bg=bgColor)
    FileFrame = tk.Frame(window,bg = bgColor)
    FileFrame.grid(row=1,column=0)
    SettingsFrame = tk.Frame(window,bg=bgColor)
    SettingsFrame.grid(row=0, column=0)
    imageFrame = tk.Frame(window, bg=bgColor)
    imageFrame.grid(row=0, column=1)
    AcqFrame = tk.Frame(window, bg=bgColor)
    AcqFrame.grid(row=1, column=1)
class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
class Illumination:
    BAUD_RATE = 115200
    DEFAULT_DELAY = 3
    DEFAULT_COMMAND = 'U'
    COMMANDS = {'Fluo': 'F', 'Up': 'U', 'Down': 'D', 'Left':'L', 'Right':'R', 'Close': 'Clear', 'Default': DEFAULT_COMMAND}

    def __init__(self, port='COM3', baudrate=BAUD_RATE):
        self.arduino = serial.Serial(port=port, baudrate=baudrate)
        time.sleep(self.DEFAULT_DELAY)
        self.arduino.write(self.DEFAULT_COMMAND.encode())

    def send_command(self, command):
        cmd = self.COMMANDS.get(command)
        if not cmd:
            raise ValueError('Invalid command.')
        self.arduino.write(cmd.encode())


def initializeCam(cam):
	cam.init()
	cam.AcquisitionMode = 'SingleFrame' 
	cam.PixelFormat= 'RGB8'
	cam.BinningVertical = 1
	cam.Width = 1920
	cam.Height = 1200
	cam.AcquisitionFrameRateAuto = 'Off'
	cam.AcquisitionFrameRateEnabled = True
	cam.AcquisitionFrameRate = 20 
	cam.GainAuto = 'Off'
	gain =  cam.get_info('Gain')['max']
	cam.Gain = gain
	cam.ExposureAuto = 'Off'
	cam.ExposureTime = 10000 
	global illumination
	illumination = Illumination()

with Camera() as cam:
	def add_button_Live():
		button_live = tk.Button(imageFrame, text="Start Live", command=_live)
		button_live.grid(row=1, column=0)

	def add_PixelFormat(Row):
		def update_pixel(entry):
			cam.stop()
			cam.PixelFormat = entry.get()
			print('Pixel format changed to', cam.PixelFormat)
			cam.start()
		Label = tk.Label(SettingsFrame, text='Pixel Format: ', font=('TkDefaultFont', 12))
		Label.grid(row=Row, column =0, sticky='E')
		Label.config(bg=bgColor)
		entry = ttk.Combobox(SettingsFrame, state = 'readonly',width=10)
		entry['values'] = ('RGB8','Mono8','Mono16','BayerRG8','BayerRG16')
		entry.current(0)
		entry.grid(row=Row, column=1)
		entry.bind("<<ComboboxSelected>>", lambda event, entry=entry: update_pixel(entry)) 

	def add_FrameRate(Row):
		def update_FrameRate(entry):
			new = int(entry.get())
			cam.AcquisitionFrameRate = min(new, cam.get_info('AcquisitionFrameRate')['max'])
			print('Frame rate changed to: %.3f' % (cam.AcquisitionFrameRate))
		Label = tk.Label(SettingsFrame, text='Frame Rate (Hz):', font=('TkDefaultFont', 12))
		Label.grid(row=Row, column =0, sticky='E')
		Label.config(bg=bgColor)
		entry = tk.Scale(SettingsFrame,variable=tk.DoubleVar(),from_=1, to =28, width=10, orient=HORIZONTAL,bg=bgColor)
		entry.grid(row=Row, column=1)
		entry.set(cam.AcquisitionFrameRate)
		entry.bind("<ButtonRelease-1>", lambda event, entry=entry: update_FrameRate(entry)) 

	def add_Gain(Row):
		def update_gain(entry):
			new = int(entry.get())
			cam.Gain = min(new, cam.get_info('Gain')['max']) 
			print('Gain changed to: %.3f' % (cam.Gain))
		Label = tk.Label(SettingsFrame, text='Gain: ', font=('TkDefaultFont', 12))
		Label.grid(row=Row, column =0, sticky='E')
		Label.config(bg=bgColor)
		entry = tk.Scale(SettingsFrame,variable=tk.DoubleVar(),from_=1, to =30, width=10, orient=HORIZONTAL,bg=bgColor)
		entry.grid(row=Row, column=1)
		entry.set(cam.Gain)
		entry.bind("<ButtonRelease-1>", lambda event, entry=entry: update_gain(entry))

	def add_Exposure(Row):
		def update_exposure(entry):
			new = int(entry.get())
			cam.ExposureTime = min(new, cam.get_info('ExposureTime')['max'])
			print('Exposure Time changed to: %.3f microseconds' % (cam.ExposureTime))
		Label = tk.Label(SettingsFrame, text='Exposure (us): ', font=('TkDefaultFont', 12))
		Label.grid(row=Row, column=0, sticky='E')
		Label.config(bg=bgColor)
		entry = tk.Scale(SettingsFrame,variable=tk.DoubleVar(),from_=1, to =26262, width=10, orient=HORIZONTAL,bg=bgColor)
		entry.set(cam.ExposureTime)
		entry.bind("<ButtonRelease-1>", lambda event, entry=entry: update_exposure(entry))
		entry.grid(row=Row, column=1)
	
	def _live():
		cam.stop()
		cam.AcquisitionMode = 'Continuous'
		cam.start()
		print('Ready')
		global running
		running = True
		if running:
			cam.AcquisitionMode = 'Continuous'
			global update_freq
			update_freq = 50
			update_im()

	def add_button_quit():
		button_quit = tk.Button(AcqFrame, text="Quit", command=_quit)
		button_quit.grid(row=3,column=0,padx=10,pady=10)

	def add_Delay():
		def update_Delay(entry):
			global Delay
			Delay = 0
			Delay = int(entry.get())
			print('Delay changed to: %.3f' % (Delay))
		label = Label(AcqFrame,text ='Capture delay (s):',bg=bgColor)
		label.grid(row=2,column=1,sticky='E')
		entry = tk.Scale(AcqFrame,variable=tk.DoubleVar(),from_=0, to =10, width=10, orient=HORIZONTAL,bg=bgColor)
		entry.grid(row=2,column=2,padx=10,pady=10)
		global Delay
		Delay = 0
		entry.set(Delay)
		entry.bind("<ButtonRelease-1>", lambda event, entry=entry: update_Delay(entry)) 

	def add_logo(Row):
		path = 'takulogo.png'
		logo = ImageTk.PhotoImage(Image.open(path))
		label = Label(SettingsFrame, image = logo, bg=bgColor, height=200)
		label.photo = logo
		label.grid(row=Row, sticky='N')

	def add_ImageFormat(Row):
		Label = tk.Label(SettingsFrame, text='Image Settings', font=('TkDefaultFont', 14, 'bold'))
		Label.grid(row=Row,column=0)
		Label.config(bg=bgColor)
		add_PixelFormat(Row+1)
		add_FrameRate(Row+2)
		add_Gain(Row+3)
		add_Exposure(Row+4)
		add_button_Live()

	def add_FileInfo():
		Label = tk.Label(FileFrame, text='File info', font=('TkDefaultFont', 14, 'bold'))
		Label.grid(row=0,column=0)
		Label.config(bg=bgColor)
		add_Station()
		add_Site()
		add_Depth()
		add_Direction()

	def add_Direction():
		directions = ['S','N','E','W']
		states = []
		x_checkbox = 2
		Label = tk.Label(FileFrame, text='Direction:', font=('TkDefaultFont', 12))
		Label.grid(row=4,column=0)
		Label.config(bg=bgColor)
		def _state():
			for s in states:
				if not s.get()=="off":
					global direction
					direction = s.get()
					print("Direction selected: "+direction)
		for dirr in directions:
			cvar = tk.StringVar()
			cvar.set("off")
			entry = tk.Checkbutton(FileFrame, text=dirr, bg='#f1faee', variable=cvar, onvalue=dirr, offvalue='off', command =_state )
			states.append(cvar)
			entry.grid(row=4,column=x_checkbox)
			entry.config(bg=bgColor)
			x_checkbox += 1
	def add_Station():
		global entry_station
		entry_station = tk.Spinbox(FileFrame,from_=0, to = 20, width=4)
		entry_station.grid(row=1, column=1, padx=10,pady=10)
		Label = tk.Label(FileFrame, text='Station:', font=('TkDefaultFont', 12))
		Label.grid(row=1,column=0)
		Label.config(bg=bgColor)

	def add_Site():
		global entry_site
		entry_site = tk.Spinbox(FileFrame,from_=0, to = 20, width=4)
		entry_site.grid(row=2, column=1, padx=10,pady=10)
		Label = tk.Label(FileFrame, text='Site:', font=('TkDefaultFont', 12))
		Label.grid(row=2,column=0, sticky='E')
		Label.config(bg=bgColor)

	def add_Depth():
		global entry_depth
		Label = tk.Label(FileFrame, text='Depth (cm):', font=('TkDefaultFont', 12))
		Label.grid(row=3,column=0, sticky='E')
		Label.config(bg=bgColor)
		entry_depth = tk.Entry(FileFrame,width=4)
		entry_depth.insert(0,'0')
		entry_depth.grid(row=3, column=1, padx=10,pady=10)

	def add_Acquisition():
		Label = tk.Label(AcqFrame, text='Acquisition', font=('TkDefaultFont', 14, 'bold'))
		Label.grid(row=0,column=0, sticky='E')
		Label.config(bg=bgColor)
		add_LED()
		add_Delay()
	
	def add_LED():
		def on_combobox_change(event):
			selected_value = entry.get()
			if selected_value == 'Fluo':
				illumination.send_command('Fluo')
			elif selected_value == 'Close':
				illumination.send_command('Close')
			else:
				illumination.send_command('Default')

    
		def Acquire():
			#try:
				illumination_type = entry.get()
				if illumination_type == 'Oblique':
					directions = ['Up', 'Down', 'Right', 'Left']
					for direction in directions:
						illumination.send_command(direction)
						time.sleep(1)
						_save(direction)
				else:
					illumination.send_command(illumination_type)
					threading.Timer(Delay, _save, args=(illumination_type,)).start()
			#except:
				#print('Live not started')

		Label = tk.Label(AcqFrame, text='Illumination Type: ', font=('TkDefaultFont', 12))
		Label.grid(row=1, column=0, sticky='E')
		Label.config(bg=bgColor)
		entry = ttk.Combobox(AcqFrame, state='readonly', width=10)
		entry['values'] = ('Oblique', 'Fluo', 'Close')
		entry.current(0)
		entry.grid(row=1, column=1)
		entry.bind('<<ComboboxSelected>>', on_combobox_change)
		button = tk.Button(AcqFrame, text='Start acquisition', command=lambda: threading.Timer(Delay, Acquire).start())
		button.grid(row=1, column=2)
	def add_consol():
		console = tk.Text(SettingsFrame, height=5, width=50, wrap="word")
		console.grid(row=1,column=0, columnspan=2, padx=10)
		sys.stdout = RedirectText(console)
		sys.stderr = RedirectText(console)
	def add_LiveView():
		fig = Figure(facecolor=bgColor)
		ax = fig.add_subplot(111)
		ax.axis('off')
		ax.set_facecolor(bgColor)
		pixel = 3.45/20
		scalebar = ScaleBar(pixel, "um", length_fraction=0.1, location = 'lower right',box_alpha=0.5)
		ax.add_artist(scalebar)
		fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
		global im
		image = cam.get_array()
		im = ax.imshow(image) 
		global canvas
		canvas = FigureCanvasTkAgg(fig,imageFrame) 
		canvas.get_tk_widget().configure(borderwidth=0, highlightthickness=0)
		canvas.get_tk_widget().grid(row=0, column=0, padx=100, pady=0)
		canvas.draw()
	acquiring = False
	def update_im():
		if running: 
			global image
			image = cam.get_array()
			im.set_data(image)
			canvas.draw()
			imageFrame.after(update_freq, update_im)

	def _quit():
		illumination.send_command('Close')
		window.quit()     
		window.destroy()  
	def _save(Illum_type):
		global folder, subfolder, directory, depth
		depth = str(entry_depth.get())
		folder = str(entry_station.get())
		subfolder = str(entry_site.get())
		directory = ('Station'+folder+'/'+'Site'+subfolder+'/')
		isExist = os.path.exists(directory)
		if not isExist:
			os.makedirs(directory)
			print(f'Directory created: {directory}')
		i = 0
		filename = directory+'/'+depth+'cm_'+Illum_type+'_'+str(i)+'.tif'
		while os.path.exists(filename):
			i += 1
			filename = directory+depth+'cm_'+Illum_type+'_'+direction+'_'+str(i)+'.tif'
		save_im = Image.fromarray(image)
		metadata = "I recorded this image on Mars"
		save_im.save(filename, pnginfo=metadata)
		print(f'Image saved as {filename}')
		



	initializeCam(Camera())
	CreateGUI()
	add_button_quit()
	add_ImageFormat(2)
	add_FileInfo()
	add_Acquisition()
	add_logo(0)
	cam.start()
	add_consol()
	add_LiveView()
	tk.mainloop()
	cam.stop()

