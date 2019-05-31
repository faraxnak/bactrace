from tkinter import Tk, Entry, mainloop, PhotoImage, Canvas, NW, Label, StringVar, CENTER
import imageio
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from argparse import ArgumentParser
import os.path
import sys

from CassetteCropper import CassetteCropper
from MarkerReader import MarkerReader

parser = ArgumentParser()
parser.add_argument("-s", "--sample", dest="sample_path",
                    help="sample path", metavar="FILE", default='/tmp/sample.tiff')
parser.add_argument("-t", "--template", dest="template_path",
                    help="template path", metavar="FILE", default='/tmp/template.tiff')
args = parser.parse_args()


""" 
template image is: 
4_Pos_low Inflammation.tiff
"""


if os.path.isfile(args.template_path) == False:
    sys.exit('Can not find the template image')
if os.path.isfile(args.sample_path) == False:
    sys.exit('Can not find the source image')

template = Image.open(args.template_path)
# sample_name = '6_Pos_Inflammation.tiff'
# sample_name = '3_Pos_Inflammation.tiff'
# sample_name = '5_Pos_low Inflammation.tiff'
# sample_name = '7_neg.tiff'
# sample_name = '8_Pos_Inflammation_suboptimal run.tiff'
# tmp2 = '/Users/farid/Documents/Workspace/python/bactrace/data/samples/' + sample_name
sample = Image.open(args.sample_path)

cropper = CassetteCropper()
cropper.set_images(sample, template)
cropped_sample = cropper.crop()
markerReader = MarkerReader()
marked_image, markers_data, markers_p_value = markerReader.read_markers(cropped_sample)

window = Tk()
window.title("Bactrace")

Label(window, text = "Result for sample at {}".format(args.sample_path)).grid(row = 0) # this is placed in 0 0
canvas = Canvas(window, width = 400, height = 150)
canvas.grid(row=1)
img = ImageTk.PhotoImage(image=Image.fromarray(np.array(marked_image)))     
img_viewer = canvas.create_image(20,20, anchor=NW, image=img) 
# canvas.place(relx=0.5, rely=0.5, anchor=CENTER)

table_canvas = Canvas(window, width = 400, height = 200)
table_canvas.grid(row=2)
height = 4
width = 5
for i in range(height):  # Rows
    if i == 0:
        texts = ['Type' ,'Intensity', 'P_Value', 'Ratio', 'Decision']
    elif i == 1:
        texts = ['Control', '{}'.format(markers_data[0]), '{}'.format(markers_p_value[0]), '1', '']
    elif i == 2:
        texts = ['Test 1', '{}'.format(markers_data[1]), '{}'.format(markers_p_value[1]), '{:.2f}'.format(markers_data[1]/markers_data[0]) ,'']
    elif i == 3:
        texts = ['Test 2', '{}'.format(markers_data[2]), '{}'.format(markers_p_value[2]), '{:.2f}'.format(markers_data[2]/markers_data[0]) ,'']

    for j in range(width):  # Columns
        b = Label(table_canvas, text=texts[j])
        b.grid(row=i, column=j)


window.mainloop()
# plt.figure()
# plt.imshow(cropped_sample)
# plt.show()