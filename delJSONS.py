import shutil
import os

def delJSON() :
	curr_path =os.getcwd()
	JSONpath = curr_path + "/projectsJSON" 
	print (JSONpath)
	shutil.rmtree(JSONpath)
	os.mkdir(JSONpath)

if __name__ == "__main__" :
	delJSON()
