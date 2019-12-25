import scipy
from scipy import ndimage
import skimage
import imageio
import matplotlib.pyplot as plt
import numpy as np
import PIL
from PIL import Image
import cv2
# import SimpleITK as sitk
import os.path
import imreg_dft as ird

from scipy.signal import find_peaks

class CassetteCropper():
    def __init__(self):
        self.img_size = (int(1280/2), int(960/2))

        self.CASSETTE_WIDTH = 1240/2
        self.CASSETTE_HEIGHT = 300/2
        

    def set_images(self, sample):
        tmp = sample
        tmp = tmp.resize(self.img_size, PIL.Image.ANTIALIAS)
        tmp = np.array(tmp)
        tmp = ndimage.median_filter(tmp, 5)
        self.sample = np.array(tmp)

    def _sobel_filters(self, img):
        Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
        Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], np.float32)
        
        Ix = ndimage.filters.convolve(img, Kx)
        Iy = ndimage.filters.convolve(img, Ky)
        
        G = np.hypot(Ix, Iy)
        G = G / G.max() * 255
        theta = np.arctan2(Iy, Ix)
        
        return (G, theta)

    def crop(self, use_registration=False):
        if not use_registration:
            cassette = self.crop_translation_only()
            if cassette is not None:
                return cassette
        '''
        if we didn't find the cassette with first method 
        or use_registration=true 
        continue with registration
        '''
        print('preprocessing sample image')
        sample_closed =  self._create_closed_image(self.sample)
        template_path = '/tmp/template_closed.png'
        template_closed = imageio.imread(template_path).astype(np.bool)
        sample_registered = self._register_to_template_2(template_closed, sample_closed)
        return self._crop_to_box(sample_registered)
        
    def crop_translation_only(self):
        # calculate the median over horizontal lines
        avg = np.mean(self.sample, axis=1)
        v_center = self._find_main_peak(avg)
        h_center = self.img_size[0]/2
        # avg = np.mean(self.sample, axis=0)
        # h_center = self._find_main_peak(avg)
        if not h_center or not v_center:
            return None
        print(h_center, v_center)
        cassette = self._crop_cassette_with_center(h_center, v_center)
        return cassette
        
    def _crop_cassette_with_center(self, h_center, v_center):
        h_index = [int(h_center - self.CASSETTE_WIDTH/2), int(h_center + self.CASSETTE_WIDTH/2)]
        if h_index[0] < 0:
            h_index[0] = 0
            h_index[1] = self.CASSETTE_WIDTH
        elif h_index[1] >= self.img_size[0]:
            h_index[1] = self.img_size[0] - 1
            h_index[0] = self.img_size[0] - self.CASSETTE_WIDTH - 1
        h_index = self._check_index(h_center, self.CASSETTE_WIDTH, self.img_size[0])
        v_index = self._check_index(v_center, self.CASSETTE_HEIGHT, self.img_size[1])
        cassette = self.sample[v_index[0]:v_index[1], h_index[0]:h_index[1]]
        return cassette

    def _check_index(self, center, size, img_size):
        h_index = [int(center) - size/2, int(center) + size/2 - 1]
        if h_index[0] < 0:
            h_index[0] = 0
            h_index[1] = size
        elif h_index[1] >= img_size:
            h_index[1] = img_size - 1
            h_index[0] = img_size - size - 1
        return [int(h_index[0]), int(h_index[1])]

    def _find_main_peak(self, avg, min_width = 100):
        peaks_loc, properties = find_peaks(avg, height=0, prominence=20, width=min_width, distance=30)
        if len(peaks_loc) == 1:
            return int((properties['left_ips'][0] + properties['right_ips'][0])/2)
        elif len(peaks_loc) == 0:
            return None
        else:            
            main_loc = None
            main_height = 0
            for i, (peaks_loc) in enumerate(peaks_loc):
                if properties['peak_heights'][i] > main_height:
                    main_loc = int((properties['left_ips'][i] + properties['right_ips'][i])/2)
                    main_height = properties['peak_heights'][i]
            return main_loc

    def _create_closed_image(self, img):
        img_blur = ndimage.gaussian_filter(img, sigma=1)
        th = np.quantile(img_blur, 0.6)
        img_threshold = np.where(img_blur > th, img_blur - th, 0)
        (img_sobel, _) = self._sobel_filters(img_threshold.astype(np.float32))

        edge_threshold = 10
        _,thresh = cv2.threshold(img_sobel.astype(np.uint8),edge_threshold,255,0)

        morph_box_size = [50, 100]
        return ndimage.morphology.binary_closing(thresh, 
                                    np.ones(morph_box_size), iterations=2)
    

    def _command_iteration(self, method) :
        print("{0:3} = {1:7.5f} : {2}".format(method.GetOptimizerIteration(),
                                           method.GetMetricValue(),
                                           method.GetOptimizerPosition()))

    
    def _register_to_template_2(self, template_closed, sample_closed):
        # fixed = sitk.GetImageFromArray(template_closed.astype(np.float) * 255)
        # fixed = sitk.DiscreteGaussian(fixed, 2.0)

        # moving = sitk.GetImageFromArray(sample_closed.astype(np.float) * 255)
        # moving = sitk.DiscreteGaussian(moving, 2.0)
        im0 = template_closed.astype(np.uint8)
        im1 = sample_closed.astype(np.uint8)
        # using imreg_dft 
        # result = ird.similarity(im0, im1, numiter=2, constraints=None)
        constraints = {}
        constraints['scale'] = [1,0.0]
        # result = ird.similarity(im0, im1, numiter=2, constraints=constraints)

        constraints['angle'] = [0,1]
        constraints['tx'] = [0,5]
        constraints['ty'] = [0,5]
        result = ird.similarity(im0, im1, numiter=2, constraints=constraints)

        assert "timg" in result
        # Maybe we don't want to show plots all the time
        # if os.environ.get("IMSHOW", "yes") == "yes":
        #     import matplotlib.pyplot as plt
        #     ird.imshow(im0, im1, result['timg'])
        #     plt.show()
        return self._transform_sample_2(result)

    def _transform_sample_2(self, result):
        sample_registered = ird.imreg.transform_img(self.sample, scale=result['scale'], angle=result['angle'], tvec=result['tvec'])
        sample_registered = sample_registered.astype(np.uint8)

        return sample_registered

    def _crop_to_box(self, sample_registered):
        # cropping mask based on the template image
        # x1 = 270/2; x2 = 900/2; y1 = 360/2; y2 = 520/2
        # x1 = 200/2; x2 = 1400/2; y1 = 400/2; y2 = 800/2
        x1 = 10/2; x2 = 1240/2; y1 = 360/2; y2 = 660/2
        sample_cropped = sample_registered[int(y1):int(y2), int(x1):int(x2)]
        return sample_cropped