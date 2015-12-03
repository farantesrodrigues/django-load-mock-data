import glob
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
import psycopg2
import subprocess
from django.db import utils
import urlparse

# command to reinitialize the database
# it resets the db and then uses a node script to populate the db
data_path = os.path.abspath(os.path.join(os.getcwd(), './app/management/'))
print data_path


def flush_db():
    # asserting if we're running locally or in server
    if settings.DEBUG:
        try:
            conn = psycopg2.connect(database="db_name", user="username", password="pass", host="127.0.0.1", port="5432")
            print "Opened database successfully"
            cur = conn.cursor()
            cur.execute('''
                drop schema public cascade;
                create schema public;
            ''')
            print "Dropped public schema in cfinvest_dev database"
            conn.commit()
            conn.close()
        except:
            try:
                print "Couldn't connect to (LOCAL) database, trying django's flush command"
                subprocess.call("./manage.py flush", shell=True)
            except:
                raise CommandError('Couldn\'t flush current database')
    else:
        try:
            # in Heroku there's an env variable called DATABASE_URL and set automatically
            db_url = urlparse.urlparse(settings.DATABASE_URL)
            username = db_url.username
            password = db_url.password
            database = db_url.path[1:]
            hostname = db_url.hostname
            conn = psycopg2.connect(
                database=database,
                user=username,
                password=password,
                host=hostname
            )
            print "Opened database successfully"
            cur = conn.cursor()
            cur.execute('''
                drop schema public cascade;
                create schema public;
            ''')
            print "Dropped public schema in match_it (NON LOCAL) database"
            conn.commit()
            conn.close()
        except:
            try:
                print "Couldn't connect to (NON LOCAL) database, trying django's flush command"
                subprocess.call("./manage.py flush", shell=True)
            except:
                raise CommandError('Couldn\'t flush current database')


def make_migrations():
    try:
        subprocess.call("./manage.py makemigrations", shell=True)
        print "Finished making migrations"
    except:
        raise CommandError('Couldn\'t make migrations')


def migrate():
    try:
        subprocess.call("./manage.py migrate", shell=True)
        print "Finished migrating"
    except:
        raise CommandError('Couldn\'t migrate')


def create_superuser():
    try:
        User.objects.create_superuser(username='username', password='password', email='email@email.com')
        print "Finished saving superuser."
    except:
        raise CommandError('Couldn\'t create superuser')


def create_mock_data():
    if settings.DEBUG:
        for filename in glob.glob(data_path + '/mock_data*'):
            print "Removing file : %s" % filename
            os.remove(filename)
        try:
            subprocess.call("node ../mock-data/runner.js", shell=True)
        except:
            raise CommandError('Couldn\'t use node to create mock data')
    else:
        raise CommandError('Command is only available in Debug mode.')


def load_data():
    try:
        for filename in glob.glob(data_path + '/mock_data*'):
            print "Loading data from : %s" % filename
            load_command = "./manage.py loaddata " + filename
            subprocess.call(load_command, shell=True)
    except:
        raise CommandError('Couldn\'t load mock data')


class Command(BaseCommand):
    help = 'Resets the database with new contents from ./mock-data/mock_data.json'

    def handle(self, *args, **options):
        flush_db()
        make_migrations()
        migrate()
        create_superuser()
        if settings.DEBUG:
            create_mock_data()
        try:
            print "Loading data output from node process..."
            load_data()
        except utils.IntegrityError:
            print "Data file is not correctly generated. Might be corruption on model relationship."