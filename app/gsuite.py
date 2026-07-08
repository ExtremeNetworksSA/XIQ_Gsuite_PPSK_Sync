#!/usr/bin/env python3
import logging
import os
import inspect
import sys
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from gsuite_test import check_token
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from requests.exceptions import HTTPError
from app.logger import logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
####################################
# written by:   Tim Smith
# e-mail:       tismith@extremenetworks.com
# date:         15 Jun 2026
# version:      3.0.0
####################################

logger = logging.getLogger('XIQ-AD-PPSK_Sync.gsuite_api')

PATH = current_dir
class GAPIFailedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
class GSuite:
    def __init__(self, gs_domain):
        self.gs_base_url = 'https://admin.googleapis.com/admin/directory/v1'
        self.gs_group_url = f"{self.gs_base_url}/groups"
        self.gs_user_url = f"{self.gs_base_url}/users"
        self.gs_domain = gs_domain

        self.SCOPES = [
            'https://www.googleapis.com/auth/admin.directory.group.readonly',
            'https://www.googleapis.com/auth/admin.directory.group.member.readonly',
            'https://www.googleapis.com/auth/admin.directory.user.readonly'
        ]
        self.header = {"Accept": "application/json", "Content-Type": "application/json"}
            # Validate and refresh GSuite token
        try:
            self.__check_token()
        except ValueError as err:
            print(err)
            print("script exiting....")
            raise SystemExit
        except:
            log_msg = "Failed to Authenticate with GSuite - Unknown reason"
            logger.error(log_msg)
            print("script is exiting....")
            raise SystemExit
        
    #API CALLS
    def __check_token(self):
        if os.path.exists('gsuite_token.json'):
            cred = Credentials.from_authorized_user_file('gsuite_token.json', self.SCOPES)
        else:
            log_msg = "gsuite_token.json was not found. Please run the 'gsuite_setup.py' script to authorize the gsuite API and receive an API token."
            logger.error(log_msg)
            raise ValueError(log_msg)
        if not cred.valid:
            if cred.expired and cred.refresh_token:
                try:
                    cred.refresh(Request())
                except RefreshError as e:
                    log_msg = f"Failed to refresh GSuite Token with - {e}"
                    logger.error(log_msg)
                    raise ValueError(log_msg)
            else:
                log_msg = "gsuite_token.json isn't valid. Please rerun the 'gsuite_setup.py script and test again."
                logger.error(log_msg)
                raise ValueError(log_msg)
        self.header['Authorization'] = "Bearer " + cred.token

    def __getGSGroupID(self,gs_groupname):
        url = self.gs_group_url + '?domain=' + self.gs_domain + "&query=name='" + gs_groupname + "'"
        response = requests.get(url, headers=self.header, verify=True)
        data = response.json()
        if 'error' in data:
            log_msg = data['error']['message']
            raise GAPIFailedException(log_msg)
        if 'groups' in data:
            found_group = False
            for group in data['groups']:
                if group['name'] == gs_groupname:
                    return group['id']
            if found_group == False:
                logmsg = f"Group '{gs_groupname}' was not found in domain {self.gs_domain}"
                raise GAPIFailedException(logmsg)
        else:
            logmsg = f"No group was found in domain {self.gs_domain}"
            raise GAPIFailedException(logmsg)

    def retrieveGSUsers(self, gs_groupname):
        try:
            group_id = self.__getGSGroupID(gs_groupname)
        except GAPIFailedException as e:
            raise GAPIFailedException(e)
        except:
            raise GAPIFailedException(f"Unknown issue collecting the group ID for {gs_groupname}")

        gsUsers = []
        gs_member_url = self.gs_group_url + "/" + str(group_id) + "/members?includeDerivedMembership=true"
        checkForUsers = True
        pageToken = ''
        while checkForUsers:
            if pageToken:
                url = gs_member_url + "&pageToken=" + pageToken
            else:
                url = gs_member_url
            response = requests.get(url, headers=self.header, verify=True)
            if response == None:
                raise GAPIFailedException("no response!")
            elif response.status_code != 200:
                log_msg(f"Error retrieving Gsuite users - HTTP Status Code: {str(response.status_code)}")
                logger.warning(f"{response.json()}")
                raise GAPIFailedException(log_msg)
            rawData = response.json()
            if 'nextPageToken' in rawData:
                pageToken = rawData['nextPageToken']
            else:
                checkForUsers = False
            if 'members' in rawData:
                gsUsers = gsUsers + rawData['members']
        for user in gsUsers:
            if user['type'] == 'USER':
                user['name'] = self.__updateUserInfo(user)
            else:
                log_msg = f"{user['email']} is type {user['type']} and not a user. Skipping group member."
                logger.info(log_msg)

        gsUsers[:] = [x for x in gsUsers if x['type'] == 'USER']

        return gsUsers

    def __updateUserInfo(self,user):
        url = self.gs_user_url + "/" + str(user['id'])
        response = requests.get(url, headers=self.header, verify=True)
        data = response.json()
        return data['name']['fullName']