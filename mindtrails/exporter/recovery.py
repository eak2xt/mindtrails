# ------------------------------------------#
# Import the Requests

import requests # To make REST requests of the client.
import time
import os.path
import rsa # To decrypt values.
import csv # To write the data into CSV file safely
import binascii
import logging
import logging.config
import yaml
import pickle
import glob
import os
import json

# ------------------------------------------#
# Load the Configuration file
if __name__ == "__main__":
    config = {}
    execfile("recovery.config", config)


# Set up logging config files
logging.config.dictConfig(yaml.load(open('recovery_log.config', 'r')))

# export Readme file

def readMe(scaleName,data_file,fileList,deleteable,entryNo,error):
    export = config["PATH"]+"recovered_data/" + "README_" + scaleName + "_recovered_" + time.strftime(config["DATE_FORMAT"]) +'.txt'
    readme = open(export,"w")
    readme.write("Data recovery done at %s, %s for %s questionnaire. Recovery information are as follow:\n" % (time.strftime(config["TIME_FORMAT"]), time.strftime(config["DATE_FORMAT"]), scaleName));
    readme.write("\n");
    readme.write("\t%d data files found in raw_data folder:\n\t\tStart file: %s\n\t\tEnd file: %s\n" % (len(fileList),fileList[0],fileList[-1]));
    readme.write("\t%d data entry recovered, %d error in recovery. HEADUP: There might be duplication in entries.\n" % (entryNo,error));
    readme.write("\tRecovered data file path: %s\n" % data_file);
    readme.write("\n");
    if not deleteable:
        readme.write("*****WARNING******: This questionnaire is not deleteable on the server. Make sure that you only recovered the most recent raw data file otherwise you might have high amount of duplicated data.\n");
        readme.write("*****WARNING******: For undeletable questionnaire, active dataset is a more acurrate and completed dataset than recovered dataset.\n");
    readme.close()



# Decrypting
with open(config["PRIVATE_FILE"]) as privatefile:
    keydata = privatefile.read()
priv_key = rsa.PrivateKey.load_pkcs1(keydata)
def decrypt(crypto, id, scaleName, field):
    log = logging.getLogger('recovery.decrypt')
    if crypto is None: return ""
    try:
        value = crypto.decode('base64')
        log.info('Decode successfully.')
        try:
            message = rsa.decrypt(value, priv_key)
            log.info('Decrypt successfully.')
            return message.decode('utf8')
        except (rsa.pkcs1.CryptoError, rsa.pkcs1.DecryptionError):
            log.error('Decrypt failed, original value recorded. Questionnaire = %s, Entry ID: %s, Field: %s See information:', scaleName, id, field, exc_info = 1)
            return crypto
    except (UnicodeDecodeError, binascii.Error):
        log.error('Decode failed, item skipped. Questionnaire = %s, Entry ID: %s, Field: %s See information:', scaleName, id, field, exc_info = 1)

# Create data files with date as name:
def createFile(file, ks):
    log = logging.getLogger('recovery.createFile')
    if not os.path.exists(file): # Create new file if file doesn't exist
        with open(file, 'w') as datacsv:
            headerwriter = csv.DictWriter(datacsv, dialect='excel', fieldnames= ks)
            try:
                headerwriter.writeheader()
                log.info("New data file created: %s", file)
            except csv.Error:
                log.critcal("Failed to create new data files, fatal, emailed admin.", exc_info=1)

