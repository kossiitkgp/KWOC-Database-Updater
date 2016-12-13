import psycopg2
import requests
import os
import traceback
import json
from leaderboard import *
from threading import Thread
import delJSONS

try:
        import urlparse
except Exception as e:
        from urllib import parse as urlparse

if "LOCAL_CHECK" in os.environ:
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
        )
        cursor = conn.cursor()
def slack_notification(message):
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "text":"Following error occured while updating KWOC database.\n{}".format(message)
    })
    r = requests.post(
        os.environ["SLACK_WEBHOOK_URL"], headers=headers, data=data)

    if r.status_code != 200:
        print("in slack_notification : {}".format(r.status_code))
        print(r.text)

def updateCommits():
    global conn, cursor
    # cursor2 = conn.cursor()
    if "LOCAL_CHECK" not in os.environ:
            msg = "Database Connection cannot be set since you are running website locally"
            slack_notification (msg)
            return 0 
    query="SELECT * FROM student"
    query2 = "SELECT * FROM project"
    try:
        cursor.execute(query)
        studentList = cursor.fetchall()
        cursor.execute(query2)
        projectsList = cursor.fetchall()
        # print projectsList
        for student in studentList :
            # print ("Getting commits for {}".format(student[0]))
            commits = 0
            for project in  projectsList :
                if not project[0] :
                    continue
                try :
                    # print ("Getting commits for {}".format(student[0]))
                    commits += getCommitsOffline(student[0],project[0])
                    # print ("Got {} commits for {} in {}".format(commits,student[0],project[0]))
                except :
                    error_msg = "Unable to get commits for {} in project {}.\nGot following error : {}".format(student[0],project[0],traceback.format_exc())
                    # print (error_msg)
                    slack_notification(error_msg)
            # print ("Updating database")
            updateQuery = "UPDATE student SET commits = '%s' where git_handle='%s'" % (str(commits),student[0]) 
            try :  #updating commits in student database 
                cursor.execute(updateQuery)
                conn.commit()
                
                # print ("Database updated")
            except :
                conn.rollback()
                
                error_msg = "Unable to update commits for {} .\nFollowing error occured{}".format(student[0],traceback.format_exc())
                # print(error_msg)
                slack_notification (error_msg)

            # print student[0]
            # if not student[5] :
                # if student[0]
            # Thread(target=getCommitsOfStudent , args=(student[0], projectsList,)).start() 
            # if index >= 10 :
            #     break
            # getCommitsOfStudent(student[0] , projectsList)
    except:
            conn.rollback()
            
            error_msg = "Unable to get all projects/students \nFollowing error occured {}".format(
                    traceback.format_exc())
            # print (error_msg)
            slack_notification (error_msg)    
# def getCommitsOfStudent(student,projectsList) :
#     global conn,cursor
#     commits = 0
#     for project in  projectsList :
#         try :
#             commits += get_commits(student,project[0])
#             print ("Got {} commits for {} in {}".format(commits,student,project[0]))
#         except :
#             error_msg = "Unable to get commits for {} in project {}.\nGot following error : {}".format(student,project[0],traceback.format_exc())
#             print (error_msg)
#     updateQuery = "UPDATE student SET commits = '%s' where git_handle='%s'" % (str(commits),student) 
#     try :  #updating commits in student database 
#         cursor.execute(updateQuery)
#         conn.commit()
#     except :
#         conn.rollback()
#         error_msg = "Unable to update commits for {} .\nFollowing error occured{}".format(student,traceback.format_exc())
#         print(error_msg)
#         # slack_notification (error_msg)
def updateProjectsJSON() :
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
            msg = "Database Connection cannot be set since you are running website locally"
            slack_notification (msg)
            return 0 
    query = "SELECT * FROM project"  
    try:
        cursor.execute(query)
        projectsList = cursor.fetchall()
        for index,project in enumerate(projectsList) :
            if not project[0] :
                continue
            getProjectsJson(project[0])
    except:
            conn.rollback()
            error_msg = "Unable to get all projects \nFollowing error occured {}".format(
                    traceback.format_exc())
            # print (error_msg)
            slack_notification (error_msg) 


