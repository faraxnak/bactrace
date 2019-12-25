# Sample reading process

reading lines consists of two parts:
1. finding the bounding box of the cassette in the image
2. detecting and measuring the lines

## finding the bounding box
to find the bouding box, two methods were developed. first one assumes only translational movements between different images and is fast. The second one, accounts for the rotational movements, too and it is slower in comparison.

### common preprocess:
    1.  denoise image using median filter
    2.  blur image using gaussian kernel

### translation only:
    1.  average over image rows
    2.  find the main peak location and width of averaged signal
        - filter out other peaks if any found (because of outliers and/or incomplete isolation while taking the image)
    3.  use the pre-set width of the cassette to define the row start and end indices in the image
    4.  crop the image based on the found indices

### rotation and translation:
    1.  make image binary by thresholding
    2.  fill the cassette box using morphological operations (closing and opening)
    4.  create registration optimizer with constraints on scale, rotation and translation
    3.  register the binary image to the predefined template
    4.  crop the cassette based on the preknown coordinates on the template

## detecting and measuring the lines
for detection, the same approach of finding the peaks is used.

    1.  use median over columns to get a 1-D signal
    2.  find the peaks with proper constraints such as the minimum width, minimum distance between them and the minimum distance between the start and end of the cassette
    3.  find the peak representing the control line (should be present in all samples)
        - if control line is not detected, print warning for this sample and move to next one
    4.  read the lines for first, second and third marker if found
    5.  calculate noise effect by averaging over the cassette with found markers excluded
    6.  set the intensity of each marker to the median of the pixels found by the peak detection minus the noise effect
    7.  draw each peak start and end line on the image
    8.  save the processed cassette image and the data extracted from in results folder
    9.  move to next image (wait if nothing is found)
