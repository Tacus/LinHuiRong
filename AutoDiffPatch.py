#!/usr/bin/env python
# encoding: utf-8

import os,sys,getopt,subprocess,commands,logging

def printW(str):
	print '\033[1;31;1m'
	logging.warn(str)
	print '\033[0m'

def printR(str):
	print '\033[1;31;1m'
	print str
	print '\033[0m'

def printInfo(str):
	print str

def usage():
	print " -s:合并的开始版本号（默认本地最新版本-1000）\n -e:结束的版本号（默认本地最新）\n -f:合并的源分支（默认当前dash工作路径）\n -t:合并的目标分支（必填）"
	# pass
opts,argvs = getopt.getopt(sys.argv[1:],"s:e:f:t:h")
startVersion = -1
endVersion = -1
newestVersion = -1
# fromDir = commands.getoutput("pwd")
fromDir = os.getcwd()
targetDir = fromDir
auth = "shabi"

for opt,value in opts:
	if opt == "-s":
		startVersion = value
	elif opt == "-e":
		endVersion = value
	elif opt == "-f":
		fromDir = value
	elif opt == "-t":
		targetDir = value
	elif opt == "-h":
		usage()
		exit()

os.chdir(fromDir)

# cmd = "svn update"
# result = os.system(cmd)
# print result

cmd='svn auth | grep Username | awk \'{print $2}\''

auth = commands.getoutput(cmd)

cmd = "svn info | grep Revision| cut -d ' ' -f 2"

newestVersion = commands.getoutput(cmd)


if startVersion == -1:
	startVersion = int(newestVersion) - 1000
	printW("no start version;will use " + str(startVersion)+" (HEAD -1000)")

if endVersion == -1:
	endVersion = 'HEAD'

cmd='svn log -r'+str(startVersion)+":"+newestVersion+" |grep "+auth +" | awk '{print $1}'"
stdout = commands.getoutput(cmd)
if(stdout == ""):
	printW("can't find changes from revision {0} to {1}".format(startVersion,endVersion))
	exit()

printR( "startVersion:{0},\nendVersion:{1},\nnewestVersion:{2},\nauthor:{3},\nfromDir:{4},\ntargetDir:{5}".format(startVersion,endVersion,newestVersion,auth,fromDir,targetDir))

revs = stdout.split("\n")

index = 1
patchFiles = []
printR( "start diff...")

patchDir = os.path.join(os.environ['HOME'],"Desktop/patchFils/")
if(not os.path.exists(patchDir)):
	os.makedirs(patchDir)

for rev in revs:
	cmd = "echo "+rev+" |cut -c 2- "
	rev = commands.getoutput(cmd)
	patchFileName = "{0}.patch".format(str(rev))
	patchFileName = os.path.join(patchDir, patchFileName)
	patchFiles.append(patchFileName)
	cmd = "svn diff -r"+str(int(rev) -1)+":"+rev +">"+patchFileName 
	result = commands.getoutput(cmd)
	index = index +1

printR( "start patch...")
os.chdir(targetDir)
cmd = "pwd"
result = commands.getoutput(cmd)

conflictsPatchs = []
for patchFile in patchFiles:

	cmd = "svn patch " + patchFile
	printR(cmd)
	result = commands.getoutput(cmd)
	printInfo( result)
	if(result.find("conflicts") != -1):
		conflictsPatchs.append(patchFile)
	else:
		cmd = "rm -f " + patchFile
		commands.getoutput(cmd)
strs = "统计：未完全成功的patch文件"
if(len(conflictsPatchs)>0):	
	for conflict in conflictsPatchs:
		strs = strs + conflict+"、"
	printR(strs)