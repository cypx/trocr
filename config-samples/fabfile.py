from fabric.api import env, run, cd, roles, sudo

env.roledefs = {
    'prod': ['user@prod_server'],
    'dev': ['user@dev_server'],
}

project_dir = {
    'prod': '/var/www/trocr',
    'dev': '/home/user/www/trocr',
}

def deploy():
    with cd(project_dir[env.roles[0]]):
        run('virtualenv --no-site-packages ./')
        run('curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1')
        run('cp websiteconfig.py.sample websiteconfig.py')
        run('source ./bin/activate && pip install -Ur requirements.txt')
        sudo('/etc/init.d/uwsgi reload')

def update():
    with cd(project_dir[env.roles[0]]):
	run('curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1')
	sudo('/etc/init.d/uwsgi reload')

@roles('demo-dev')
def reset_dev():
    with cd(project_dir[env.roles[0]]):
	run('rm *')
	run('rm -rf data thumbnail')
        run('curl -L https://github.com/cypx/trocr/archive/master.tar.gz | tar zx --strip-components=1')
        run('cp websiteconfig.py.sample websiteconfig.py')
