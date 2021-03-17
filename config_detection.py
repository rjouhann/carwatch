# Clear the buffer stack every time it reaches a certain capacity
buffer = 500

# True/False
screenshots = True
record_video = False
show_video = False
debug = False

# detection car limits
limit_detected = 30 # recommended below 30
limit_good = 270 # this can be tweek recommended between 300-500
limit_bad = 1000 # this can be tweek recommended between 700-1200, at least 2x limit_good
# when to take the screenshot 
good_car_screenshot = 300 # generally close to limit_good
# time to wait before resetting the detection loop
delay = 2500 # must be more than limit_bad
# detection car settings
scaleFactor = 1.02
minNeighbors = 5
minSize = (160,160)