# Bactrace cassette reader

## Requirements
use `requirements.txt` to install python libraries. this code was tested on `python3` so please use the same version. This code will run on UNIX (Linux, MacOS) since it needs to store file at `/tmp` folder.
```
pip install -r requirements.txt
```

## Usage
`4_Pos_low Inflammation.tiff` was used as the template image. Pass the address of the sample image and template using `-s` and `-t` respectively. default values would be `/tmp/sample.tiff` and `/tmp/template.tiff` if not provided in the arguments. type `python3 bactrace.py -h` for help. sample usage:
```
python3 bactrace.py -s data/samples/10_Pos_Inflammation_Low\ bact.tiff -t data/samples/4_Pos_low\ Inflammation.tiff
```
