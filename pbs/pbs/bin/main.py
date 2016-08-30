#!/usr/bin/env python

import commands
import os
import sys
import yaml
import requests
import urllib2
import shutil
import time
import subprocess
import argparse

from tqdm import tqdm

cwd=os.getcwd()


def run(cmd,chk_err=True):
    """
    Calls RunGetOutput on 'cmd', returning only the return code.
    If chk_err=True then errors will be reported in the log.
    If chk_err=False then errors will be suppressed from the log.
    """
    retcode=RunGetOutput(cmd,chk_err)
    print retcode,cmd
    return retcode

def RunGetOutput(cmd, chk_err=True, log_cmd=True):
    """
    Wrapper for subprocess.check_output.
    Execute 'cmd'.  Returns return code and STDOUT, trapping expected exceptions.
    Reports exceptions to Error if chk_err parameter is True
    """
    if log_cmd:
        print "Executing command : "+cmd
    try:
        output=subprocess.check_call(cmd,stderr=subprocess.STDOUT,shell=True)
    except subprocess.CalledProcessError,e :
        if chk_err and log_cmd:
            print 'CalledProcessError.  Error Code is ' + str(e.returncode)
            print 'CalledProcessError.  Command string was ' + e.cmd
        return e.returncode
    return 0

def parse_config(path):
  if os.path.exists(path):
    with open(path, "r") as f:
      return yaml.load(f)
  else:
    print "could not load lib file at %s" % path
    sys.exit(1)

def validate_uri(complete_uri):
  try:
    ret = urllib2.urlopen(complete_uri)
    if ret.code == 200:
      return 0
    else:
      return 1;
  except:
      return 1

def build_uri(dep,repoyml):
  repos = parse_config(repoyml);
  try:
    base_uri = repos[dep['repo']]['url']
    print " Base URI ::: ", base_uri
  except:
      print "URL not found in the yml for repo: "+dep['repo']
      sys.exit(1)
  complete_uri = base_uri + dep['name'][0] + '/' + dep['name']
  uri_true=validate_uri(complete_uri)
  if uri_true == 0:
      print " Download URI : " , complete_uri
      return complete_uri
  else:
      complete_uri = base_uri + dep['name']
      uri_true=validate_uri(complete_uri)
      if uri_true == 0:
        print " Download URI : " , complete_uri
        return complete_uri
      else:
        print " Not a valid Download link :"+ complete_uri
        sys.exit(1)


def download_package(name, pkg_path ,url):
  #widgets = [FormatLabel('Downloading ' + name + ': '), Percentage(), Bar()]
  print name
  print pkg_path
  print url
  deb = requests.get(url, stream=True)
  if not deb.status_code == requests.codes.ok:
    print 'Download deb Failed'
    print deb.status_code
    print deb.text
    sys.exit(1)

 # pbar = ProgressBar(maxval=10000, widgets=widgets).start() # TODO(JR): Fix the PB max value

  pbar = tqdm(total=4096)
  pbar.set_description("Downloading Package .... " + name + ":")
  try:
    if not os.path.exists(pkg_path):
      os.makedirs(pkg_path)

    with open(pkg_path+"/"+ name, 'wb') as f:
      for chunk in deb.iter_content(chunk_size=1024):
        pbar.update(12)
        if chunk: # filter out keep-alive new chunks
          f.write(chunk)
          f.flush()

    pbar.close()

  except Exception as e:
    print 'Download ' + name + ' Failed'
    print e

def setup_env(env):
  chroot_path="./"+os.path.join(env['target'])
  #Create a base folder for building the image
  create_folder(chroot_path,True)
  make_block_disk(chroot_path)
  return chroot_path

def unpack_pkg(pkgname,gz,chroot_path):
  print "Package " , pkgname
  if(gz):
    unpackstr = "cd %s; ar p %s data.tar.gz | tar xz "%(chroot_path, pkgname);
    print " UNPACKER : " , unpackstr
  else:
    unpackstr = "cd %s; ar p %s data.tar.xz | tar xJ "%(chroot_path, pkgname);
    print " UNPACKER : " , unpackstr
  cmd_exec = commands.getoutput(unpackstr)
  print cmd_exec

def create_folder(path,remove_if_present=False):
  if (os.path.exists(path) and remove_if_present):
    shutil.rmtree(path)

  if not os.path.exists(path):
    os.makedirs(path,0755);
  return path

