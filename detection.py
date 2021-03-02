# OpenCV Python program to detect cars in video frame
# import libraries of python OpenCV 
import cv2
import datetime
from datetime import timedelta
import os.path
from os import path
# used to send email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
# used for the report
import pandas as pd
from matplotlib import pyplot

# Settings
import app_config

#video = "rtsp://" + app_config.rtsp_user + ":" + app_config.rtsp_password + "@" + app_config.rtsp_ip + ":" + app_config.rtsp_port + app_config.rtsp_channel
# for dev
video = "media/2.mp4"

def send_email_notification(text, html, image, subject, receiver_email):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = app_config.gmail_user 
    message["To"] = app_config.receiver_email

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    fp = open(image, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    msgImage.add_header('Content-ID', '<image1>')
    message.attach(msgImage)

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    if app_config.debug:
        print("SMTP server: " + str(app_config.smtp_server))
    server = smtplib.SMTP(app_config.smtp_server, app_config.smtp_port)
    server.ehlo()
    server.starttls()
    server.login(app_config.gmail_user, app_config.gmail_password)
    result_email = server.sendmail(app_config.gmail_user, app_config.receiver_email.split(','), message.as_string())
    server.quit()

def build_report():
    data = pd.read_csv('data/cars.csv', usecols= ['DAY','CARS'])
    if app_config.debug:
        print(data)
    # filter the data
    good = data[data['CARS'] == 'good']
    bad = data[data['CARS'] == 'bad']
    good=good.replace(to_replace="good",value=int(1))
    bad=bad.replace(to_replace="bad",value=int(1))

    if app_config.debug:
        print('\nGood cars')
        print(good)
        print('\nBad cars')
        print(bad)

    good = good.groupby(['DAY'])['CARS'].sum()
    bad = bad.groupby(['DAY'])['CARS'].sum()

    if app_config.debug:
        print('\nGood cars')
        print(good)
        print('\nBad cars')
        print(bad)

    good.plot(color="darkgreen",label="good cars")
    bad.plot(color="darkred",label="bad cars")
    pyplot.xticks(rotation=45, ha='right')
    pyplot.style.use('seaborn-pastel') #sets the size of the charts
    pyplot.style.use('seaborn-talk')
    pyplot.xlabel('Days', fontsize = 15, weight = 'bold')
    pyplot.ylabel('Numbers', fontsize = 15, weight = 'bold')
    pyplot.legend()
    pyplot.tight_layout()
    pyplot.subplots_adjust(top=0.88)
    pyplot.suptitle('Maxwell parking garage gate traffic', fontsize=20)
    pyplot.savefig('tmp/carwatch-report.jpg')
    if app_config.debug:
        pyplot.show()
    return(good, bad)


## INITIALIZATION/CLEANUP
i = 0
j = 0
k = 0

if not os.path.exists('tmp'):
    os.makedirs('tmp')
if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists('media'):
    os.makedirs('media')

if os.path.isfile('tmp/a'):
    os.remove("tmp/a")
if os.path.isfile('tmp/b'):
    os.remove("tmp/b")
if os.path.isfile('tmp/good'):
    os.remove("tmp/good")
if os.path.isfile('tmp/mail'):
    os.remove("tmp/mail")
if os.path.isfile('media/debug1.avi'):
    os.remove("media/debug1.avi")
if os.path.isfile('media/debug2.avi'):
    os.remove("media/debug2.avi")

print('video = ' + str(video))

# capture frames from a video/stream
cap = cv2.VideoCapture(video)

# trained XML classifiers describes some features of some object we want to detect
car_cascade = cv2.CascadeClassifier('haarcascade_car.xml')

# describe the type of font to be used.
font = cv2.FONT_HERSHEY_SIMPLEX
# position on the screen
position = (80, 260)

# record the stream
if app_config.record:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
    size = (width, height)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out1 = cv2.VideoWriter('./media/debug1.avi', fourcc, 20.0, size)
    out2 = cv2.VideoWriter('./media/debug2.avi', fourcc, 20.0, size)

# loop runs if capturing has been initialized.
while(cap.isOpened()):
    # print('debug time = ' + str(datetime.datetime.now()))

    # by default, no car
    car = 0

    # reads frames from a video
    ret, frames = cap.read()


    # convert to gray scale of each frames
    gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)

    # Detects cars of different sizes in the input image
    cars = car_cascade.detectMultiScale(gray, scaleFactor=1.02, minNeighbors=4, minSize=(150,150))

    # save video in a file
    if app_config.record:
        out1.write(frames)

    # To draw a rectangle in each cars
    for (x,y,w,h) in cars:
        cv2.rectangle(frames,(x,y),(x+w,y+h),(255,0,255),4)
        car = 1

    if os.path.isfile('tmp/good'):
        k += 1
        # if app_config.debug:
        #    print('\t\tdebug k = ' + str(k))
        # after car has been flag good, let's always reset i and j to 0 giving some time for the good car to leave
        if k < 600:
            cv2.putText(frames, 'GOOD CAR', position, font, 2, (0, 204, 0), 4, cv2.LINE_4)
            i = 0
            j = 0
        if k == 600:
            print(str(datetime.datetime.now().strftime("%x %X")) + ': good car left (reset loop k = ' + str(k) +')')
            os.remove("tmp/good")
            file = open("data/cars.csv", "a")
            file.write(str(datetime.datetime.now().strftime("%x,%X")) + ",good\n")
            file.close()

    if car == 1:
        i += 1
        # if app_config.debug:
        #     print('debug i = ' + str(i))
        if not os.path.isfile('tmp/good'):
            if i > 1 and i < 10:
                cv2.putText(frames, '...', position, font, 2, (0, 255, 255), 4, cv2.LINE_4) 
                if app_config.debug:
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': something detected (i = ' + str(i) +')')
            if i == 10:
                print(str(datetime.datetime.now().strftime("%x %X")) + ': car detected (i = ' + str(i) +')')
                file = open("tmp/a", "w")
                file.close()
            if i >= 10 and i <400:
                cv2.putText(frames, 'CAR DETECTED', position, font, 2, (255, 128, 0), 4, cv2.LINE_4) 
            if i == 400:
                file = open("tmp/b", "w")
                file.close()
                if app_config.debug:
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': car waited (i = ' + str(i) +')')

    if os.path.isfile('tmp/a') and os.path.isfile('tmp/b'):
        os.remove("tmp/a")
        os.remove("tmp/b")
        i = 0
        k = 0
        print(str(datetime.datetime.now().strftime("%x %X")) + ': good car')
        file = open("tmp/good", "w")
        file.close()

    if car == 0 and os.path.isfile('tmp/a'):
        j += 1
        # if app_config.debug:
        #     print('\tdebug j = ' + str(j))
        if i >= 10 and i <400:
            cv2.putText(frames, 'CAR DETECTED', position, font, 2, (255, 128, 0), 4, cv2.LINE_4) 
        # wait for some time before call the car gone and reset the loop
        if j == 700:
            print(str(datetime.datetime.now().strftime("%x %X")) + ': bad car, left without waiting long enough (reset loop i = ' + str(i) +')')
            i = 0
        if j > 700 and j < 900:
            cv2.putText(frames, 'BAD CAR !', position, font, 2, (0, 255, 255), 4, cv2.LINE_4)
        if j == 800:
            file = open("data/cars.csv", "a")
            file.write(str(datetime.datetime.now().strftime("%x,%X")) + ",bad\n")
            file.close()
            os.remove("tmp/a")
            j = 0

    # save video in a file
    if app_config.record:
        out2.write(frames)

    # Display frames in a window
    if app_config.debug:
        cv2.imshow('window', frames)

    # first day of the week, email report
    if datetime.date.today().weekday() == 0 and not os.path.isfile('tmp/mail'):
        print("First day of the week, Build the report")
        good, bad = build_report()
        print("Now, emailing it.")
        text = 'Email only available in HTML format.'
        html = """\
        <html>
        <head></head>
        <body>
        <p><strong>Good cars</strong>: cars waiting at the gate long enough so the gate closes.</p>
        <p><strong>Bad cars</strong>: cars NOT waiting at the gate long enough.</p>
        <p></p>
        <p><img src="cid:image1" alt="Carwatch Report"></p>
        </body>
        </html>
        """
        subject = '[carwatch] Weekly Report Maxwell Parking Garage Gate'
        result_email = send_email_notification(text, html, 'tmp/carwatch-report.jpg', subject, app_config.receiver_email)
        file = open("tmp/mail", "w")
        file.close()

    if datetime.date.today().weekday() != 0 and os.path.isfile('tmp/mail'):
        if app_config.debug:
            print('debug delete tmp/mail')
        os.remove("tmp/mail")

    # Wait for Esc key to stop
    if cv2.waitKey(33) == 27:
        break
 
# De-allocate any associated memory usage
cap.release()
if app_config.record:
    out1.release()
    out2.release()
cv2.destroyAllWindows()