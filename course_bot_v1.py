import os
import urllib
import requests
import time
from bs4 import BeautifulSoup
from time import sleep, strftime, gmtime
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
sectionList = []


# returns the unique semester identifier

def getSemester():
    # start a new web scraping session
    s = requests.session()

    # download the main page of classes
    try:
        html = s.get("https://ntst.umd.edu/soc")
    except requests.exceptions.RequestException as e:
        post_params = { 'bot_id' : 'yourbotapi', 'text': "something wrong" }
        requests.post('https://api.groupme.com/v3/bots/post', params = post_params)

        print(e)
        sleep(10)

    # parse the html of the class page
    options = BeautifulSoup(html.text, "html.parser")
    options = options.find("select", {"id": "term-id-input"})
    options = str(options).split("</option>")

    # find the option with the semester code in it
    for option in options:
        if '"selected"' in option:
            semester = option

    # extract the semester code
    semester = semester[semester.index('value="')+7:]
    semester = semester[:semester.index('"')]

    # close the session
    s.close()

    return semester

# returns a list of sections


def getSections(course):
    # start a new web scraping session
    s = requests.session()

    # begin composing the url
    url = "https://ntst.umd.edu/soc/search"
    url += "?courseId=" + course
    url += "&sectionId="
    url += "&termId="+getSemester()
    url += "&_openSectionsOnly=on"
    url += "&creditCompare="
    url += "&credits="
    url += "&courseLevelFilter=ALL"
    url += "&instructor="
    url += "&_facetoface=on"
    url += "&_blended=on"
    url += "&_online=on"
    url += "&courseStartCompare="
    url += "&courseStartHour="
    url += "&courseStartMin="
    url += "&courseStartAM="
    url += "&courseEndHour="
    url += "&courseEndMin="
    url += "&courseEndAM="
    url += "&teachingCenter=ALL"
    url += "&_classDay1=on"
    url += "&_classDay2=on"
    url += "&_classDay3=on"
    url += "&_classDay4=on"
    url += "&_classDay5=on"

    # download the list of classes
    try:
        html = s.get(url).text
    except requests.exceptions.RequestException as e:
        post_params = { 'bot_id' : 'yourbotapi', 'text': "something wrong" }
        requests.post('https://api.groupme.com/v3/bots/post', params = post_params)

        print(e)
        sleep(10)

    # parse the html with bs4
    courses = BeautifulSoup(html, "html.parser").find_all(
        "div", {"class": "section"})

    # make an empty list to contain all sections
    sections = []

    # loop through every section in the course list
    for course in courses:

        # declare a blank list to hold section and time info
        section = []
        times = []

        # get the times avaiable
        slots = course.find("div", {"class": "class-days-container"})
        slots = slots.find_all("div", {"class": "row"})

        # loops thorugh and add all time to the list
        for slot in slots:
            time = slot.find("div", {"class": "section-day-time-group"})
            time = " ".join(time.text.strip().split("\n"))
            times.append(time)

        # get the name of the course
        name = str(course.find(
            "div", {"class": "section-action-links-container"}))
        name = name[name.index('value="')+7:]
        name = name[:name.index('"')]

        # append the name of the course to the list
        section.append(name)

        # get the amount of open seats
        openSeatsCount = int(course.find(
            "span", {"class": "open-seats-count"}).text)

        # say whether class is open
        if openSeatsCount > 0:
            section.append("open")
        else:
            section.append("closed")

        # get the section number, and the instructor
        section.append(course.find(
            "span", {"class": "section-id"}).text.strip())
        section.append(course.find(
            "span", {"class": "section-instructor"}).text)
        sectionList.append(course.find(
            "span", {"class": "section-id"}).text.strip())

        # add the section information and the times
        sections.append(section)
        section.append(times)

    # close the current session
    s.close()

    # return all sections
    return sections

# returns if a section is open


def isOpen(section):
    if section[1] != "open":
        return False
    else:
        return True


# main function, continuously checks for openings

#global vars
rows = 15
columns = 15
sections_to_check = [[0 for x in range(columns)] for y in range(rows)]
to_remove = [[0 for x in range(columns)] for y in range(rows)]
base_sections = []
course = []