def updateProjectImage():
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
            msg = "Database Connection cannot be set since you are running website locally"
            slack_notification (msg)
            return 0 
    query="SELECT * FROM project"
    try:
        cursor.execute(query)
        # projectsData=list()
        for index,row in enumerate(cursor.fetchall()) :
            if row[1] == "df" and row[2] == "df" :
                continue
            if not row[7] or row[7] == "http://i.imgur.com/nx6cwcv.png" :   #checking if a valid image url is already present 
                handle=row[0][:]
                imgURL=getimageURL(handle.split("/")[0])
                if imgURL :
                    updateQuery = "UPDATE project SET image='%s' WHERE project_handle='%s'" % (imgURL,row[0])
                else : 
                    updateQuery = "UPDATE project SET image='%s' WHERE project_handle='%s'" % ("http://i.imgur.com/nx6cwcv.png",row[0])
                try :  #updating image URL in the database 
                    cursor.execute(updateQuery)
                    conn.commit()
                    
                except :
                    conn.rollback()
                    
                    error_msg = "Unable to update image url {} for {}.\nFollowing error occured{}".format(imgURL,row[0],
                traceback.format_exc())
                    slack_notification (error_msg)
    except:
            conn.rollback()
            
            error_msg = "Unable to get all projects\nFollowing error occured {}".format(
                    traceback.format_exc())
            slack_notification (error_msg)

def getimageURL(githubUsername) :  # getting the image url from github 
    baseQuery="https://api.github.com/search/users?access_token={}&q=".format(os.environ["DEFCON_GITHUB_AUTH_TOKEN"])
    try :
        query = baseQuery+githubUsername 
        response=requests.get(baseQuery+githubUsername).json()
        if response["total_count"] == 1 :  # checking if a unique user is found
            return response["items"][0]["avatar_url"]
            # return unicode(response["items"][0]["avatar_url"] , "utf-8")
        else :
            for item in response["items"] :
                if item["login"] == githubUsername :
                    return item["avatar_url"]
            slack_notification ("Unable to find image for {} ".format(githubUsername))
            return False 
    except :
        slack_notification("Unable to retrive image url for {}\nGot following error :{}".format(githubUsername,traceback.format_exc()))
        return False 

def updateForkNo():
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
            msg = "Database Connection cannot be set since you are running website locally"
            print (msg)
    query="SELECT * FROM project"
    try:
        cursor.execute(query)
        for index,row in enumerate(cursor.fetchall()) :
            if row[1] == "df" and row[2] == "df" :
                continue
            forkno = getforks(row[0])
            updateQuery = "UPDATE project SET forkno='%s' WHERE project_handle='%s'" % (str(forkno),row[0])
            try :  #updating image URL in the database 
                cursor.execute(updateQuery)
                conn.commit()
                
            except :
                conn.rollback()
                
                error_msg = "Unable to update fork no for {}.\nFollowing error occured{}".format(row[0],
            traceback.format_exc())
                slack_notification (error_msg)
    except:
            conn.rollback()
            
            error_msg = "Unable to get all projects\n\n {}".format(
                    traceback.format_exc())
            slack_notification (error_msg)   

def getforks(projectHandle):
    baseQuery="https://api.github.com/repos/{}?access_token={}".format(projectHandle,os.environ["DEFCON_GITHUB_AUTH_TOKEN"])
    try :
        response = requests.get(baseQuery).json()
        forkNo = response["forks_count"]
        return forkNo
    except :
        error_msg = "Unable to get total forks for {}.\nFollowing error occured : {}".format(projectHandle,traceback.format_exc())
        slack_notification(error_msg)
        return "None"

def updatewatcherNo():
    global conn, cursor
    if "LOCAL_CHECK" not in os.environ:
            msg = "Database Connection cannot be set since you are running website locally"
            print (msg)
    query="SELECT * FROM project"
    try:
        cursor.execute(query)
        for index,row in enumerate(cursor.fetchall()) :
            if row[1] == "df" and row[2] == "df" :
                continue
            watcherno = getwatchers(row[0])
            updateQuery = "UPDATE project SET watcherno='%s' WHERE project_handle='%s'" % (str(watcherno),row[0])
            try :  #updating image URL in the database 
                cursor.execute(updateQuery)
                conn.commit()
                
            except :
                conn.rollback()
                
                error_msg = "Unable to update watcher no for {}.\nFollowing error occured{}".format(row[0],
            traceback.format_exc())
                # print (error_msg)
                slack_notification(error_msg)
    except:
            conn.rollback()
            
            error_msg = "Unable to get all projects\n\n {}".format(
                    traceback.format_exc())
            slack_notification (error_msg)   

def getwatchers(projectHandle):
    baseQuery="https://api.github.com/repos/{}?access_token={}".format(projectHandle,os.environ["DEFCON_GITHUB_AUTH_TOKEN"])
    try :
        response = requests.get(baseQuery).json()
        watcherNo = response["watchers"]
        return watcherNo
    except :
        error_msg = "Unable to get total watchers for {}.\nFollowing error occured : {}".format(projectHandle,traceback.format_exc())
        slack_notification(error_msg)
        return "-"


if __name__ == "__main__" :
    updateProjectsJSON()
    updateCommits()
    updatewatcherNo()
    updateProjectImage()
    updateForkNo()
    delJSONS.delJSON()
    conn.close()


