# Convolutional Neural Network on Starcraft II

## Setup

Run the AI on windows to collect the data, to train and test use ubuntu (virtual machine on paperspace)

## on windows

Generate the train data running `get_data.py` or download 1200 game data against hard ai [here](https://drive.google.com/file/d/1cO0BmbUhE2HsUC5ttQrLQC_wLTdCn2-u/view) (recommended)

```sh
pip install -r requirements.txt

mkdir train_data

python3 get_data.py
```

### ubuntu 16.04

- python 3.5
- pip 10.0.1
- anaconda

```sh
conda install -c anaconda tensorflow-gpu

pip3 install -r requirements.txt

python3 train.py
```

>if u installed starcraft in another directory, u'll need to remeber to change it in "C:\Users\USER_NAME\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\sc2\path.py" or add this line to your code:'os.environ["SC2PATH"] = 'E:\Program Files (x86)\StarCraft II'

> this sc2 fork has the method on_end: https://github.com/daniel-kukiela/python-sc2 download it and save the sc2 folder in your project directory

>download some maps here https://github.com/Blizzard/s2client-proto#map-packs

>open-cv is kinda hard to install on windows, see this tutorial: https://pythonprogramming.net/loading-images-python-opencv-tutorial/

>a lot of functions here are in "C:\Users\USER_NAME\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\sc2\bot_ai.py"

>https://drive.google.com/file/d/1cO0BmbUhE2HsUC5ttQrLQC_wLTdCn2-u/view 1280 game data vs hard ai
