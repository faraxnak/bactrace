from tkinter import Tk, Entry, mainloop, PhotoImage, Canvas, NW, Label, StringVar, CENTER
import imageio
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from argparse import ArgumentParser
import argparse
import os.path
import sys
import csv
import datetime, shutil
from CassetteCropper import CassetteCropper
from MarkerReader import MarkerReader

class ResultViewer():
    def __init__(self):
        self.window = None

    def create_window(self, title, cropped_sample, marked_image, markers_data, markers_p_value):        
        ## generate window
        window = Tk()
        window.title("Bactrace")

        self.title_stringVars = StringVar()
        self.title_stringVars.set("Result for sample at {}".format(title))
        self.title_label = Label(window, textvariable = self.title_stringVars)
        self.title_label.grid(row = 0)
        w = 700
        h = 200
        self.canvas_orig = Canvas(window, width = w, height = h)        
        self.img_orig = ImageTk.PhotoImage(image=Image.fromarray(np.array(cropped_sample)))     
        self.img_viewer_orig = self.canvas_orig.create_image(20,20, anchor=NW, image=self.img_orig)
        self.canvas_orig.grid(row=1)

        self.canvas = Canvas(window, width = w, height = h)        
        self.img = ImageTk.PhotoImage(image=Image.fromarray(np.array(marked_image)))     
        self.img_viewer = self.canvas.create_image(20,20, anchor=NW, image=self.img)
        self.canvas.grid(row=2)

        self.table_canvas = Canvas(window, width = 400, height = 200)
        self.table_canvas.grid(row=3)
        self.height = 5
        self.width = 5    
        # self.labels = []    
        self.stringVars = []
        for i in range(self.height):  # Rows
            texts, fg = self.getTextForRow(i, markers_data, markers_p_value)
            rows = []
            for j in range(self.width):  # Columns
                v = StringVar()                
                rows.append(v)
                b = Label(self.table_canvas, textvariable=v, fg = fg)
                # b.pack()                
                b.grid(row=i, column=j)                                
                v.set(texts[j])
            self.stringVars.append(rows)
        self.window = window            
        return window
    def update(self, title, cropped_sample, marked_image, markers_data, markers_p_value):              
        self.title_stringVars.set("Result for sample at {}".format(title))
        self.img_orig = ImageTk.PhotoImage(image=Image.fromarray(np.array(cropped_sample)))
        self.canvas_orig.itemconfig(self.img_viewer_orig, image = self.img_orig)
        self.img = ImageTk.PhotoImage(image=Image.fromarray(np.array(marked_image)))
        self.canvas.itemconfig(self.img_viewer, image = self.img)
        for i in range(self.height):  # Rows
            texts, _ = self.getTextForRow(i, markers_data, markers_p_value)
            for j in range(self.width):  # Columns
                self.stringVars[i][j].set(texts[j])
        pass

    def getTextForRow(self, i, markers_data, markers_p_value):
        fg = "black"
        if i == 0:
            texts = ['Type' ,'Intensity', 'P_Value', 'Ratio', 'Decision']
        elif i == 1:
            texts = ['Control', '{}'.format(markers_data[0]), '{}'.format(markers_p_value[0]), '1', '']
            fg = "purple"
        elif i == 2:
            texts = ['Test 1', '{}'.format(markers_data[1]), '{}'.format(markers_p_value[1]), '{:.2f}'.format(markers_data[1]/markers_data[0]) ,'']
            fg = "red"
        elif i == 3:
            texts = ['Test 2', '{}'.format(markers_data[2]), '{}'.format(markers_p_value[2]), '{:.2f}'.format(markers_data[2]/markers_data[0]) ,'']
            fg = "orange"
        elif i == 4:
            texts = ['Test 3', '{}'.format(markers_data[3]), '{}'.format(markers_p_value[3]), '{:.2f}'.format(markers_data[3]/markers_data[0]) ,'']
            fg = "cyan4"
        return texts, fg

def readImages(can_be_empty = False):
    samples = []
    filenames = []
    source_pathes = []
    if reading_from_folder == True:
        for file in os.listdir(args.sample_dir):
            if file.endswith(".tiff"):
                filename = args.sample_dir + file
                samples.append(Image.open(filename).convert('L'))
                filenames.append(file)
                source_pathes.append(args.sample_dir + file)
        if len(samples) == 0:
            if not can_be_empty:
                sys.exit('Did not find any tiff images in {}'.format(args.sample_dir))
    else:
        source_pathes.append(args.sample_path)
        filenames = [args.sample_path.split("/")[-1]]
        samples.append(Image.open(args.sample_path).convert('L'))
    return samples, filenames, source_pathes

def process_images(samples, filenames):
    cropped_images = []
    marked_images = []
    markers_data_list = []
    markers_p_value_list = []
    cropper = CassetteCropper()
    markerReader = MarkerReader()
    for sample, filename in zip(samples, filenames):    
        print('started processing {}'.format(filename))
        cropper.set_images(sample)
        cropped_sample = cropper.crop(use_registration=args.use_registration)
        cropped_images.append(cropped_sample)    
        marked_image, markers_data, markers_p_value = markerReader.read_markers(cropped_sample)
        marked_images.append(marked_image)
        markers_data_list.append(markers_data)
        markers_p_value_list.append(markers_p_value)
    return cropped_images, marked_images, markers_data_list, markers_p_value_list

