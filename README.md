Overview
========

The goal of **carwatch** is to capture a video stream and detect cars waiting at the parking garage gate for it to close before leaving.

When a car is detected, **carwatch** will take a screenshot and save it into a JPG.

![Example Detection](./example_detection.jpg)

**Carwatch** also provides ability to create a weekly report and send it by email once a week with graph and screenshots attached in a zip file.

![Example Report](./example_report.png)

**Carwatch** is designed to capture a RTSP video stream and run on a Raspberry Pi.

Installation
============

Python libraries needed:
```
pip3 install opencv-python
pip3 install pytesseract
pip3 install matplotlib
pip3 install pandas
```

OpenCV install on Mac (for testing):
```
brew install opencv3
echo 'export PATH="/usr/local/opt/qt/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

After you clone the git repository, rename the file ``sample.app_config.py`` to ``app_config.py`` and edit the mail and RTSP configuration.
You may also tune other detection settings which might depend on your camera.

```
nohup python3 carwatch.py >> carwatch.log 2>&1
```
