# OpenCV Python program to detect cars in video frame
# import libraries of python OpenCV 
import cv2
import gc
from multiprocessing import Process, Manager
import datetime
from datetime import timedelta
import os, time
import os.path
from os import path
import glob
# used to send email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
# used for the report
import pandas as pd
from matplotlib import pyplot
import zipfile
# import user config
import app_config

# send report by email
def send_email_notification(text, html, image, zip_name, subject, receiver_email):
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

    # Add image report
    filename1 = os.path.basename(image)
    msgImage.add_header('Content-ID', '<image1>')
    message.attach(msgImage)
    print('Includes: ' + str(filename1))

    # Add zip file
    if app_config.screenshots:
        filename2 = os.path.basename(zip_name)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(open(zip_name, "rb").read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=\"%s\"" % (filename2))
        message.attach(part)
        print('Includes: ' + str(filename2))

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    if app_config.debug:
        print("SMTP server used: " + str(app_config.smtp_server))
    server = smtplib.SMTP(app_config.smtp_server, app_config.smtp_port)
    server.ehlo()
    server.starttls()
    server.login(app_config.gmail_user, app_config.gmail_password)
    result_email = server.sendmail(app_config.gmail_user, app_config.receiver_email.split(','), message.as_string())
    server.quit()

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

# build weekly report
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
    pyplot.suptitle(app_config.report_title, fontsize=20)
    pyplot.savefig('tmp/carwatch-report.jpg')
    if app_config.debug:
        pyplot.show()

    if app_config.screenshots:
        print('\nArchive screenshots')
        # zip all files available
        zip_name = 'archive/' + str(datetime.datetime.now().strftime("%d-%m-%Y")) + '_screenshots.zip'
        zipf = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
        zipdir('img/', zipf)
        zipf.close()
        # delete screenshots zipped
        files = glob.glob('img/*')
        for f in files:
            os.remove(f)

    return(good, bad, zip_name)

# write data to the shared buffer stack:
def write(stack, cam, top: int) -> None:
    """
         :param cam: camera parameters
         :param stack: Manager.list object
         :param top: buffer stack capacity
    :return: None
    """
    print('Process to write: %s' % os.getpid())
    file = open("carwatch.log", "a")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": Process to write: %s" % os.getpid() + "\n")
    file.close()
    cap = cv2.VideoCapture(cam)

    # record the stream before processing
    if app_config.record:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
        size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out1 = cv2.VideoWriter('video/debug.avi', fourcc, 20.0, size)

    while True:
        _, img = cap.read()
        if _:
            stack.append(img)
            # save video in a file
            if app_config.record:
                out1.write(img)

            # Clear the buffer stack every time it reaches a certain capacity
            # Use the gc library to manually clean up memory garbage to prevent memory overflow
            if len(stack) >= top:
                print('Buffer exceeding capacity (' + str(len(stack)) + ')')
                file = open("carwatch.log", "a")
                file.write(str(datetime.datetime.now().strftime("%x %X")) + ": Buffer exceeding capacity (" + str(len(stack)) + ")\n")
                file.close()
                del stack[:]
                gc.collect()

    # De-allocate any associated memory usage
    cap.release()
    if app_config.record:
        out1.release()
    cv2.destroyAllWindows()

def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)

