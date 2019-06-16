from tkinter import Tk, Entry, mainloop, PhotoImage, Canvas, NW, Label, StringVar, CENTER
import imageio
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from argparse import ArgumentParser
import os.path
import sys
import csv
import datetime

from CassetteCropper import CassetteCropper
from MarkerReader import MarkerReader

parser = ArgumentParser()
parser.add_argument("-s", "--sample", dest="sample_path",
                    help="sample path", metavar="FILE", default='/tmp/sample.tiff')
parser.add_argument("-d", "--directory", dest = "sample_dir",
                    help="sample directory", metavar="DIR", default='/tmp/samples/')
parser.add_argument("-t", "--template", dest="template_path",
                    help="template path", metavar="FILE", default='/tmp/template.tiff')
args = parser.parse_args()


""" 
template image is: 
4_Pos_low Inflammation.tiff
"""

if os.path.isdir(args.sample_dir):
    reading_from_folder = True
    if not args.sample_dir.endswith('/'):
        args.sample_dir += "/"
elif os.path.isfile(args.sample_path):
    reading_from_folder = False
else:
    sys.exit('Can not find the sample image or sample directory')

if os.path.isfile(args.template_path) == False:
    sys.exit('Can not find the template image')
# if os.path.isfile(args.sample_path) == False:
#     sys.exit('Can not find the source image')

template = Image.open(args.template_path)
# sample_name = '6_Pos_Inflammation.tiff'
# sample_name = '3_Pos_Inflammation.tiff'
# sample_name = '5_Pos_low Inflammation.tiff'
# sample_name = '7_neg.tiff'
# sample_name = '8_Pos_Inflammation_suboptimal run.tiff'
# tmp2 = '/Users/farid/Documents/Workspace/python/bactrace/data/samples/' + sample_name
samples = []

filenames = []
if reading_from_folder == True:
    for file in os.listdir(args.sample_dir):
        if file.endswith(".tiff"):
            filename = args.sample_dir + file
            samples.append(Image.open(filename))
            filenames.append(file)
    if len(samples) == 0:
        sys.exit('Did not find any tiff images in {}'.format(args.sample_dir))
else:
    filenames = [args.sample_path.split("/")[-1]]
    samples.append(Image.open(args.sample_path))

cropped_images = []
marked_images = []
markers_data_list = []
markers_p_value_list = []
cropper = CassetteCropper()
markerReader = MarkerReader()
for sample in samples:    
    cropper.set_images(sample, template)
    cropped_sample = cropper.crop()
    cropped_images.append(cropped_sample)    
    marked_image, markers_data, markers_p_value = markerReader.read_markers(cropped_sample)
    marked_images.append(marked_image)
    markers_data_list.append(markers_data)
    markers_p_value_list.append(markers_p_value)

"""
Saving result (CSV and processed image)
"""

results_folder = "/tmp/results/"
if not os.path.isdir(results_folder):
    os.mkdir(results_folder)

current_run_folder = results_folder + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
if not os.path.isdir(current_run_folder):
    os.mkdir(current_run_folder)

header = ['Filename', 'Control Intensity', 'Test 1 Intensity', 'P_Value', 'Ratio',  'Test 2 Intensity', 'P_Value', 'Ratio']
with open(current_run_folder + '/output.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(header)
    for filename, markers_data, markers_p_value in zip(filenames, markers_data_list, markers_p_value_list):
        r1 = '{:.2f}'.format(markers_data[1]/markers_data[0])
        r2 = '{:.2f}'.format(markers_data[2]/markers_data[0])
        row = ([filename, 
                '{}'.format(markers_data[0]), 
                '{}'.format(markers_data[1]), 
                '{}'.format(markers_p_value[1]), 
                r1,
                '{}'.format(markers_data[2]),
                '{}'.format(markers_p_value[2]), 
                r2])
        writer.writerow(row)
    csvFile.close()

cropped_folder = current_run_folder + "/cropped/"
os.mkdir(cropped_folder)
marked_folder = current_run_folder + "/processed/"
os.mkdir(marked_folder)
for filename, cropped_image, marked_image in zip(filenames, cropped_images, marked_images):
    image = Image.fromarray((cropped_image).astype(np.uint8))
    image.save(cropped_folder + filename)
    image = Image.fromarray((marked_image).astype(np.uint8))
    image.save(marked_folder + filename)

"""
Showing the result
"""

window = Tk()
window.title("Bactrace")

Label(window, text = "Result for sample at {}".format(args.sample_path)).grid(row = 0) # this is placed in 0 0

canvas_orig = Canvas(window, width = 400, height = 100)
canvas_orig.grid(row=1)
img_orig = ImageTk.PhotoImage(image=Image.fromarray(np.array(cropped_sample)))     
img_viewer = canvas_orig.create_image(20,20, anchor=NW, image=img_orig) 

canvas = Canvas(window, width = 400, height = 100)
canvas.grid(row=2)
img = ImageTk.PhotoImage(image=Image.fromarray(np.array(marked_image)))     
img_viewer = canvas.create_image(20,20, anchor=NW, image=img) 

# canvas.place(relx=0.5, rely=0.5, anchor=CENTER)

table_canvas = Canvas(window, width = 400, height = 200)
table_canvas.grid(row=3)
height = 4
width = 5
for i in range(height):  # Rows
    fg = "black"
    if i == 0:
        texts = ['Type' ,'Intensity', 'P_Value', 'Ratio', 'Decision']
    elif i == 1:
        texts = ['Control', '{}'.format(markers_data[0]), '{}'.format(markers_p_value[0]), '1', '']
    elif i == 2:
        texts = ['Test 1', '{}'.format(markers_data[1]), '{}'.format(markers_p_value[1]), '{:.2f}'.format(markers_data[1]/markers_data[0]) ,'']
        fg = "red"
    elif i == 3:
        texts = ['Test 2', '{}'.format(markers_data[2]), '{}'.format(markers_p_value[2]), '{:.2f}'.format(markers_data[2]/markers_data[0]) ,'']
        fg = "green"

    for j in range(width):  # Columns
        b = Label(table_canvas, text=texts[j], fg = fg)
        b.grid(row=i, column=j)

def check():
    window.after(50, check)

window.after(50, check)
try:
    window.mainloop()
except KeyboardInterrupt:
        print('\nClosing the program')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
