"""This tool will SFTP into a server given a host name and user name.
It will allow users to get a file or directory(recursively) from source 
and copy the file to target location. 
It will also allow users to transfer files from between two SFTP servers.
Version 1.2
"""

import shutil
import pysftp
import os
from stat import S_ISDIR
import paramiko
import ntpath
from ftplib import FTP
import io
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from subprocess import check_output


class Move_Files():
    
    def __init__(self, host=None, username=None, password=None, pem=None, contype=None):
        self.host = host
        self.username = username
        self.password = password
        self.pem = pem
        if contype != None:
            self.contype = contype.lower()

    def sftp_connection(self):
        """"Hacky implementation of when a user does not give a password and no pem key. This is due to pysftps bug with not being able
        to handle this properly so moving back to paramiko to handle this type of connection
        """
        if self.password == "None" and self.contype == "sftp_p":
            client = paramiko.SSHClient()
            client.load_system_host_keys(r'C:\Users\L.Nguyen\Desktop\known_hosts')
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            client.connect(self.host, username=self.username, key_filename=self.pem, banner_timeout=60)
            sftp = client.open_sftp()
            return sftp
        elif self.contype == 'ftp':
            ftps = FTP(self.host)
            ftps.login(self.username, self.password)
            return ftps
        elif self.contype =='network':
            return shutil
        else:
            cnopts = pysftp.CnOpts()
            #cnopts.hostkeys.load(r'C:\Users\L.Nguyen\Documents\known_hosts')
            cnopts.hostkeys = None
            sftp = pysftp.Connection(self.host, username=self.username, password=self.password, cnopts=cnopts, private_key=self.pem)
            return sftp
   
    def append_date(self, target_file, ext):
        """Time stamps the target_file name with 
        dateformat _YYYY_MM_DD_HH_MI_S
        Also puts together the file with the extension
        to avoid breaking anything
        """
        now_ts = datetime.now().strftime('_%Y%m%d_%H%M%S')
        new_name = target_file+now_ts+ext
        return new_name
        

    def sftp_get(self, target, destination=None, match_pattern=None):
        """Given a target, will check if target is a file or directory.
        If it is a directory it will assume the user wants to download all files.
        If the target is a file it will only download the file.
        """
        sftp = self.sftp_connection()
        if os.path.isfile(target):
            #bugged only works on local 
            if self.contype == 'sftp':
                if destination != None:
                    #Checks if the user wants to download the file to a specific directory
                    sftp.get(target, localpath=destination)
                    sftp.close()
                else:
                    #if no directory is given it the code will download the file to where the script is located
                    sftp.get(target)
                    sftp.close()
            elif self.contype == 'network':
                #Copies a file from one path locally to another path locally or on the network drive
                shutil.copy(target, destination)
        elif os.path.isdir(target):
            if self.contype == 'sftp':
                    #this is a recursive function that will go through all directories and subdirectories and download them to the supplied destination
                    sftp.get_r(target, destination, preserve_mtime=True)
                    sftp.close()
            elif self.contype == 'network':
                shutil.copytree(target, destination)
        else:
            if match_pattern != None:
                for fileattr in sftp.listdir_attr(os.path.dirname(target)):
                    if fnmatch(fileattr.filename, os.path.basename(target)+'*'):
                        sftp.chdir(os.path.dirname(target))
                        sftp.get(fileattr.filename, localpath=os.path.join(destination, fileattr.filename))
    
    def download_dir(self, target_dir, destination_dir):
        """Downloads a directory from the server to a the specific path given by the user
        """
        sftp = self.sftp_connection()
        os.path.exists(destination_dir) or os.makedirs(destination_dir)
        dir_items = sftp.listdir_attr(target_dir)
        for item in dir_items:
            # assuming the local system is Windows and the remote system is Linux
            # os.path.join won't help here, so construct remote_path manually
            remote_path = target_dir + '/' + item.filename         
            local_path = os.path.join(destination_dir, item.filename)
            if S_ISDIR(item.st_mode):
                self.download_dir(remote_path, local_path)
            else:
                sftp.get(remote_path, local_path)

    def sftp_target_src(self, target, destination=None, append_date=False):
        """
        When copying files to target make sure to specify file name after destiation or else it wont work
        Copies target file to the cwd on the server preserving modification time
        """
        sftp = self.sftp_connection()
        base_filename = os.path.basename(os.path.splitext(target)[0])
        ext = os.path.splitext(target)[1]
        if self.contype == 'ftp':
            sftp.cwd(destination)
            if append_date != False:
                base_filename = self.append_date(base_filename,ext)
            if ext in ('.txt', '.htm', '.html', '.csv'):
                sftp.storlines('STOR ' + base_filename, open(target, 'rb'))
            else:
                sftp.storbinary('STOR ' + base_filename, open(target, 'rb'), 1024)
        elif destination != None:
            if append_date != False:
                base_filename = self.append_date(base_filename,ext)
            sftp.put(target, remotepath=os.path.join(destination,base_filename+ext))
            # sftp://144.160.149.152/m10375
            sftp.close()
        else:
            sftp.put(target)
            sftp.close()

    def archive_files(self, target_file, target_destination=None, append_date=False, current_directory=None):
        """
        Archive method that moves the file into an archive folder either in the same directory or up one from the parent directory
        Arguments: 
        target_file(The file that is to be moved) 
        target_destination(If you want to move the file to a specific directory then specify the full path)
        append_date(If you want the file to be time stamped when the file was moved)
        current_directory(If the archive folder is in the same directory as the file) 
        """
        if target_destination == None:
            file_path,ext = os.path.splitext(target_file)
            directory = Path(os.path.dirname(file_path))
            basename = os.path.splitext(os.path.basename(target_file))[0]
            parent = Path(directory).parent
            baseWithDate = self.append_date(basename,ext)
            if append_date != False and current_directory != None:
                #Archive is one folder above the current folder due to .parent
                shutil.move(target_file, str(directory)+'\Archive\\'+baseWithDate)
            elif append_date != False and current_directory == None:
                shutil.move(target_file, str(parent)+'\Archive\\'+baseWithDate)
            elif append_date == False and current_directory != None:
                shutil.move(target_file, str(directory)+'\Archive\\'+basename+ext)
            else:
                shutil.move(target_file, str(parent)+'\Archive\\'+basename+ext)
        else:
            shutil.move(target_file, target_destination)
    
    def check_connectivity(self):
        sftp = self.sftp_connection()
        sftp.listdir_attr()
        sftp.close()
    
    def email(self, email_address, email_message, subject):
        """Emails users the message using the smtp server
        Arguments: email_address(needs to be a list), email_message(str), subject(str)
        Returns: None
        """
        msg = MIMEMultipart()
        recipients = [i for i in email_address]
        message = email_message
        msg['From'] = 'python@dtr-python-script.cydcor.com'
        msg['To'] = ';'.join(recipients)
        print(';'.join(recipients))
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP('smtp.cydcor.com')
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

    def check_locked_status(self, path):
        #Checks to see if the file is locked by any processes before performing an action on the file
        result = check_output(r'2>nul (>> "{}" (call ) ) && (echo file is not locked) || (echo file is locked)'.format(path), shell=True).decode()
        return result.rstrip()


def find_credentials(config, *args):
    """Helper to find the correct credentials when given a host name and username
    
    Arguments: configuration file(Should be in JSON format), host and username
    Returns: password, type of connection, username

    """
    creds = {}
    for i in config:
        for arg in args:
            if arg == i['host']:
                creds = {'host': i['host']}
        for j in i['users']:
            if creds.get('host') == i['host'] and arg == j['username']:
                creds.update({'password': j['password'], 'type': i['type'],'pem': j['ppk'], 'username': j['username']})
    return creds
