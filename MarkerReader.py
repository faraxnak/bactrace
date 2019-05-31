from scipy.signal import find_peaks
from scipy import stats
import numpy as np
import sys
import matplotlib.pyplot as plt


class MarkerReader():
    def __init__(self):
        pass

    def read_markers(self, sample_cropped):
        bin_width = 2
        start_margin = 30
        sample_size = sample_cropped.shape
        sampling_loc = np.arange(bin_width/2 + start_margin, sample_size[1]-bin_width/2, bin_width).astype(int)
        sample_median = np.zeros(len(sampling_loc))
        for i, loc in enumerate(sampling_loc):
            sample_median[i] = np.median(sample_cropped[:,loc - int(bin_width/2) : loc + int(bin_width/2)-1])            
        peaks_loc, properties = find_peaks(sample_median, height=np.quantile(sample_median, 0.5), width=5, distance=15)
        noise_level, noise_std = self._find_noise_level(sample_median, properties)
        
        test_1_val = None
        test_2_val = None
        if len(peaks_loc) > 2:
            test_1_loc = peaks_loc[0]
            test_1_val = properties['peak_heights'][0] - noise_level
        if len(peaks_loc) > 3:
            test_2_loc = peaks_loc[1]
            test_2_val = properties['peak_heights'][1] - noise_level
        if len(peaks_loc) > 1:
            control_loc = peaks_loc[-1]
            control_val = properties['peak_heights'][-2] - noise_level
        else:
            sys.exit('Failed to find the locations')

        if test_1_val is not None:
            print(test_1_val/control_val)
            z_score = test_1_val/noise_std    
            confidence_1 = stats.norm.sf(abs(z_score))
        else:
            test_1_val = 0
            confidence_1 = 1
        if test_2_val is not None:
            print(test_2_val/control_val)
            z_score = test_2_val/noise_std    
            confidence_2 = stats.norm.sf(abs(z_score))
        else:
            test_2_val = 0
            confidence_2 = 1

        sample_cropped_boxes = np.copy(sample_cropped)
        for loc, start, end in zip(peaks_loc, properties['left_ips'], properties['right_ips']):
            sample_cropped_boxes[:,int(start) * bin_width + start_margin] = 255
            sample_cropped_boxes[:,int(end) * bin_width + start_margin] = 255
        
        return sample_cropped_boxes, (control_val, test_1_val, test_2_val), (0, confidence_1, confidence_2)
        

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