# read data in the buffer stack:
def read(stack) -> None:
    print('Process to read: %s' % os.getpid())
    file = open("carwatch.log", "a")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": Process to read: %s" % os.getpid() + "\n")
    file.close()
    i = 0
    j = 0
    k = 0
    while True:
        if len(stack) != 0:
            # print('debug time = ' + str(datetime.datetime.now()))
            
            # by default, no car
            car = 0
            
            # trained XML classifiers describes some features of some object we want to detect
            car_cascade = cv2.CascadeClassifier('haarcascade_car.xml')

            # describe the type of font to be used.
            font = cv2.FONT_HERSHEY_SIMPLEX
            # position on the screen
            position1 = (120, 220) # ..., CAR DETECTED
            position2 = (170, 420) # GOOD CAR, BAD CAR

            # reads frames
            frames = stack.pop()

            # convert to gray scale of each frames
            gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)

            # detects cars of different sizes in the input image
            cars = car_cascade.detectMultiScale(gray, scaleFactor=app_config.scaleFactor, minNeighbors=app_config.minNeighbors, minSize=app_config.minSize)

            # draw a rectangle in each cars
            for (x,y,w,h) in cars:
                cv2.rectangle(frames,(x,y),(x+w,y+h),(255,0,255),4)
                car = 1

            # if something has been deteted but likely not a car so reseting after 20 seconds
            if car == 0 and os.path.isfile('tmp/something') and not os.path.isfile('tmp/unknown') and not os.path.isfile('tmp/good') and not os.path.isfile('tmp/bad'):
                if file_age('tmp/something') > 60:
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': incorrect detection, probably not a car (reset loop i = ' + str(i) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': incorrect detection, probably not a car (reset loop i = ' + str(i) +')\n')
                    file.close()
                    os.remove("tmp/something")
                    i = 0

            # if there is a car and no good or bad cars have been detected
            if car == 1 and not os.path.isfile('tmp/good') and not os.path.isfile('tmp/bad'):
                i += 1
                if app_config.debug:
                    print('debug i = ' + str(i))
                if i > 1 and i < int(app_config.limit_detected):
                    cv2.putText(frames, '...', position1, font, 2, (0, 255, 255), 4, cv2.LINE_4) 
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': something detected (i = ' + str(i) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': something detected (i = ' + str(i) +')\n')
                    file.close()
                    file = open("tmp/something", "w")
                    file.close()
                if i == (app_config.limit_detected):
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': car detected (i = ' + str(i) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': car detected (i = ' + str(i) +')\n')
                    file.close()
                    os.remove("tmp/something")
                    # save picture of the car detected
                    if app_config.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_detected.jpg'
                        cv2.imwrite(img_name, frames) 
                    file = open("tmp/unknown", "w")
                    file.close()
                if i >= 10 and i < int(app_config.limit_good):
                    cv2.putText(frames, 'CAR DETECTED', position1, font, 2, (255, 128, 0), 4, cv2.LINE_4) 
                if i == int(app_config.limit_good):
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': good car (i = ' + str(i) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': good car (i = ' + str(i) +')\n')
                    file.close()
                    file = open("tmp/good", "w")
                    file.close()
                    # record into CSV
                    file = open("data/cars.csv", "a")
                    file.write(str(datetime.datetime.now().strftime("%x,%X")) + ",good\n")
                    file.close()

            # if no car on the frame but a car has been detected, not tagged as good or bad yet
            # This logic is to detect bad cars
            if car == 0 and os.path.isfile('tmp/unknown') and not os.path.isfile('tmp/good') and not os.path.isfile('tmp/bad'):
                j += 1
                if app_config.debug:
                    print('\tdebug j = ' + str(j))
                if i >= 10 and i < int(app_config.limit_good):
                    cv2.putText(frames, 'CAR DETECTED', position1, font, 2, (255, 128, 0), 4, cv2.LINE_4)
                # wait for some time before call the car gone and reset the loop
                if j == int(app_config.limit_bad):
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': bad car, left without waiting long enough (i = ' + str(i) +' j = ' + str(j) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': bad car, left without waiting long enough (i = ' + str(i) +' j = ' + str(j) +')\n')
                    file.close()
                    cv2.putText(frames, 'BAD CAR !', position2, font, 2, (0, 255, 255), 4, cv2.LINE_4)
                    if app_config.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_bad_car.jpg'
                        cv2.imwrite(img_name, frames) 
                    file = open("tmp/bad", "w")
                    file.close()
                    # record into CSV
                    file = open("data/cars.csv", "a")
                    file.write(str(datetime.datetime.now().strftime("%x,%X")) + ",bad\n")
                    file.close()
                        
            # GOOD car detected
            if os.path.isfile('tmp/good'):
                k += 1
                if app_config.debug:
                    print('\t\tdebug k = ' + str(k))
                if k < int(app_config.delay):
                    cv2.putText(frames, 'GOOD CAR', position2, font, 2, (0, 204, 0), 4, cv2.LINE_4)
                if k == app_config.good_car_screenshot:
                    if app_config.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_good_car.jpg'
                        cv2.imwrite(img_name, frames) 
                # after car has been flagged, let's always reset i and j to 0 giving some time for the car to leave
                if k == int(app_config.delay):
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': good car left (reset loop k = ' + str(k) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': good car left (reset loop k = ' + str(k) +')\n')
                    file.close()
                    os.remove("tmp/good")
                    os.remove("tmp/unknown")
                    i = 0
                    j = 0
                    k = 0

            # BAD car detected
            if os.path.isfile('tmp/bad'):
                k += 1
                if app_config.debug:
                    print('\t\tdebug k = ' + str(k))
                if k < int(app_config.delay):
                    cv2.putText(frames, 'BAD CAR !', position2, font, 2, (0, 255, 255), 4, cv2.LINE_4)
                # after car has been flagged, let's always reset i and j to 0 giving some time for the car to leave
                if k == int(app_config.delay):
                    print(str(datetime.datetime.now().strftime("%x %X")) + ': bad car left (reset loop k = ' + str(k) +')')
                    file = open("carwatch.log", "a")
                    file.write(str(datetime.datetime.now().strftime("%x %X")) + ': bad car left (reset loop k = ' + str(k) +')\n')
                    file.close()
                    os.remove("tmp/bad")
                    os.remove("tmp/unknown")
                    i = 0
                    j = 0
                    k = 0

            # display frames in a window
            if app_config.showvideo:
                cv2.imshow('stream', frames)

            # first day of the week, email report
            if datetime.date.today().weekday() == app_config.report_day and not os.path.isfile('tmp/mail'):
                print("First day of the week, Build the report")
                file = open("carwatch.log", "a")
                file.write(str(datetime.datetime.now().strftime("%x %X")) + ': First day of the week, Build the report\n')
                file.close()
                good, bad, zip_name = build_report()
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
                subject = '[carwatch] ' + str(datetime.datetime.now().strftime("%d-%m-%Y")) + ' ' + app_config.report_title
                result_email = send_email_notification(text, html, 'tmp/carwatch-report.jpg', zip_name, subject, app_config.receiver_email)
                file = open("tmp/mail", "w")
                file.close()

            if datetime.date.today().weekday() != app_config.report_day and os.path.isfile('tmp/mail'):
                if app_config.debug:
                    print('debug delete tmp/mail')
                os.remove("tmp/mail")

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    # De-allocate any associated memory usage
    if app_config.record:
        out2.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('video'):
        os.makedirs('video')
    if not os.path.exists('img'):
        os.makedirs('img')
    if not os.path.exists('archive'):
        os.makedirs('archive')

    if os.path.isfile('tmp/something'):
        os.remove("tmp/something")
    if os.path.isfile('tmp/unknown'):
        os.remove("tmp/unknown")
    if os.path.isfile('tmp/good'):
        os.remove("tmp/good")
    if os.path.isfile('tmp/bad'):
        os.remove("tmp/bad")
    if os.path.isfile('tmp/mail'):
        os.remove("tmp/mail")
    if os.path.isfile('video/debug.avi'):
        os.remove("video/debug.avi")
    
    # initalize cars.csv file
    if not os.path.exists('data/cars.csv'):
         file = open("data/cars.csv", "w")
         file.write("DAY,HOUR,CARS")

    video = app_config.video
    if app_config.debug:
        print(str(datetime.datetime.now().strftime("%x %X")) + ': video = ' + str(video))

    file = open("carwatch.log", "a")
    file.write("=========================================================\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": screenshots = " + str(app_config.screenshots) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": record = " + str(app_config.record) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": showvideo = " + str(app_config.showvideo) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": debug = " + str(app_config.debug) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": buffer = " + str(app_config.buffer) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": limit_detected = " + str(app_config.limit_detected) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": limit_good = " + str(app_config.limit_good) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": limit_bad = " + str(app_config.limit_bad) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": good_car_screenshot = " + str(app_config.good_car_screenshot) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": delay = " + str(app_config.delay) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": scaleFactor = " + str(app_config.scaleFactor) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": minNeighbors = " + str(app_config.minNeighbors) + "\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": minSize = " + str(app_config.minSize) + "\n")
    file.write("----------------------------------------------------------\n")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": start\n")
    file.close()

    # The parent process creates a buffer stack and passes it to each child process:
    q = Manager().list()
    pw = Process(target=write, args=(q, video, app_config.buffer))
    pr = Process(target=read, args=(q,))
    # Start the child process pw, write:
    pw.start()
    # Start the child process pr, read:
    pr.start()

    # Wait for pr to end:
    pr.join()

    # pw Process is an infinite loop, can not wait for its end, can only be forced to terminate:
    pw.terminate()

    file = open("carwatch.log", "a")
    file.write(str(datetime.datetime.now().strftime("%x %X")) + ": end\n")
    file.write("=========================================================\n")
    file.close()