def download_unpack(chroot_path,repoyml,group_manifest):
  count=0
  for deb in group_manifest:
      print " Downloading Deb :: " , deb
      # Download the package 
      count=count+1
      download_package(deb['dep']['name'].split('/')[-1], chroot_path ,build_uri(deb['dep'],repoyml))
      print " count " , count 

  time.sleep(10)
  count = unpack_package(chroot_path,repoyml,group_manifest)
  return count

def unpack_package(chroot_path,repoyml,group_manifest):
  # Unpack the package 
  count=0
  for deb in group_manifest:
      print " Unpacking Deb :: " , deb
      count=count+1
      unpack_pkg(deb['dep']['name'].split('/')[-1],deb['dep']['format']=='gz', chroot_path)
      print " count " , count 
  return count

def download_packages(chroot_path,repoyml,group_manifest):
    count=0
    print "executing download_packages: chroot_path:%s, repoyml:%s, group_manifest:%s"%(chroot_path, repoyml, group_manifest)
    for deb in group_manifest:
      print " Deb :: " , deb
      download_package(deb['dep']['name'].split('/')[-1], chroot_path ,build_uri(deb['dep'],repoyml))
      count=count+1
      print " Batch Count " , count 
    return count

def install(group_manifest, chroot_path, pkg_path, force_install):
  if force_install:
    force_str="--force-depends"
  else:
    force_str=""

  for deb in group_manifest:
    install_str="LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot %s /bin/bash -c \"dpkg %s --install  --force-overwrite %s/%s\""%(chroot_path,force_str,pkg_path,deb['dep']['name'].split('/')[-1])
    print install_str
    run(install_str)

def configure_all(chroot_path):
  print run("LANG=C chroot %s /bin/bash -c \"dpkg --configure -a\""%(chroot_path))

def touch_shadow(chroot_path):
  run("LANG=C chroot %s /bin/bash -c \"touch /etc/shadow\""%(chroot_path))
  run("LANG=C chroot %s /bin/bash -c \"touch /etc/gshadow\""%(chroot_path))

def bind_sys(chroot_path):
  run("mount -o bind /dev %s/dev"%(chroot_path))
  run("mount -o bind /dev/pts %s/dev/pts"%(chroot_path))
  run("mount -o bind /proc %s/proc"%(chroot_path))
  run("mount -o bind /sys %s/sys"%(chroot_path))

def download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs):
  count=download_packages(chroot_path,repoyml,group_manifest)
  os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
  install(group_manifest, chroot_path, pkg_path, False)
  configure_all(chroot_path)
  print "Count " ,count
  return count

def make_block_disk(chroot_path):
  raw_file="./tmp/output.raw"
  run("dd if=/dev/zero of=%s bs=512 count=5242880"%(raw_file))
  time.sleep(5) 
  loop_dev = commands.getoutput("losetup -f")
  print "Created loop device :"+loop_dev
  run("losetup %s %s"%(loop_dev,raw_file))
  run("mkfs.ext4 -L ProdNG %s"%(loop_dev))
  run("mount %s %s"%(loop_dev,chroot_path))

def extlinux(chroot_path):
  run("LANG=C chroot %s /bin/bash -c \"extlinux --install \\boot\""%(chroot_path))
  boot_path=os.path.join(chroot_path,"boot")
  conf_file=os.path.join(boot_path,"extlinux.conf")
  for file in os.listdir(boot_path):
    if file.startswith("initrd"):
      initrd=os.path.join("/boot",file)
      run("cd %s/boot; ln -s %s initrd.img"%(chroot_path,file))
    elif file.startswith("vmlinuz"):
      vmlinuz=os.path.join("/boot",file)
      run("cd %s/boot; ln -s %s vmlinuz"%(chroot_path,file))
  syslinux_file="""
  DEFAULT PRODNG \n
  LABEL PRODNG
    KERNEL vmlinuz
    APPEND rw initrd=initrd.img root=LABEL=ProdNG console=tty0 console=ttyS0,115200n8"""
  file = open(conf_file,"w")
  file.write(syslinux_file)
  file.close()

