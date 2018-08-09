#Author - Alex Cherniak
#Date: 24.7.18
#Version 1.0
#Description: the scritp is for monitoring for failed jenkins Jobs
#received through arguments the Jenkins URL , username , password , check time , jobs limit , jobs names
#user can provide several jobs to check with '#' delimiter between the jobs.
#user can set a limit of the number of jobs checked(sometimes there is no need to check more than 10 latest builds - the default)
#user can define the check time - if the age of the job is newer than the check time and its failed , it will trigger an alert (default - 900 seconds)
#script can send emails using smtp - postfix. in order to do so , user should use the "-m" option and insert emails with '#' delimiter between them
#python version 2.7.5

####  Imports  ######
import jenkins
import json
import time
import sys
from argparse import ArgumentParser
import smtplib
from email.mime.text import MIMEText
### Arguments ###################

parser = ArgumentParser()
parser.add_argument("-j", "--jobs", dest="jobs" , type=str , required=True , help="Insert job names you want to monitor with a '#' delimiter for several jobs") #jobs argument
parser.add_argument("-l", "--limit", dest="limit",default=10,type=int , required=False , help="Insert builds limit to test for - will be testing the last X builds") #limit number of pulled builds arguments
parser.add_argument("-t", "--timeCheck", dest="checkTime",default=900,type=int , required=False , help="Insert the required check time - job age to test for , test for jobs younger than X seconds")
parser.add_argument("-u", "--username", dest="username",type=str , required=True , help="Insert Jenkins username to login with")
parser.add_argument("-p", "--password", dest="password",type=str , required=True , help="Insert Jenkins password to login with")
parser.add_argument("-m" , "--mail" , dest="mail" ,type=str , required=False , default="" , help="Insert Email addresses if you want to send email alerts with '#' delimiter between emails, make sure email service is on!")
parser.add_argument("-url" , dest="url" ,type=str , required=True , help="Insert Jenkins URL to login to")

args = parser.parse_args()


#######  Read Arguments  ###########################

limit = args.limit
checkTime = args.checkTime
jobs = args.jobs.split("#")
user = args.username
passwd = args.password
url = args.url
emails = args.mail
if ( emails != "" ):
    emails = emails.split('#') #split emails into array by delimiter
### Global Variables ###
result=""
checkTimeMinutes = checkTime / 60

########   Functions   ##########

def sendEmail():
    global result
    global checkTimeMinutes
    mailContent = "Found Failed Jenkins jobs in the last " + str(checkTimeMinutes) + " minutes! \n" + result
    msg = MIMEText(mailContent)
    msg['Subject'] = "Failed Jobs on Jenkins!"
    msg['From'] = "Leeeeroy"
    msg['To'] = str(emails)
    snd = smtplib.SMTP('localhost')
    #snd.set_debuglevel(1)
    try:
        snd.sendmail( "Leeeroy" , emails , msg.as_string() )
    except:
        print "Unable to send email to " + str(emails)
    snd.quit()

def epochToSeconds( time ):
    time = time / 1000
    return time



def connectToJenkins( user , passwd , url ):
    try:
        jenkinsServer = jenkins.Jenkins( url, username=user, password=passwd )
    except:
        print "Unable to connect to Jenkins URL: " + str(url) + ", Please check URL and Credentials"
        sys.exit(3)
    return jenkinsServer


def output():
    global result
    global checkTimeMinutes
    if ( result != "" ): #then there are failed jobs
        print "CRITICAL! Found Failed Jenkins Jobs! in the last: " + str(checkTimeMinutes) + " Minutes - See extended info"
        print result
        print "### ADDITIONAL INFO ###"
        print "Checked Jobs Limit: " + str(limit)
        print "Checked Jobs: " + str(jobs)
        print "Jenkins URL: " + str(url)
        if ( emails != "" ): #make sure there are emails to send to
            sendEmail() #go to send mail function
        sys.exit(2)
    else:
        print "OK! No Failed Jenkins Jobs in the last " + str(checkTimeMinutes) + " Minutes"
        print "### ADDITIONAL INFO ###"
        print "Checked Jobs Limit: " + str(limit)
        print "Checked Jobs: " + str(jobs)
        print "Jenkins URL: " + str(url)
        sys.exit(0)


def main():
    ##### Check Body #####
    global result
    jenkins = connectToJenkins(url=url , passwd=passwd , user=user) #connect to jenkins

    for job in jobs:
        try:
            info = jenkins.get_job_info(job,depth=0,fetch_all_builds=False) #get the info of the job (last 100 builds)
        except:
            print "Unable to fetch builds from job: " + job
            sys.exit(3)
        counter=0
        for build in info['builds']:
            if (counter>limit):
                break
            counter+=1
            number = build['number']
            try:
                buildInfo = jenkins.get_build_info(job , number ,depth=0) #get build information for each fetched build
            except:
                print "Unable to get build information from Job: " + job + ", Job Number: " + number
                sys.exit(3)
            buildTime=epochToSeconds( time=buildInfo['timestamp'] ) #build time in Seconds
            currentTime = time.time() #the current time
            timeDiff = currentTime - buildTime
            if ( buildInfo['result'] == "FAILURE" and timeDiff < checkTime ): #need to document it if clauses are true
                result = result + "Failed Jenkins Job ID: " + buildInfo['id'] + ", INFO: " + buildInfo['fullDisplayName'] + "\n"
        output()

####  Main Start  ####
if __name__ == "__main__":
	main()
