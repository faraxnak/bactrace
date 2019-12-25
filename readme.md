# Bactrace cassette reader

## Requirements
use `requirements.txt` to install python libraries. this code was tested on `python3` so please use the same version. This code will run on UNIX (Linux, MacOS) since it needs to store file at `/tmp` folder.
```
pip install -r requirements.txt
```

## Usage
`4_Pos_low Inflammation.tiff` was used as the template image. User can pass these parameters to the program: 
- Path to template image for registration method using `-t` (default: `exec_file_directory` + `template_closed.png`)
- Path to sample image using `-s` (default: `/tmp/sample.tiff`)
- Directory containing sample images using `-d` (default: `/tmp/samples/`)
- Flag to choose the method for cropping the cassette: set `--use_registration` to `true` if you prefer to only use the registration method (slower but more accurate).

If the directory is passed as an argument or the default directory exists, the sample path will be ignored. Only `tiff` images are read from the directory.

If you pull from this repo, the template image should be in the correct path and there is no need to pass that argument.

sample usage:
```
python3 bactrace.py -s data/samples/10_Pos_Inflammation_Low bact.tiff
```
Or
```
python3 bactrace.py -d data/samples/
```
User can stop the program using `Ctrl-C` from terminal or by closing the results window.

## Results
The results will be saved to `/tmp/results/{Data_Time}` folder (e.g. `/tmp/results/2019-06-16_21-31-14/`). For each running the program, there will be a new folder containing the original cropped images, marked images and a csv file with the measurements for all the samples in sample directory (or one sample passed using the sample pass argument).
Measurements for the last image will be shown at the end.
