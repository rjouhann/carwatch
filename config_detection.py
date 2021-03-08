# Clear the buffer stack every time it reaches a certain capacity
buffer = 150

# True/False
screenshots = True
record_video = False
show_video = False
debug = False

# detection car limits
limit_detected = 20 # recommended below 20
limit_good = 400 # this can be tweek recommended between 300-500
limit_bad = 800 # this can be tweek recommended between 700-1200, at least 2x limit_good
# when to take the screenshot 
good_car_screenshot = 450 # must be less than delay
# time to wait before resetting the detection loop
delay = 1500 # must be less than delay
# detection car settings
scaleFactor = 1.02
minNeighbors = 5
minSize = (160,160)