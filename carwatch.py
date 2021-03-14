# OpenCV Python program to detect cars in video frame
# import libraries of python OpenCV 
import cv2
import gc
from multiprocessing import Process, Manager
import datetime
from datetime import timedelta
import os, time
#import os.path
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
# used for prog arguments
import argparse
import sys
# used for logging
import logging
# import user config
import config_app
import config_detection

# send report by email
def send_email_notification(text, html, image1, image2, subject, receiver_email):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = config_app.gmail_user 
    message["To"] = config_app.receiver_email

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")


    for filename in image1, image2:
        fp = open(filename, 'rb')
        msg_img = MIMEImage(fp.read())
        fp.close()
        msg_img.add_header('Content-ID', '<{}>'.format(filename))
        msg_img.add_header('Content-Disposition', 'inline', filename=filename)
        message.attach(msg_img)
        print("attach " + str(filename))

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    if config_detection.debug:
        print("SMTP server used: " + str(config_app.smtp_server))
    server = smtplib.SMTP(config_app.smtp_server, config_app.smtp_port)
    server.ehlo()
    server.starttls()
    server.login(config_app.gmail_user, config_app.gmail_password)
    result_email = server.sendmail(config_app.gmail_user, config_app.receiver_email.split(','), message.as_string())
    server.quit()

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

# archive images
def archive_img():
    print("zip screenshots")
    # zip all files available
    zip_name = 'archive/' + str(datetime.datetime.now().strftime("%d-%m-%Y")) + '_screenshots.zip'
    zipf = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    zipdir('img/', zipf)
    zipf.close()
    # delete screenshots zipped
    files = glob.glob('img/*')
    for f in files:
        os.remove(f)
    return(zip_name)

# build weekly report
def build_report():
    data = pd.read_csv('data/cars.csv', usecols= ['DAY','CARS'])
    if config_detection.debug:
        print(data)
    # filter the data
    good = data[data['CARS'] == 'good']
    bad = data[data['CARS'] == 'bad']
    good=good.replace(to_replace="good",value=int(1))
    bad=bad.replace(to_replace="bad",value=int(1))

    if config_detection.debug:
        print('\nGood cars')
        print(good)
        print('\nBad cars')
        print(bad)

    good = good.groupby(['DAY'])['CARS'].sum()
    bad = bad.groupby(['DAY'])['CARS'].sum()

    if config_detection.debug:
        print('\nGood cars')
        print(good)
        print('\nBad cars')
        print(bad)

    g = []
    for d1, c1 in good.items():
        g.append([d1,c1])

    b = []
    for d2, c2 in bad.items():
        b.append([d2,c2])

    gdf=pd.DataFrame(g, columns =['day', 'good']) 
    bdf=pd.DataFrame(b, columns =['day', 'bad']) 
    df=pd.merge(gdf, bdf, how='left', left_on='day', right_on='day')
    df['good'] = df['good'].fillna(0).astype(int)
    df['bad'] = df['bad'].fillna(0).astype(int)
    df = df.set_index(pd.DatetimeIndex(df['day']))
    df.index = df.index.strftime('%B %d, %Y')
    del df['day']
    print(df)

    fig = pyplot.figure() # Create matplotlib figure
    ax = fig.add_subplot(111) # Create matplotlib axes
    df.good.plot(kind='bar', color='darkgreen', ax=ax, width=0.15, position=1, label="good cars")
    df.bad.plot(kind='bar', color='darkred', ax=ax, width=0.15, position=0, label="bad cars")

    pyplot.xticks(rotation=45, ha='right', size=8)
    pyplot.style.use('seaborn-pastel') #sets the size of the charts
    pyplot.style.use('seaborn-talk')
    pyplot.ylabel('Numbers', fontsize = 15, weight = 'bold')
    pyplot.xlabel(' ', fontsize = 1)
    pyplot.legend()
    pyplot.tight_layout()
    pyplot.subplots_adjust(top=0.88)
    pyplot.suptitle(config_app.report_title, fontsize=15)
    pyplot.savefig('tmp/carwatch-report.jpg')
    print("check new tmp/carwatch-report.jpg\n")
    if config_detection.debug:
        pyplot.show()
    pyplot.close(fig)

    # Pie purcentage bad/good
    fig = pyplot.figure() # Create matplotlib figure
    print(df.tail(7).sum(axis=0))
    labels=['good cars','bad cars']
    colors=['darkgreen','darkred']
    df.sum(axis=0).plot(kind='pie', autopct='%1.1f%%', labels=labels, colors=colors, figsize=(5,5))
    pyplot.ylabel("")
    pyplot.suptitle("Total Good vs Bad cars from last 7 days", fontsize=15)
    pyplot.savefig('tmp/carwatch-report-total-7days.jpg')
    print("check new tmp/carwatch-report-total-7days.jpg\n")
    if config_detection.debug:
        pyplot.show()
    pyplot.close(fig)

    return(good, bad)