"""
Saving result (CSV and processed image)
"""
def save_resutls(cropped_images, marked_images, markers_data_list,
                 markers_p_value_list, filenames, source_pathes,
                 input_folder, cropped_folder, marked_folder, current_run_folder):
    header = ['Filename', 'Control Intensity', 
            'Test 1 Intensity', 'P_Value', 'Ratio', 
            'Test 2 Intensity', 'P_Value', 'Ratio',
            'Test 3 Intensity', 'P_Value', 'Ratio']
    csv_file_path = current_run_folder + '/output.csv'
    if not os.path.isfile(csv_file_path):
        with open(csv_file_path, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(header)
            csvFile.close()
    with open(csv_file_path, 'a+') as csvFile:
        writer = csv.writer(csvFile)
        for filename, markers_data, markers_p_value in zip(filenames, markers_data_list, markers_p_value_list):
            r1 = '{:.2f}'.format(markers_data[1]/markers_data[0])
            r2 = '{:.2f}'.format(markers_data[2]/markers_data[0])
            r3 = '{:.2f}'.format(markers_data[3]/markers_data[0])
            row = ([filename, 
                    '{}'.format(markers_data[0]), 
                    '{}'.format(markers_data[1]), 
                    '{}'.format(markers_p_value[1]), 
                    r1,
                    '{}'.format(markers_data[2]),
                    '{}'.format(markers_p_value[2]), 
                    r2,
                    '{}'.format(markers_data[3]),
                    '{}'.format(markers_p_value[3]), 
                    r3])
            writer.writerow(row)
        csvFile.close()

    for source_path, filename in zip(source_pathes, filenames):
        if os.path.isfile(source_path):
            os.rename(source_path, input_folder + filename) 
    
    for filename, cropped_image, marked_image in zip(filenames, cropped_images, marked_images):
        image = Image.fromarray((cropped_image).astype(np.uint8))
        image.save(cropped_folder + filename)
        image = Image.fromarray((marked_image).astype(np.uint8))
        image.save(marked_folder + filename)


def create_folders():
    results_folder = "/tmp/results/"
    if not os.path.isdir(results_folder):
        os.mkdir(results_folder)

    current_run_folder = results_folder + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if not os.path.isdir(current_run_folder):
        os.mkdir(current_run_folder)
    
    input_folder = current_run_folder + "/input/"
    os.mkdir(input_folder)
    cropped_folder = current_run_folder + "/cropped/"
    os.mkdir(cropped_folder)
    marked_folder = current_run_folder + "/processed/"
    os.mkdir(marked_folder)

    return current_run_folder, input_folder, cropped_folder, marked_folder

def check():    
    samples, filenames, source_pathes = readImages(can_be_empty=True)    
    if len(samples) > 0:
        cropped_images, marked_images, markers_data_list, markers_p_value_list = process_images(samples, filenames)
        save_resutls(cropped_images, marked_images, markers_data_list, 
                    markers_p_value_list, filenames, source_pathes,
                    input_folder, cropped_folder, marked_folder, current_run_folder)
        viewer.update(filenames[-1], cropped_images[-1], 
                        marked_images[-1], markers_data_list[-1], markers_p_value_list[-1])
        window.after(int(1e3), check)
    else:
        window.after(int(1e3), check)

def ctrl_c_check():
    window.after(10, ctrl_c_check)

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')



if __name__ == "__main__":
    """
    read arguments
    """
    parser = ArgumentParser()
    parser.add_argument("-s", "--sample", dest="sample_path",
                        help="sample path", metavar="FILE", default='/tmp/sample.tiff')
    parser.add_argument("-d", "--directory", dest = "sample_dir",
                        help="sample directory", metavar="DIR", default='/tmp/samples/')
    parser.add_argument("-t", "--template", dest="template_path",
                        help="template path", metavar="FILE", 
                        default= os.path.dirname(os.path.abspath(__file__)) + '/template_closed.png')
    parser.add_argument('--use_registration', type=str2bool,  default=False,
                        help='Only use registraton method for cropping the cassette (default: False)')
    args = parser.parse_args()

    """ 
    check input arguments
    """

    if os.path.isdir(args.sample_dir):
        reading_from_folder = True
        if not args.sample_dir.endswith('/'):
            args.sample_dir += "/"
    elif os.path.isfile(args.sample_path):
        reading_from_folder = False
    else:
        sys.exit('Can not find the sample image or sample directory')

    if os.path.isfile(args.template_path):
        shutil.copy(args.template_path, '/tmp/template_closed.png')
    else:
        sys.exit('Can not find the template image')

    samples, filenames, source_pathes = readImages()
    cropped_images, marked_images, markers_data_list, markers_p_value_list = process_images(samples, filenames)



    current_run_folder, input_folder, cropped_folder, marked_folder = create_folders() 
    save_resutls(cropped_images, marked_images, markers_data_list, 
                markers_p_value_list, filenames, source_pathes,
                input_folder, cropped_folder, marked_folder, current_run_folder)

    """
    Showing the result
    """
    viewer = ResultViewer()
    window = viewer.create_window(filenames[-1], cropped_images[-1], 
                            marked_images[-1], markers_data_list[-1], markers_p_value_list[-1])

    window.after(int(1e4), check)
    window.after(10, ctrl_c_check)
    try:
        window.mainloop()
    except KeyboardInterrupt:
            print('\nClosing the program')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
    