import scipy
from scipy import ndimage
import skimage
import imageio
import matplotlib.pyplot as plt
import numpy as np
import PIL
from PIL import Image
import cv2
import SimpleITK as sitk
import os.path


class CassetteCropper():
    def __init__(self):
        self.img_size = (int(1280/2), int(960/2))
        

    def set_images(self, sample, template):
        tmp = sample
        tmp = tmp.resize(self.img_size, PIL.Image.ANTIALIAS)
        tmp = np.array(tmp)
        tmp = ndimage.median_filter(tmp, 5)
        self.sample = np.array(tmp)

        tmp = template
        tmp = tmp.resize(self.img_size, PIL.Image.ANTIALIAS)
        tmp = np.array(tmp)
        tmp = ndimage.median_filter(tmp, 5)
        self.template = np.array(tmp)

    def _sobel_filters(self, img):
        Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
        Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], np.float32)
        
        Ix = ndimage.filters.convolve(img, Kx)
        Iy = ndimage.filters.convolve(img, Ky)
        
        G = np.hypot(Ix, Iy)
        G = G / G.max() * 255
        theta = np.arctan2(Iy, Ix)
        
        return (G, theta)

    def crop(self):
        sample_closed =  self._create_closed_image(self.sample)
        template_path = '/tmp/template_closed.png'
        if os.path.isfile(template_path):
            template_closed = imageio.imread(template_path).astype(np.bool)
        else:
            template_closed = self._create_closed_image(self.template)
            imageio.imwrite(template_path, template_closed.astype(np.uint8) * 255)
        sample_registered = self._register_to_template(template_closed, sample_closed)
        return self._crop_to_box(sample_registered)
        

    def _create_closed_image(self, img):
        img_blur = ndimage.gaussian_filter(img, sigma=1)
        th = np.quantile(img_blur, 0.9)
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

    def _register_to_template(self, template_closed, sample_closed):
        fixed = sitk.GetImageFromArray(template_closed.astype(np.float) * 255)
        fixed = sitk.DiscreteGaussian(fixed, 2.0)

        moving = sitk.GetImageFromArray(sample_closed.astype(np.float) * 255)
        moving = sitk.DiscreteGaussian(moving, 2.0)
        
        R = sitk.ImageRegistrationMethod()
        R.SetMetricAsMeanSquares()
        sample_per_axis=100
        tx = sitk.Euler2DTransform()
        # Set the number of samples (radius) in each dimension, with a
        # default step size of 1.0
        R.SetOptimizerAsExhaustive([sample_per_axis//2,0,0])
        # Utilize the scale to set the step size for each dimension
        R.SetOptimizerScales([2.0*np.pi/sample_per_axis, 1.0,1.0])

        # Initialize the transform with a translation and the center of
        # rotation from the moments of intensity.
        tx = sitk.CenteredTransformInitializer(fixed, moving, tx)
        R.SetInitialTransform(tx)
        R.SetInterpolator(sitk.sitkLinear)
        R.AddCommand( sitk.sitkIterationEvent, lambda: self._command_iteration(R) )
        outTx = R.Execute(fixed, moving)
        return self._transform_sample(outTx, fixed)

    def _transform_sample(self, outTx, fixed):
        moving = sitk.GetImageFromArray(self.sample)
        moving = sitk.Normalize(moving)
        moving = sitk.DiscreteGaussian(moving, 2.0)
        resampler = sitk.ResampleImageFilter()
        resampler.SetReferenceImage(fixed)
        resampler.SetInterpolator(sitk.sitkLinear)
        resampler.SetDefaultPixelValue(1)
        resampler.SetTransform(outTx)
        out = resampler.Execute(moving)
        simg2 = sitk.Cast(sitk.RescaleIntensity(out), sitk.sitkUInt8)
        sample_registered = sitk.GetArrayFromImage(simg2)

        # simg1 = sitk.Cast(sitk.RescaleIntensity(fixed), sitk.sitkUInt8)
        # simg2 = sitk.Cast(sitk.RescaleIntensity(out), sitk.sitkUInt8)        
        # cimg = sitk.Compose(simg1, simg2, simg1//2.+simg2//2.)
        # plt.imshow(sitk.GetArrayFromImage(cimg))
        # plt.show()
        return sample_registered

    def _crop_to_box(self, sample_registered):
        # cropping mask based on the template image
        x1 = 270/2; x2 = 900/2; y1 = 360/2; y2 = 500/2
        sample_cropped = sample_registered[int(y1):int(y2), int(x1):int(x2)]
        return sample_cropped