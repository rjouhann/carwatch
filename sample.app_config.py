gmail_user = "user@gmail.com"    
gmail_password = "secret"
smtp_server = "smtp.gmail.com"
smtp_port = "587" # TLS
receiver_email = "user@gmail.com"

rtsp_user = "admin"
rtsp_password = "secret"
rtsp_ip = "10.1.1.10"
rtsp_port = "554"
rtsp_channel = "/Streaming/Channels/101/Streaming/Channels/1"

report_title = "Parking garage gate traffic"
report_day = 0 # Monday, which day of the week the report is sent

screenshots = True # True/False
record = False # True/False
debug = False # True/False

# RTSP video stream
video = "rtsp://" + rtsp_user + ":" + rtsp_password + "@" + rtsp_ip + ":" + rtsp_port + rtsp_channel

# detection car limits
limit_good = 200
limit_bad = 700
# time to wait before resetting the detection loop
delay = 700
# detection car settings
scaleFactor = 1.03
minNeighbors = 4
minSize = (140,140)
