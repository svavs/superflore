# Instance of the ROS Overlay
from .repo_instance import repo_instance
import random
import string
import time
import os

def get_random_tmp_dir():
    return '/tmp/{0}'.format(''.join(random.choice(string.ascii_letters) for x in range(10)))

def get_random_branch_name():
    return 'gentoo-bot-{0}'.format(''.join(random.choice(string.ascii_letters) for x in range(10)))

class ros_overlay(repo_instance):
    def __init__(self):
        # clone repo into a random tmp directory.
        repo_instance.__init__(self, 'ros', 'ros-overlay', get_random_tmp_dir())
        self.branch_name = get_random_branch_name()        
        self.clone()
        repo_instance.info('Creating new branch {0}...'.format(self.branch_name))
        self.create_branch(self.branch_name)

    def clean_ros_ebuild_dirs(self, distro=None):
        if distro is not None:
            self.info('Cleaning up ros-{0} directory...'.format(distro))
            self.git.rm('-rf', 'ros-{0}'.format(distro))
        else:
            self.info('Cleaning up ros-* directories...')
            self.git.rm('-rf', 'ros-*')

    def commit_changes(self, distro):
        self.info('Adding changes...')
        if distro == 'all' or distro == 'update':
            self.git.add('ros-*')
        else:
            self.git.add('ros-{0}'.format(distro))
        commit_msg = {
            'update' : 'rosdistro sync, {0}',
            'all' : 'regenerate all distros, {0}',
            'lunar' : 'regenerate ros-lunar, {0}',
            'indigo' : 'regenerate ros-indigo, {0}',
            'kinetic' : 'regenerate ros-kinetic, {0}',
        }[distro].format(time.ctime())
        self.info('Committing to branch {0}...'.format(self.branch_name))
        self.git.commit(m='{0}'.format(commit_msg))

    def regenerate_manifests(self, mode):
        self.info('Generating manifests...')
        pid = os.fork()

        if pid == 0:
            if mode == 'all' or mode == 'update':
                os.chdir(self.repo_dir)
            else:
                os.chdir('{0}/ros-{1}'.format(self.repo_dir, mode))
            self.info('child: changed work directory to {0}'.format(os.getcwd()))
            os.execlp('sudo', 'sudo', 'repoman', 'manifest')
            self.error('Failed to run repoman!')
            self.error('Do you have permissions?')
            sys.exit(1)
        else:            
            if os.waitpid(pid, 0)[1] != 0:
                self.error('Manifest generation failed. Exiting...')
                sys.exit(1)
            else:
                self.happy('Manifest generation succeeded.')

    def pull_request(self, message):
        self.info('Filing pull-request for ros/ros-overlay...')
        pr_title = 'rosdistro sync, {0}'.format(time.ctime())        
        self.git.pull_request(m='{0}'.format(message), title='{0}'.format(pr_title))
        self.happy('Successfully filed a pull request with the ros/ros-overlay repo.')