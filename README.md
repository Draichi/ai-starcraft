
>if u installed starcraft in another directory, u'll need to remeber to change it in "C:\Users\USER_NAME\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\sc2\path.py" or add this line to your code:'os.environ["SC2PATH"] = 'E:\Program Files (x86)\StarCraft II'

> this sc2 fork has the method on_end: https://github.com/daniel-kukiela/python-sc2 download it and save the sc2 folder in your project directory

>download some maps here https://github.com/Blizzard/s2client-proto#map-packs

>open-cv is kinda hard to install on windows, see this tutorial: https://pythonprogramming.net/loading-images-python-opencv-tutorial/

>a lot of functions here are in "C:\Users\USER_NAME\AppData\Local\Programs\Python\Python36-32\Lib\site-packages\sc2\bot_ai.py"

>https://drive.google.com/file/d/1cO0BmbUhE2HsUC5ttQrLQC_wLTdCn2-u/view 1280 game data vs hard ai

### windows

```sh
install anaconda
conda create -n tensorflow pip python=3.5 
activate tensorflow
pip install --ignore-installed --upgrade tensorflow-gpu 
pip install -r requirements.txt
```

### linux

```sh
conda install -c anaconda tensorflow-gpu 
activate tensorflow-gpu
```