from CassetteCropper import CassetteCropper
from MarkerReader import MarkerReader
from tkinter import Tk, Entry, mainloop, PhotoImage, Canvas, NW, Label, StringVar, CENTER
import imageio
import matplotlib.pyplot as plt
import numpy as np
import PIL
from PIL import Image, ImageTk

template = Image.open('/Users/farid/Documents/Workspace/python/bactrace/data/samples/4_Pos_low Inflammation.tiff')
# sample_name = '6_Pos_Inflammation.tiff'
# sample_name = '3_Pos_Inflammation.tiff'
sample_name = '5_Pos_low Inflammation.tiff'
# sample_name = '7_neg.tiff'
# sample_name = '8_Pos_Inflammation_suboptimal run.tiff'
sample = Image.open('/Users/farid/Documents/Workspace/python/bactrace/data/samples/' + sample_name)

cropper = CassetteCropper()
cropper.set_images(sample, template)
cropped_sample = cropper.crop()
markerReader = MarkerReader()
marked_image, markers_data = markerReader.read_markers(cropped_sample)

window = Tk()
window.title("GUI")

Label(window, text = "Image").grid(row = 0) # this is placed in 0 0
canvas = Canvas(window, width = 400, height = 200)
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
        texts = ['Type' ,'Intensity', 'Confidence', 'Ratio', 'Decision']
    elif i == 1:
        texts = ['Control', '{}'.format(markers_data[0]), '', '1', '']
    elif i == 2:
        texts = ['Test 1', '{}'.format(markers_data[1]), '', '{:.2f}'.format(markers_data[1]/markers_data[0]) ,'']
    elif i == 3:
        texts = ['Test 2', '{}'.format(markers_data[2]), '', '{:.2f}'.format(markers_data[2]/markers_data[0]) ,'']

    for j in range(width):  # Columns
        # text_var = StringVar()
        # # here we are setting cell text value
        # text_var.set('%s%s' % (i, j)) 
        b = Label(table_canvas, text=texts[j])
        b.grid(row=i, column=j)


window.mainloop()
# plt.figure()
# plt.imshow(cropped_sample)
# plt.show()