# SafeWrite function, use this to write questionnaire data into csv files
def safeWrite(quest, date_file, scaleName, deleteable):
#B\ Open [form_name]_[date].csv, append the data we have into it, one by one.
    log = logging.getLogger('recovery.safeWrite')
    log.info("Writing new entries from %s to %s: writing in progress......", scaleName, date_file)
    ks = list(quest[0].keys())
    ks.sort()
    createFile(date_file, ks)
    with open(date_file, 'a') as datacsv:
        dataWriter = csv.DictWriter(datacsv, dialect='excel', fieldnames= ks)
        t = 0
        error = 0
        for entry in quest:
            for key in ks:
                if(key.endswith("RSA")): value = decrypt(entry[key], entry['id'], scaleName, key)
                elif entry[key] is None: value = ""
                elif isinstance(entry[key], unicode): value = entry[key]
                else:
                    try:
                        value = str(entry[key]) # could be an int, make sure it is a string so we can encode it.
                    except:
                        log.error("Data encode failed, data lost. Questionnaire: %s, Entry ID: %s, Field: %s", scaleName, entry['id'], key, exc_info = 1) # Should log error, entry ID and data field
                if (value != None):
                    try:
                        entry[key] = value.encode('utf-8')
                        log.debug("Data successfully encoded.")
                    except UnicodeEncodeError:
                        log.error("Data encode failed, data lost. Questionnaire: %s, Entry ID: %s, Field: %s", scaleName, entry['id'], key, exc_info = 1) # Should log error, entry ID and data field
                else: entry[key] = ""
            try:
                dataWriter.writerow(entry)
                t += 1
                log.debug("%s entries wrote successfully.", str(t))
            except csv.Error:
                error += 1
                log.critical("Failed in writing entry, Questionnaire: %s, Entry ID: %s", scaleName, str(entry['id']), exc_info = 1)
        log.info("Questionnaire %s update finished - %s new entries recoded successfully.", scaleName, str(t))
        if error > 0:
            log.critical("Questionnaire %s update error - %s new entries failed to recode.", scaleName, str(error))
    return (t, error)

# Check the path before doing anything
def pathCheck():
    log = logging.getLogger('recovery.pathCheck')
    if not os.path.exists(config["PATH"]+"raw_data/"):
        log.error("No raw_data folder is found, please double check before continuing.")
        print("No raw_data folder is found, please double check before continuing.")
        return False
    if not os.path.exists(config["PATH"]+"recovered_data/"):
        try:
            os.makedirs(config["PATH"]+"recovered_data/")
            log.info("Successfully created recoverer_data folder.")
            print("Successfully created recoveryed_data folder.")
            return True
        except:
            log.critical("Failed to create data folders, fatal, emailed admin.", exc_info=1)
            print("Failed to create data folders, fatal, emailed admin.")
            return False
    else: return True

# Read in files here and recover the data
def safeRecover(scaleName, data_file, deleteable):
    log = logging.getLogger('recovery.safeRecover')
    fileList = sorted(glob.glob(config["PATH"]+'raw_data/'+scaleName+'*.json'))
    entryNo = 0
    error = 0
    for infile in fileList:
        with open(infile) as json_file:
            response = json.load(json_file)
            t, e = safeWrite(response,data_file,scaleName,deleteable)
            entryNo += t
            error += e
    readMe(scaleName,data_file,fileList,deleteable,entryNo,error)


# Take your order so that we know what scale and how much data you want to recover:
def takeOrder():
    log = logging.getLogger('recovery.takeOrder')
    scaleName = str(raw_input("""Please enter the scale name that you would like
        to recover data for. Reminder: Type in the name exactly as it is on the
        raw data files.\nscaleName:"""))
    deleteable = str(raw_input("Is this scale deleteable?[Y/N]:"))
    yn = set(['Y','N'])
    while (not (deleteable in yn)):
        deleteable = str(raw_input("I don't get it. Is this scale deleteable or not?[Y/N]:"))
    deleteable = True if deleteable == 'Y' else False
    print("Thanks!\n")
    if (not deleteable):
        go = str(raw_input("*****WARNING******: Make sure that you only recover the most recent data file instead of all of them, otherwise the recovered data will contain a lot of replication. Do you want to continue the recovery?[Y/N]:"))
        while (not (go in yn)):
            go = str(raw_input("I don't get it. Do you want to continue the recovery?[Y/N]:"))
        go = True if go == 'Y' else False
    else: go = True
    if go:
        date_file = config["PATH"]+"recovered_data/" + scaleName + "_recovered_" + time.strftime(config["DATE_FORMAT"]) +'.csv'
        log.info("Recovery started.")
        safeRecover(scaleName, date_file, deleteable)
    else:
        log.info("Recovery aborted.")

# ------------------------------------------#
# This is the main module
def recovery():
    log = logging.getLogger('recovery')
    print("Hello there!")
    if pathCheck():
        log.info("Data Recovery tried at %s, %s",time.strftime(config["DATE_FORMAT"]), time.strftime(config["TIME_FORMAT"]))
        print("Data Recovery tried at %s, %s",time.strftime(config["DATE_FORMAT"]), time.strftime(config["TIME_FORMAT"]))
        takeOrder()
    else:
        log.info("No raw data found or recovery data folder failed to be created. Please check before trying again. Thanks!")
        print("No raw data found or recovery data folder failed to be created. Please check before trying again. Thanks!")


# Works here:
recovery()
