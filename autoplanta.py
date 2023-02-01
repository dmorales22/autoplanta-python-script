#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import board
import sys
import os
import configparser
import adafruit_dht
import mysql.connector
import datetime  

#default placeholder values
dhtpin = 0
lightpin = 0 
host = "127.0.0.0"
dbuser = "dbuser"
dbpasswd = "dbpwd"
dbname = "dbname"
dbtable = "dbtable"

#This method reads the DHT11 sensor using the Adafruit driver
def dhtreading():
    sensor = adafruit_dht.DHT11(board.D14) 

    while True:
        try:
            humidity = sensor.humidity
            temperature = sensor.temperature
            temperature_f = (temperature * 1.8) + 32
            print("Temperature: " + str(temperature_f) + " Humidity: " + str(humidity))
            
            return humidity, temperature_f

        except RuntimeError as error:
            print("Opps! There was an error. Trying again.")
            time.sleep(2.0)
            continue

        except Exception as error:
            sensor.exit()
            raise error

        time.sleep(2.0)

#This method creates the mySQL insertion statement to add reading into the database
def sqlwrite(date, temperature, humidity, light_stat):
    conn = mysql.connector.connect(host= host, user=dbuser, passwd=dbpasswd, db=dbname)
    c = conn.cursor()
    
    c.execute("INSERT INTO " + dbtable + " (Date, Temperature, Humidity, Light) VALUES (%s, %s, %s, %s)",(date, temperature, humidity, light_stat))
    conn.commit()
    
    c.close
    conn.close()

#This method reads light sensor and passes the result
def light_sensor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    LIGHT_PIN = int(lightpin)
    GPIO.setup(LIGHT_PIN, GPIO.IN)

    if GPIO.input(LIGHT_PIN):
        print ('Light off')
        return False 
    else:
        print('Light on')
        return True


#This method writes a CSV log of the temperature and status of the grow tent in local storage
def csv_write(date, temperature, humidity, light_stat):
    filename = "grow_box_log_" + str(datetime.date.today()) + ".csv"
    if os.path.exists(filename) == False:
        print("New daily CSV log")
        log = open(filename, 'a')
        os.chmod(filename, 0o777)
        log.write("Date,Temperature,Humidity,Light\n")
        log.write(str(date) + "," + str(temperature) + "," + str(humidity) + "," + str(light_stat) + "\n")
        log.close()

    else:
        print("Updated CSV log")
        log = open(filename, 'a')
        log.write(str(date) + "," + str(temperature) + "," + str(humidity) + "," + str(light_stat) + "\n")
        log.close()

#This method reads the autoplanta_config.cfg to get values like pin numbers and mySQL credentials
def config_reader():
    global dhtpin
    global lightpin
    global host
    global dbuser 
    global dbpasswd
    global dbname 
    global dbtable 
    
    config = configparser.ConfigParser()
    config.read("autoplanta_config.cfg")
    dhtpin = config.get("PINOUT", "dhtsensor")
    lightpin = config.get("PINOUT", "lightsensor")
    host = config.get("DATABASE", "host")
    dbuser = config.get("DATABASE", "dbuser")
    dbpasswd = config.get("DATABASE", "dbpasswd")
    dbname = config.get("DATABASE", "dbname")
    dbtable = config.get("DATABASE", "dbtable")


def main(): 
    unix = int(time.time())
    date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
    config_reader()
    
    print("DHT Pin:", dhtpin)
    print("Light Sensor Pin", lightpin)
    print("DB host:", host)
    print("DB User:", dbuser)
    print("DB Password:", dbpasswd)
    print("DB Name:", dbname)
    print("DB Table:", dbtable)

    humidity, temperature = dhtreading()
    light_stat = light_sensor()
    csv_write(date, temperature, humidity, light_stat)
    sqlwrite(date, temperature, humidity, light_stat)

main()