# write data to the shared buffer stack:
def write(stack, cam, top: int) -> None:
    """
         :param cam: camera parameters
         :param stack: Manager.list object
         :param top: buffer stack capacity
    :return: None
    """
    print("Process to write: %s" % os.getpid())
    logging.info("Process to write: %s" % os.getpid())
    try:
        cap = cv2.VideoCapture(cam)       
    except Exception as e:
        logging.info("Oops! Can't read the video stream.", e.__class__, "occurred.")
        sys.exit(1)

    # record the stream before processing
    if config_detection.record_video:
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
            if config_detection.record_video:
                out1.write(img)

            # Clear the buffer stack every time it reaches a certain capacity
            # Use the gc library to manually clean up memory garbage to prevent memory overflow
            if len(stack) >= top:
                print("buffer exceeding capacity (" + str(len(stack)) + ")")
                logging.info("buffer exceeding capacity (" + str(len(stack)) + ")")
                del stack[:]
                gc.collect()

    # De-allocate any associated memory usage
    cap.release()
    if config_detection.record_video:
        out1.release()
    cv2.destroyAllWindows()

def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)

# read data in the buffer stack:
def read(stack) -> None:
    print("Process to read: %s" % os.getpid())
    logging.info("Process to read: %s" % os.getpid())
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
            try:
                frames = stack.pop()
                
            except Exception as e:
                logging.info("Oops! Can't read the frame.", e.__class__, "occurred.")
                break
                
            # convert to gray scale of each frames
            gray = cv2.cvtColor(frames, cv2.COLOR_BGR2GRAY)

            # detects cars of different sizes in the input image
            cars = car_cascade.detectMultiScale(gray, scaleFactor=config_detection.scaleFactor, minNeighbors=config_detection.minNeighbors, minSize=config_detection.minSize)

            # draw a rectangle in each cars
            for (x,y,w,h) in cars:
                cv2.rectangle(frames,(x,y),(x+w,y+h),(255,0,255),4)
                car = 1

            # if something has been deteted but likely not a car so reseting after 20 seconds
            if car == 0 and os.path.isfile('tmp/something') and not os.path.isfile('tmp/unknown') and not os.path.isfile('tmp/good') and not os.path.isfile('tmp/bad'):
                if file_age('tmp/something') > 60:
                    print('incorrect detection, probably not a car (reset loop i = ' + str(i) +')')
                    logging.info('incorrect detection, probably not a car (reset loop i = ' + str(i) +')\n')
                    os.remove("tmp/something")
                    i = 0

            # if there is a car and no good or bad cars have been detected
            if car == 1 and not os.path.isfile('tmp/good') and not os.path.isfile('tmp/bad'):
                i += 1
                if config_detection.debug:
                    print('debug i = ' + str(i))
                if i > 1 and i < int(config_detection.limit_detected):
                    cv2.putText(frames, '...', position1, font, 2, (0, 255, 255), 4, cv2.LINE_4) 
                    print('something detected (i = ' + str(i) +')')  
                    logging.info('something detected (i = ' + str(i) +')\n')
                    file = open("tmp/something", "w")
                    file.close()
                if i == (config_detection.limit_detected):
                    print('car detected (i = ' + str(i) +')')
                    logging.info('car detected (i = ' + str(i) +')\n')
                    os.remove("tmp/something")
                    # save picture of the car detected
                    if config_detection.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_detected.jpg'
                        cv2.imwrite(img_name, frames) 
                    file = open("tmp/unknown", "w")
                    file.close()
                if i >= 10 and i < int(config_detection.limit_good):
                    cv2.putText(frames, 'CAR DETECTED', position1, font, 2, (255, 128, 0), 4, cv2.LINE_4) 
                if i == int(config_detection.limit_good):
                    print('good car (i = ' + str(i) +')')
                    logging.info('good car (i = ' + str(i) +')\n')
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
                if config_detection.debug:
                    print('\tdebug j = ' + str(j))
                if i >= 10 and i < int(config_detection.limit_good):
                    cv2.putText(frames, 'CAR DETECTED', position1, font, 2, (255, 128, 0), 4, cv2.LINE_4)
                # wait for some time before call the car gone and reset the loop
                if j == int(config_detection.limit_bad):
                    print('bad car, left without waiting long enough (i = ' + str(i) +' j = ' + str(j) +')')   
                    logging.info('bad car, left without waiting long enough (i = ' + str(i) +' j = ' + str(j) +')\n')
                    cv2.putText(frames, 'BAD CAR (' + str(i) +')', position2, font, 2, (0, 255, 255), 4, cv2.LINE_4)
                    if config_detection.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_bad_car.jpg'
                        cv2.imwrite(img_name, frames) 
                    file = open("tmp/bad", "w")
                    file.close()
                    # record value of i in a file so it can help with tuning detections settings
                    file = open("data/tuning.csv", "a")
                    file.write(str(i) + "\n")
                    file.close()
                    # record into CSV
                    file = open("data/cars.csv", "a")
                    file.write(str(datetime.datetime.now().strftime("%x,%X")) + ",bad\n")
                    file.close()
                        
            # GOOD car detected
            if os.path.isfile('tmp/good'):
                k += 1
                if config_detection.debug:
                    print('\t\tdebug k = ' + str(k))
                if k < int(config_detection.delay):
                    cv2.putText(frames, 'GOOD CAR', position2, font, 2, (0, 204, 0), 4, cv2.LINE_4)
                if k == config_detection.good_car_screenshot:
                    if config_detection.screenshots:
                        img_name = 'img/' + str(datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")) + '_good_car.jpg'
                        cv2.imwrite(img_name, frames) 
                # after car has been flagged, let's always reset i and j to 0 giving some time for the car to leave
                if k == int(config_detection.delay):
                    print('good car left (reset loop k = ' + str(k) +')')   
                    logging.info('good car left (reset loop k = ' + str(k) +')\n')
                    os.remove("tmp/good")
                    os.remove("tmp/unknown")
                    i = 0
                    j = 0
                    k = 0

            # BAD car detected
            if os.path.isfile('tmp/bad'):
                k += 1
                if config_detection.debug:
                    print('\t\tdebug k = ' + str(k))
                if k < int(config_detection.delay):
                    cv2.putText(frames, 'BAD CAR !', position2, font, 2, (0, 255, 255), 4, cv2.LINE_4)
                # after car has been flagged, let's always reset i and j to 0 giving some time for the car to leave
                if k == int(config_detection.delay):
                    print('bad car left (reset loop k = ' + str(k) +')')    
                    logging.info('bad car left (reset loop k = ' + str(k) +')\n')
                    os.remove("tmp/bad")
                    os.remove("tmp/unknown")
                    i = 0
                    j = 0
                    k = 0

            # display frames in a window
            if config_detection.show_video:
                cv2.imshow('stream', frames)

            # first day of the week, email report
            if datetime.date.today().weekday() == config_app.report_day and not os.path.isfile('tmp/mail'):
                print("First day of the week, build the report") 
                logging.info('First day of the week, build the report\n')
                good, bad = build_report()
                if config_detection.screenshots:
                    zip_name = archive_img()
                print("Now, emailing it.")
                text = 'Email only available in HTML format.'
                html = """\
                <html>
                <head></head>
                <body>
                <p><strong>Good cars</strong>: cars waiting at the gate long enough so the gate closes.</p>
                <p><strong>Bad cars</strong>: cars NOT waiting at the gate long enough.</p>
                <p></p>
                <p><img src="cid:tmp/carwatch-report.jpg" alt="Carwatch Report"></p>
                <p><img src="cid:tmp/carwatch-report-total-7days.jpg" alt="Carwatch Report Total last 7 days"></p>
                </body>
                </html>
                """
                subject = '[carwatch] ' + str(datetime.datetime.now().strftime("%d-%m-%Y")) + ' ' + config_app.report_title
                result_email = send_email_notification(text, html, 'tmp/carwatch-report.jpg', 'tmp/carwatch-report-total-7days.jpg', subject, config_app.receiver_email)
                file = open("tmp/mail", "w")
                file.close()

            if datetime.date.today().weekday() != config_app.report_day and os.path.isfile('tmp/mail'):
                if config_detection.debug:
                    print('debug delete tmp/mail')
                os.remove("tmp/mail")

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    # De-allocate any associated memory usage
    if config_detection.record:
        out2.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    # Initiate the parser
    parser = argparse.ArgumentParser(description='Check if cars are waiting long enough at the parking garage gate.')
    parser.add_argument("-R","--report", help="generate report on demand", action="store_true")

    # Read arguments from the command line
    args = parser.parse_args()

    # Check for --report or -R
    if args.report:
        logging.info("=========================================================")
        logging.info("generate report on demand")
        logging.info("=========================================================")
        print("Generate report demand")
        good, bad = build_report()
        sys.exit(1)

    # Initiate logs 
    pid = os.getpid()
    logname = "logs/" + str(datetime.datetime.now().strftime("%d-%m-%Y")) + "_carwatch_" + str(pid) + ".log"
    logging.basicConfig(filename=logname, format="%(asctime)s: %(message)s", level=logging.INFO)

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
    if not os.path.exists('logs'):
        os.makedirs('logs')

    if os.path.isfile('tmp/something'):
        os.remove("tmp/something")
    if os.path.isfile('tmp/unknown'):
        os.remove("tmp/unknown")
    if os.path.isfile('tmp/good'):
        os.remove("tmp/good")
    if os.path.isfile('tmp/bad'):
        os.remove("tmp/bad")
    if os.path.isfile('video/debug.avi'):
        os.remove("video/debug.avi")
    
    # initalize cars.csv file
    if not os.path.exists('data/cars.csv'):
         file = open("data/cars.csv", "w")
         file.write("DAY,HOUR,CARS")
         file.close()

    video = config_app.video
    if config_detection.debug:
        print('video = ' + str(video))

    logging.info("=========================================================")
    logging.info("screenshots = " + str(config_detection.screenshots))
    logging.info("record_video = " + str(config_detection.record_video))
    logging.info("show_video = " + str(config_detection.show_video))
    logging.info("debug = " + str(config_detection.debug))
    logging.info("buffer = " + str(config_detection.buffer))
    logging.info("limit_detected = " + str(config_detection.limit_detected))
    logging.info("limit_good = " + str(config_detection.limit_good))
    logging.info("limit_bad = " + str(config_detection.limit_bad))
    logging.info("good_car_screenshot = " + str(config_detection.good_car_screenshot))
    logging.info("delay = " + str(config_detection.delay))
    logging.info("scaleFactor = " + str(config_detection.scaleFactor))
    logging.info("minNeighbors = " + str(config_detection.minNeighbors))
    logging.info("minSize = " + str(config_detection.minSize))
    logging.info("----------------------------------------------------------")
    logging.info("start")

    # The parent process creates a buffer stack and passes it to each child process:
    q = Manager().list()
    pw = Process(target=write, args=(q, video, config_detection.buffer))
    pr = Process(target=read, args=(q,))
    # Start the child process pw, write:
    pw.start()
    # Start the child process pr, read:
    pr.start()

    # Wait for pr to end:
    pr.join()

    # pw Process is an infinite loop, can not wait for its end, can only be forced to terminate:
    pw.terminate()

    logging.info("end")
    logging.info("=========================================================")
    