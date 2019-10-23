from scipy.signal import find_peaks
from scipy import stats
import numpy as np
import sys
import matplotlib.pyplot as plt
import cv2

class MarkerReader():
    def __init__(self):
        pass

    def _find_margins(self, sample_cropped, bin_width = 2):
        sample_size = sample_cropped.shape
        sampling_loc = np.arange(bin_width/2, sample_size[1]-bin_width/2, bin_width).astype(int)
        sample_median = np.zeros(len(sampling_loc))
        for i, loc in enumerate(sampling_loc):
            sample_median[i] = np.median(sample_cropped[:,loc - int(bin_width/2) : loc + int(bin_width/2)-1])            
        peaks_loc, properties = find_peaks(sample_median, height=0, prominence=10, width=(5, 40), distance=10)
        start_margin = 30
        end_margin = 30
        if len(peaks_loc) > 1:
            if properties['left_ips'][0] * bin_width < start_margin:
                start_margin = np.max([start_margin, int(properties['right_ips'][0] * bin_width) + 5])
            if properties['right_ips'][-1] * bin_width > (sample_size[1] - start_margin):
                end_margin = np.max([end_margin, sample_size[1] - int(properties['left_ips'][-1] * bin_width) + 5])
        return start_margin, end_margin

    def read_markers(self, sample_cropped):
        bin_width = 2
        # start_margin = 30
        # end_margin = 30
        start_margin, end_margin = self._find_margins(sample_cropped, bin_width=bin_width)
        sample_size = sample_cropped.shape
        sampling_loc = np.arange(bin_width/2 + start_margin, sample_size[1]-end_margin, bin_width).astype(int)
        sample_median = np.zeros(len(sampling_loc))
        for i, loc in enumerate(sampling_loc):
            sample_median[i] = np.median(sample_cropped[:,loc - int(bin_width/2) : loc + int(bin_width/2)-1])            
        
        peaks_loc, properties = find_peaks(sample_median, height=0, prominence=10, width=(5, 40), distance=10)
        noise_level, noise_std = self._find_noise_level(sample_median, properties)
        
        # if len(peaks_loc) > 1:
        #     if properties['left_ips'][0] < start_margin:
        #         start_margin = properties['right_ips'][0]
        #     if properties['right_ips'][-1] > (sample_size[1] - start_margin):
        #         end_margin = sample_size[1] - properties['right_ips'][-1]

        sample_cropped_marked_boxes = cv2.cvtColor(sample_cropped ,cv2.COLOR_GRAY2RGB)
        if len(peaks_loc) > 1:
            control_loc = peaks_loc[-1]
            control_val = properties['peak_heights'][-2] - noise_level
            sample_cropped_marked_boxes = self._draw_box_border(sample_cropped_marked_boxes,
                                                    int(properties['left_ips'][-2]) * bin_width + start_margin,
                                                    int(properties['right_ips'][-2]) * bin_width + start_margin,
                                                    "black")
            control_val = properties['peak_heights'][-2] - noise_level
            sample_cropped_marked_boxes = self._draw_box_border(sample_cropped_marked_boxes,
                                                    int(properties['left_ips'][-1]) * bin_width + start_margin,
                                                    int(properties['right_ips'][-1]) * bin_width + start_margin,
                                                    "white")
        else:
            sys.exit('Failed to find the locations')

        # sample_cropped_marked_boxes = cv2.cvtColor(sample_cropped_marked_boxes ,cv2.COLOR_GRAY2RGB)
        test_1_val = None
        test_2_val = None
        if len(peaks_loc) > 2:
            test_1_loc = peaks_loc[0]
            test_1_val = properties['peak_heights'][0] - noise_level
            sample_cropped_marked_boxes = self._draw_box_border(sample_cropped_marked_boxes,
                                                    int(properties['left_ips'][0]) * bin_width + start_margin,
                                                    int(properties['right_ips'][0]) * bin_width + start_margin,
                                                    "red")
        if len(peaks_loc) > 3:
            test_2_loc = peaks_loc[1]
            test_2_val = properties['peak_heights'][1] - noise_level
            sample_cropped_marked_boxes = self._draw_box_border(sample_cropped_marked_boxes,
                                                    int(properties['left_ips'][1]) * bin_width + start_margin,
                                                    int(properties['right_ips'][1]) * bin_width + start_margin,
                                                    "orange")
        if len(peaks_loc) > 4:
            for i in np.arange(2,len(peaks_loc)-2, step=1):
                sample_cropped_marked_boxes = self._draw_box_border(sample_cropped_marked_boxes,
                                                        int(properties['left_ips'][i]) * bin_width + start_margin,
                                                        int(properties['right_ips'][i]) * bin_width + start_margin,
                                                        "cyan")

        if test_1_val is not None:
            print(test_1_val/control_val)
            z_score = test_1_val/noise_std    
            p_value_1 = stats.norm.sf(abs(z_score))
        else:
            test_1_val = 0
            p_value_1 = 1
        if test_2_val is not None:
            print(test_2_val/control_val)
            z_score = test_2_val/noise_std    
            p_value_2 = stats.norm.sf(abs(z_score))
        else:
            test_2_val = 0
            p_value_2 = 1

        return sample_cropped_marked_boxes, (control_val, test_1_val, test_2_val), (0, p_value_1, p_value_2)
        
    def _draw_box_border(self, image, start, end, color):
        if color == "black":
            color_array = [128,0,128]
        elif color == "red":
            color_array = [255,0,0]
        elif color == "orange":
            color_array = [255,165,0]
        elif color == "white":
            color_array = [200,200,200]
        elif color == "cyan":
            color_array = [0,100,100]
        image[:,start:start+2,:] = color_array
        image[:,end:end+2,:] = color_array
        return image

    def _find_noise_level(self, signal, peaks_properties):
        for start, end in zip(peaks_properties['left_ips'], peaks_properties['right_ips']):
            signal[int(start):int(end)] = -1
        peak_extracted_singal = signal[np.where(signal != -1)]
        noise_level = np.median(peak_extracted_singal)
        thresholds = np.quantile(peak_extracted_singal, [0.1, 0.9])
        noise_std = np.std(peak_extracted_singal[
            np.where((peak_extracted_singal > thresholds[0]) & 
                    (peak_extracted_singal < thresholds[1]))])
        return noise_level, noise_std
