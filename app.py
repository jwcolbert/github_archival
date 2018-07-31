#!/usr/bin/env python

import json
import subprocess
import re
from github import Github
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-o", "--org",
                    help="Organization to archive", required=True)
parser.add_argument("-u", "--user",
                    help="GitHub UserName", required=True)
parser.add_argument("-p", "--password",
                    help="GitHub Password", required=True)

args = vars(parser.parse_args())

org = args["org"]
user = args["user"]
password = args["password"]

#Retrieve all repositories

#Retrieve Github Instance
g = Github(user, password)

#Loop Through Repos
for repo in g.get_organization(org).get_repos():
    mirror = subprocess.Popen(['git', 'clone', '--mirror', repo.ssh_url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = mirror.communicate()[0].decode('utf-8')
    repodir = ''.join(re.findall(r"'(.*?)'", output, re.DOTALL))
    tarname = org + "_" + repodir + ".tar.gz"
    print("Creating " + tarname)
    tar = subprocess.Popen(['/usr/bin/tar', '-czf', tarname, repodir])
    tar.wait()
    remove = subprocess.Popen(['rm', '-rf', repodir])
    s3_dest = "s3://github-archives/" + tarname
    backup = subprocess.Popen(['s3cmd', 'put', tarname, s3_dest])
    backup_success = backup.communicate()[0]
    if backup.returncode != 0:
        print("Error Backing up " + tarname)
        exit
    else:
        if repo.private:
            print("Deleting Private Repo: " + repo.name)
            repo.delete()
        else:
            print("Public Repo, not deleting")
