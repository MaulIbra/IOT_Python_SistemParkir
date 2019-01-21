from PIL import Image
import RPi.GPIO as GPIO
import pytesseract
from time import sleep


import cv2
import numpy as np
import requests
import base64
import json
import pymysql

import hashlib
from pyfingerprint.pyfingerprint import PyFingerprint

#from matplotlib import pyplot as plt
#import pymysql


 
connection = pymysql.connect(
    host='localhost',
    user='admin',
    password='pkm',
    db='PKM',
)

cam = cv2.VideoCapture(0)
cv2.namedWindow("test")
img_counter = 0

while True:
    ret,frame = cam.read()
    cv2.imshow("test",frame)
    #kode_sidik_jari = '5031998'
    k=cv2.waitKey(1)
    if k%256 == 27:
        print("closing")
        break
    elif k%256 == 32:
        try:
            f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
            if ( f.verifyPassword() == False ):
                raise ValueError('The given fingerprint sensor password is wrong!')
        except Exception as e:
            print('The fingerprint sensor could not be initialized!')
            print('Exception message: ' + str(e))
            exit(1)
        
        print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))
        try:
            print('Waiting for finger...')
            while ( f.readImage() == False ):
                pass
            
            f.convertImage(0x01)
            result = f.searchTemplate()
            positionNumber = result[0]
            accuracyScore = result[1]
            if ( positionNumber == -1 ):
                positionNumber = 100
#                print('No match found!')
#                exit(0)
            else:
                print('Found template at position #' + str(positionNumber))
                print('The accuracy score is: ' + str(accuracyScore))
                f.loadTemplate(positionNumber, 0x01)
                characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')
                print('SHA-2 hash of template: ' + hashlib.sha256(characterics).hexdigest())
               
        except Exception as e:
            print('Operation failed!')
            print('Exception message: ' + str(e))
        
#        nim=input("Masukkan Nim : ")
        img_name = "PLAT.jpg".format(img_counter)
        cv2.imwrite("/home/pi/PKM/PLAT.jpg",frame)
        #print("written".format(img_name))
        IMAGE_PATH = '/home/pi/PKM/PLAT.jpg'
        SECRET_KEY = 'sk_22db7f5b4007953aff259b10'
        with open(IMAGE_PATH, 'rb') as image_file:
                img_base64 = base64.b64encode(image_file.read())
        url = 'https://api.openalpr.com/v2/recognize_bytes?recognize_vehicle=1&country=id&secret_key=%s' % (SECRET_KEY)
        r = requests.post(url, data = img_base64)
        try:
            recognize_plat_nomor = json.dumps(r.json()["results"][0]["plate"], indent=2)
            temp_plate_recognize = recognize_plat_nomor.split('"')
            print(temp_plate_recognize[1])
            status = "tersedia"
        except:
            status = "tidaktersedia"
            print("gagal baca dan dirubah")
        
        if status.__eq__("tersedia"):
            try:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM kendaraan"
                    try:
                        cursor.execute(sql)
                        result = cursor.fetchall()
                        for row in result:
                            if temp_plate_recognize[1].__eq__(str(row[0])) and (str(positionNumber)).__eq__(str(row[2])):
                                recognize = "true"
                                print(positionNumber)
                                print("data kendaraan valid SILAHKAN KELUAR !")
                            else:
                                recognize = "false"
                                print("DILARANG KELUAR !")
                                
                    except:
                        recognize = "false"
            except:
                recognize = "false"
            finally:
                connection.commit()
        else:
            recognize = "false"
            
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(19, GPIO.OUT)
        GPIO.setup(21, GPIO.OUT)
        
        if  recognize.__eq__("true"):
            GPIO.output(19,GPIO.HIGH)
            sleep(5)
            GPIO.output(19,GPIO.LOW)
            GPIO.cleanup()
        else:
            GPIO.output(21,GPIO.HIGH)
            sleep(5)
            GPIO.output(21,GPIO.LOW)

cv2.waitKey(0)
cv2.destroyAllWindows()