def testudo():
    post_params = { 'bot_id' : 'yourbotapi', 'text': "Starting Bot" }
    requests.post('https://api.groupme.com/v3/bots/post', params = post_params)
    # if section not open, continuously check
    last_message = ""
    remove_mes = "remove"
    while True:
        request_params = {'token': 'your request token'}
        request_params['limit'] = 1
        response_messages = requests.get(
            'https://api.groupme.com/v3/groups/yourgroupID/messages', params=request_params).json()['response']['messages']
        for message in response_messages:
            if(message['user_id'] == 'YourUserID' and message['text'] != last_message):
                # list function
                if(message['text'].lower() == "list"):
                    listFunction()
                    break
                if(remove_mes in message['text'].lower()):
                    deleteSectionWithMessage(message['text'])
                    print(message['text'])
                    last_message = message['text']
                    sleep(1)
                    break
                print(message['text'])
                last_message = message['text']
                index_of_space = message['text'].find(" ")
                # accepts new course
                new_course = message['text'][0:index_of_space]
                new_section_num = message['text'][index_of_space +
                                                  1: len(message['text'])]

                got_new = True
                for curr_course in course:
                    if(new_course.lower() == curr_course.lower()):
                        got_new = False
                # if this is a new course
                if (got_new == True):
                    base_sections.append(getSections(new_course))
                    print("creating new course")
                    #this is where we add a new course
                    course.append(new_course.lower())
                # adds section to this list
                index_of_course = course.index(new_course.lower())
                curr_sections = getSections(course[index_of_course])
                counter = 0
                while(counter < len(curr_sections)):
                    if(curr_sections[counter][2] == new_section_num):
                        command = 'curl -X POST \"https://api.groupme.com/v3/bots/post?bot_id=yourbotapi&text=' + \
                            "(ADDED)-->" + course[index_of_course] + "-->status:" + \
                            curr_sections[counter][1] + \
                            "-->Section:" + new_section_num + '\"'
                        os.system(command)
                    counter += 1
                sections_to_check[index_of_course].append(new_section_num)
                break
        index_of_course = 0
        #This is where we check the status of each section of each course
        while (index_of_course < len(course)):
            checkStatus(index_of_course)
            index_of_course += 1
            sleep(randint(10, 20))
        # course: open/close: section#: proffName: times:


def listFunction():
    course_index = 0
    while (course_index < len(course)):
        sections = getSections(course[course_index])
        counter = 0
        while(counter < len(sections)):
            for curr_section in sections_to_check[course_index]:
                if(sections[counter][2] == curr_section):
                    command = 'curl -X POST \"https://api.groupme.com/v3/bots/post?bot_id=yourbotapi&text=' + \
                        str(len(sections_to_check[course_index]))+"_" + course[course_index] + "-->status:" + \
                        sections[counter][1] + \
                        "-->Section:" + str(curr_section) + '\"'
                    os.system(command)
                    sleep(1)
            counter += 1
        course_index += 1


def checkStatus(course_index):
    if(len(to_remove[course_index]) > 0):
        for index in reversed(to_remove[course_index]):
            del sections_to_check[course_index][index]
    to_remove[course_index].clear()
    # print(course[course_index])
    if(course[course_index] != "0"):
        # checks for new sections
        newSection(course_index, base_sections[course_index])
        # gets new list of sections (updates)
        sections = getSections(course[course_index])
        counter = 0
        while(counter < len(sections)):
            indexForSection = 0
            for curr_section in sections_to_check[course_index]:
                #if(sections[counter][2] == curr_section):
                    #print("checking " +
                    #      course[course_index] + "section: " + curr_section)
                if(sections[counter][2] == curr_section and sections[counter][1] == "open"):
                    #print(curr_section + " is open")
                    command = 'curl -X POST \"https://api.groupme.com/v3/bots/post?bot_id=yourbotapi&text=' + \
                        str(len(sections_to_check[course_index]))+"_" + course[course_index] + "__IS_OPEN__" + \
                        "-->Section:" + curr_section + '\"'
                    os.system(command)
                    to_remove[course_index].append(indexForSection)
                indexForSection += 1
            counter += 1

# returns if a new section is open


def deleteSectionWithMessage(message):
    checking_course = message[7:message.index(" ", 8)].lower()
    section = message[message.index(" ", 8)+1:len(message)]
    print("_"+checking_course + "_remove")
    print("_"+section + "_remove")
    if(checking_course in course):
        course_index = course.index(checking_course.lower())
        deleteSection(course_index, section)


def deleteSection(course_index, section_to_remove):
    print("courseindex:_" + str(course_index) + "_")
    print("sectiontoremove_" + section_to_remove + "_")
    print("sectiontocheck:_"+sections_to_check[course_index][0])
    if(sections_to_check[course_index].count(section_to_remove) > 0):
        print("found section")
        index = sections_to_check[course_index].index(section_to_remove)
        command = 'curl -X POST \"https://api.groupme.com/v3/bots/post?bot_id=yourbotapi&text=' + \
            "Removed:__" + course[course_index] + \
            "-->Section:" + section_to_remove + '\"'
        os.system(command)
        del sections_to_check[course_index][index]
   # if(len(sections_to_check[course_index]==0)):
       # del course[course_index]


def newSection(course_index, currsections):
    #print("checking new section: "+ currsections[1][0])
    updated_section = getSections(course[course_index])
    counter = 0
    while(counter < len(updated_section)):
        section_number = updated_section[counter][2]
        if section_number not in currsections[counter]:
            command = 'curl -X POST \"https://api.groupme.com/v3/bots/post?bot_id=yourbotapi&text=' + \
                course + "_(NEW)section_open-->" + section_number + '\"'
            os.system(command)
            base_sections[course_index] = getSections(course)
        counter += 1


# define the command line arguments
if __name__ == '__main__':
    testudo()
