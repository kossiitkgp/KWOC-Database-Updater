import requests
import traceback 
import json 
import os
from pprint import pprint
from datetime import datetime
import time 

def get_commitsOnline(username, repo_name):
    '''
    username : 'kshitij10496'
    repo_name : 'kshitij10496/IIKH'
                'sympy/sympy'
    '''
    # total_commits = 0
    # total_additions, total_deletions, total_changes = 0, 0, 0
    
    # user = g.get_user(username)
    # repo = g.get_repo(repo_name)
    # starting_date = datetime.datetime(2016, 5, 1)
    # ending_date = datetime.datetime(2016, 12, 31)
    # all_commits = repo.get_commits(author=username)#, since=starting_date, until=ending_date)
    # for commit in all_commits:
    #     total_additions += int(commit.stats.additions)
    #     total_deletions += int(commit.stats.deletions)
    #     total_changes += int(commit.stats.total)
    #     total_commits += 1
    # # return total_commits
    # print("Total commits: " + str(total_commits))
    # print("Total additions: " + str(total_additions))
    # print("Total deletions: " + str(total_deletions))
    # print("Total changes: " + str(total_changes))
    query = "https://api.github.com/repos/{}/stats/contributors?access_token={}".format(repo_name,os.environ["DEFCON_GITHUB_AUTH_TOKEN"])
    response = requests.get(query).json()
    commits = 0
    try :
        for data in response :
            if data["author"]["login"].lower() == username.lower() :
                commits+=int(data["total"])
        return commits 
    except TypeError :
        msg = "Unable to get commits in {} repo.\nFollowing error occured : {}".format(repo_name,traceback.format_exc())
        slack_notification(msg)
        return 0

def getProjectsJson(repo) :
    query = "https://api.github.com/repos/{}/stats/contributors?access_token={}".format(repo,os.environ["DEFCON_GITHUB_AUTH_TOKEN"])
    print ("Getting details for {}".format(repo))
    try :
        time.sleep(2)
        response = requests.get(query).json()
        if isinstance(response,dict):
            # pprint(response)
            time.sleep(20)
            response = requests.get(query).json()
            if isinstance(response,dict):
                slack_notification("Unable to get commits of {} \n\nGot the following response : {}".format(repo,response))
                return -1
        json.dump(response,open("projectsJSON/{}.json".format(repo.replace("/",".")) , "w"))
    # pprint (response)
    except :
        slack_notification("Got following error {} \n\n {}".format(traceback.format_exc()))
        return -1
    

def getCommitsOffline(studentHandle,repo) :
    allCommits = json.load(open("projectsJSON/{}.json".format(repo.replace("/",".")) , "r"))
    dec1Timestamp = datetime.fromtimestamp(1480204800)
    commits = 0
    try :
        for data in allCommits :
            if data["author"]["login"].lower() == studentHandle.lower() :
                for week in data["weeks"] :
                    if dec1Timestamp <= datetime.fromtimestamp(int(week['w'])) :
                        if int(week["c"]) :
                            print ("Got {} commits for {} in {}".format(int(week["c"]),studentHandle,repo))
                        commits+=int(week["c"])
        return commits 
    except TypeError :
        return 0 
        pass 
    except : 
        # pprint (allCommits)
        msg = "Unable to get commits for {} in {}.\nFollowing error occured : {}".format(studentHandle,repo,traceback.format_exc())
        slack_notification(msg)
        # print (msg)
        return 0   


def slack_notification(message):
        headers = {
                "Content-Type": "application/json"
        }
        data = json.dumps({
                "text": "In leaderboard.py from KWOC database updater  following error occured :\n{}".format(message)
        })
        r = requests.post(
                os.environ["SLACK_WEBHOOK_URL"], headers=headers, data=data)

        if r.status_code != 200:
                print("in slack_notification : {}".format(r.status_code))
                print(message)
                print(r.text)
if __name__ == '__main__':
    print getCommitsOffline('AvijitGhosh82', 'AvijitGhosh82/material-chess-android')