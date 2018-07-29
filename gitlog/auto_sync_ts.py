#!/usr/bin/env python
# encoding: utf-8
import os,sys
os.system("/bin/launchctl setenv PATH $PATH:/usr/local/bin:/usr/bin:/bin")
path = os.path.split(os.path.realpath(__file__))[0]
client_script_trunk_path = os.path.join(path,'client-trunk/client-refactory/Develop/Assets/Resources/Script')
client_script_studio_path = os.path.join(path,'client-branches/Studio/client-refactory/Develop/Assets/Resources/Script')
# client_script_tf_path = os.path.join(path,'client-branches/TF/client-refactory/Develop/Assets/Resources/Script')
# client_script_release_path = os.path.join(path,'client-branches/Release/client-refactory/Develop/Assets/Resources/Script')


os.system("svn revert -R %s %s"%(client_script_trunk_path,\
                                        client_script_studio_path))

cm = "svn st %s| grep '^?' | awk '{print $2}' | xargs rm -rf"
cm1 = "svn st %s| grep '^!' | awk '{print $2}' | xargs svn rm"
cm2 = "svn st %s| grep '^?' | awk '{print $2}' | xargs svn add"

rm_cm = cm%(client_script_trunk_path)
os.system(rm_cm)

rm_cm = cm%(client_script_studio_path)
os.system(rm_cm)

os.system("svn up %s %s"%(client_script_trunk_path,\
                                        client_script_studio_path))

#############region config 更新生成 start 
#############region config 更新生成 end 

#############region svn_sync 更新生成 start

#需要删除svn 新增的文件但是git 目前还没有的文件，（svn 已加，git pull 已加则会产生冲突 可以删除先）

# trunk
os.chdir(client_script_trunk_path)

headVersionCmd = "git rev-parse --short HEAD"
ver1=os.popen(headVersionCmd).read()
ver1 = ver1.replace("\n","")

os.system("svn revert -R .")
os.system("git checkout .")
os.system("git clean -fd")
os.system("git pull")
os.system("git checkout Trunk\(svn\)")
# rm_cm = cm%(client_script_trunk_path)
svn_rm_cm = cm1%(client_script_trunk_path)
svn_add_cm = cm2%(client_script_trunk_path)

# os.system(rm_cm)
os.system(svn_rm_cm)
os.system(svn_add_cm)

ver2=os.popen(headVersionCmd).read()
ver2 = ver2.replace("\n","")
logDesccmd = "git log %s..%s"%(ver1,ver2)
logDesccmd = logDesccmd+" --pretty=\"author:%an,desc:%s\""
logContent=os.popen(logDesccmd).read()

commitCmd = "svn ci -m \"%s\" %s"%(logContent,client_script_trunk_path)
os.system(commitCmd)

#studio
os.chdir(client_script_studio_path)

ver1=os.popen(headVersionCmd).read()
ver1 = ver1.replace("\n","")

os.system("svn revert -R .")
os.system("git checkout .")
os.system("git clean -fd")
os.system("git pull")
os.system("git checkout Studio\(svn\)")
# rm_cm = cm%(client_script_studio_path)
svn_rm_cm = cm1%(client_script_studio_path)
svn_add_cm = cm2%(client_script_studio_path)
# os.system(rm_cm)
os.system(svn_rm_cm)
os.system(svn_add_cm)


ver2=os.popen(headVersionCmd).read()
ver2 = ver2.replace("\n","")
logDesccmd = "git log %s..%s"%(ver1,ver2)
logDesccmd = logDesccmd+" --pretty=\"author:%an,desc:%s\""
logContent=os.popen(logDesccmd).read()

commitCmd = "svn ci -m \"%s\" %s"%(logContent,client_script_studio_path)
os.system(commitCmd)

# #tf
# os.chdir(client_script_tf_path)
# os.system("svn revert -R .")
# os.system("git checkout .")
# os.system("git pull")
# os.system("git checkout TF\(svn\)")
# add_cm = cm%(client_script_tf_path)
# rm_cm = cm1%(client_script_tf_path)
# os.system(rm_cm)
# os.system(add_cm)
# os.system("svn ci -m \"svn sync tf from git\" "+client_script_tf_path)

# # #release
# os.chdir(client_script_release_path)
# os.system("svn revert -R .")
# os.system("git checkout .")
# os.system("git pull")
# os.system("git checkout Release\(svn\)")
# add_cm = cm%(client_script_release_path)
# rm_cm = cm1%(client_script_release_path)
# os.system(rm_cm)
# os.system(add_cm)
# os.system("svn ci -m \"svn sync release from git\" "+client_script_release_path)

#############region svn_sync 更新生成 end