def reconfigure_all(chroot_path):
  pkg_list=commands.getoutput("LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot " + chroot_path + " dpkg -l | egrep 'all|amd' | awk {'print $2'} ").split()
  for pkg in pkg_list:
    print " reconfiguring pkg ",pkg
    reconfig_cmd="LANG=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true chroot " + chroot_path + " dpkg-reconfigure " + pkg
    run(reconfig_cmd)
  run(" echo \"US/Pacific\" > " + chroot_path+"/etc/timezone")    
  run(" chroot " + chroot_path+" dpkg-reconfigure -f noninteractive  tzdata")

def update_initramfs(chroot_path):
  run("chroot " + chroot_path + " update-initramfs -u")

def qemu_image_create():
  print "Doing image create"
  run("qemu-img convert -O vmdk ./tmp/output.raw ./tmp/output.vmdk")


def upload_image(version):
  """ 
  Load the openstack config for glance operations
  """
  env="ProdNG"
  yamlPath=cwd+"/openStack.yml"
  with open(yamlPath, 'r') as ymlfile:
   cfg = yaml.load(ymlfile)
   os.environ["OS_USERNAME"]=cfg[env]['OS_USERNAME']
   os.environ["OS_PASSWORD"]=cfg[env]['OS_PASSWORD']
   os.environ["OS_AUTH_URL"]=cfg[env]['OS_AUTH_URL']
   os.environ["OS_TENANT_NAME"]=cfg[env]['OS_TENANT_NAME']
   os.environ["OS_TENANT_ID"]=cfg[env]['OS_TENANT_ID']
   os.environ["OS_REGION_NAME"]=cfg[env]['OS_REGION_NAME']
   sys_time=int(time.time())
   append=""
   if ARGS['append']:
     append="_"+ARGS['append']
   image_name=env+"_"+ARGS['manifest']+"_"+version+append
   glance_upload="glance image-create --name "+  image_name + " " + " --disk-format vmdk --container-format bare  --file  ./tmp/output.vmdk"
   run(glance_upload)
   


def add_ppci(chroot_path):
  #PPCI binary is built by : gcc -Os ppci.cpp -L. -ljsoncpp -lstdc++ -o ppci,
  # after make installing jsoncpp to the env from here: https://github.com/open-source-parsers/jsoncpp
  """
  run("cp "+cwd+"/utils/ppci"+ " %s/root/"%(chroot_path))
  run("cp "+cwd+"/utils/ppci.sh"+ " %s/root/"%(chroot_path))
  """
  run("cp "+cwd+"/utils/rc.local"+ " %s/etc/"%(chroot_path))
  run("cp "+cwd+"/utils/fstab"+ " %s/etc/"%(chroot_path))
  run("mkdir %s/etc/prodng"%(chroot_path))
  if (ARGS['manifest'] != 'base' ) :
    run("cp "+cwd+"/utils/sources.list"+ " %s/etc/apt/"%(chroot_path))
    

  # Creating test usere TODO: remove these for production image
  run(("chroot " + chroot_path +" adduser --disabled-password --gecos \"\" prodngadmin"))
  create_folder(os.path.join(chroot_path,"home","prodngadmin",".ssh"))
  run("touch "+chroot_path+"/home/prodngadmin/.ssh/authorized_keys")
  run("cat "+cwd+"/ssh-key/rsynckey>>"+chroot_path+"/etc/prodng/prodng_key")
  run("chroot "+chroot_path +" chmod 600 /etc/prodng/prodng_key")
  run("cat "+cwd+"/ssh-key/id_rsa.pub>>"+chroot_path+"/home/prodngadmin/.ssh/authorized_keys")
  run("chroot "+chroot_path +" useradd -m -p paQVlNZJDlSzk -s /bin/bash prodngdev")
  run("echo \"prodngdev   ALL=(ALL) NOPASSWD: ALL\">>"+chroot_path+"/etc/sudoers")
  run("chroot "+chroot_path +" ln -s /etc/init.d/osqueryd /etc/rc3.d/S01osqueryd")
  run("echo \"prodngadmin   ALL=(ALL) NOPASSWD: ALL\">>"+chroot_path+"/etc/sudoers")
  configure_all(chroot_path)
  run("chroot " + chroot_path +" dpkg -l > "+chroot_path +"/etc/prodng/manifest.txt")
  run("chroot " + chroot_path +" dpkg -l " )
  
def cleanup(chroot_path,pkg_path_abs):
  #delete the packages folder
  shutil.rmtree(pkg_path_abs)

