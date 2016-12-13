import shutil
import os

def delJSON() :
	curr_path =os.getcwd()
	JSONpath = curr_path + "/projectsJSON" 
	print (JSONpath)
	shutil.rmtree(dirpath)
	os.mkdir(dirpath)