def test_chroot(chroot_path,count):
    status,output = commands.getstatusoutput("chroot "+chroot_path+" dpkg -l | wc -l")
    status2,output2 = commands.getstatusoutput("chroot "+chroot_path+" dpkg -l ")
    print " ######### "
    print output2
    print " ######### "
    if (status != 0 ) :
        print "Error getting package count in chroot"
        sys.exit(1)

    
    if (output == str(count+5) ) :
        print "Packages " , output
        print "All packages present!"
    else:
        print " final count " ,count
        print "Expected "+str(count+5)+", got ", output
        #sys.exit(1)

    status,output = commands.getstatusoutput("chroot "+chroot_path+" dpkg -l| sed 1,5d | awk '{print $1}'| uniq")
    if (status != 0 ) :
        print "Error getting installed package status"

    if "ii" == output:
        print "All packages installed correctly"
    else:
        print "Some packages failed to install. Here is the report :"
        status,output = commands.getstatusoutput("chroot "+chroot_path+" dpkg -l")
        print output
        sys.exit(1)
        
def initialize():
    global ARGS
    opts = argparse.ArgumentParser(description="Create the prodng bootstrapper", prog="PBS")
    opts.add_argument("--upload", help="Upload image to glance", action="store_true")
    opts.add_argument("-m", "--manifest", help="Manifest name: should be one of either \"dev\" \"c3\" or \"base\"", required=True, type=str, choices=['dev', 'base','c3'])
    opts.add_argument("--append", help="String to append to the image name", type=str, default="")
    ARGS = vars(opts.parse_args())
    global path
    path=cwd+"/"+ARGS['manifest']+".yml"
    
    
def main():
  initialize()
  manifest = parse_config(path)
  chroot_path=setup_env(manifest['env'])
  version=manifest['version']
  pkg_path = "packages"
  pkg_path_abs = os.path.join(chroot_path,pkg_path)
  create_folder(pkg_path_abs)
  count=0
  for dep in manifest['stages']:
    group = dep['dep']['group']
    artifact = dep['dep']['artifact']
    version = dep['dep']['version']
    group_manifest = parse_config(cwd+"/"+group + '/' + artifact + '.yml')
    repoyml = cwd+"/"+group+"/repo.yml"
    if group_manifest == None:
      print "THERE IS NOTHING HERE, YO"
      continue
    
    if "defaults" in artifact:
      print "\n\n####################  Installing the base packages  ############################\n\n"
      count=count+download_unpack(chroot_path,repoyml,group_manifest)
      #Move the packages to folder
      os.system("mv %s/*.deb %s"%(chroot_path,pkg_path_abs))
      os.system("cd %s; touch var/lib/dpkg/status"%(chroot_path))
    #Install all the packages with force-depends
    elif "stage1" in artifact:
      #Force install stage1 packages
      install(group_manifest, chroot_path, pkg_path, True)
      configure_all(chroot_path)
    elif "stage2" in artifact:
      print "\n\n####################  Installing the stage2 packages  ############################\n\n"
      # Install stage2 packages normally
      install(group_manifest, chroot_path, pkg_path, False)
      configure_all(chroot_path)
    elif "system" in artifact:
      print "\n\n####################  Installing the system packages  ############################\n\n"
      # Install system packages normally
      touch_shadow(chroot_path)
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "networking" in artifact:
      print "\n\n####################  Installing the netowrking packages  ############################\n\n"
      bind_sys(chroot_path)
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "development" in artifact:
      print "\n\n####################  Installing the development packages  ############################\n\n"
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "apt" in artifact:
      print "\n\n####################  Installing the apt packages  ############################\n\n"
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "git" in artifact:
      print "\n\n####################  Installing the git packages  ############################\n\n"
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "ldap" in artifact:
      print "\n\n####################  Installing the ldap packages  ############################\n\n"
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
    elif "physical" in artifact:
      print "\n\n####################  Installing the physical packages          ############################\n\n"
      count=count+download_install(chroot_path,repoyml,group_manifest,pkg_path,pkg_path_abs)
  extlinux(chroot_path)
  reconfigure_all(chroot_path) 
  update_initramfs(chroot_path)
  add_ppci(chroot_path)
  cleanup(chroot_path,pkg_path_abs)
  print "Sleeping for 2 min"
  time.sleep(120)
  test_chroot(chroot_path,count)
  qemu_image_create()
  if ARGS['upload']:
     upload_image(version)
if __name__ == "__main__":
  main()
