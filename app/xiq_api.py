#!/usr/bin/env python3
import logging
import os
import inspect
import sys
import json
import time
import requests
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
# date:         28 Aug 2025
# version:      3.0.0
####################################

logger = logging.getLogger('XIQ-AD-PPSK_Sync.xiq_api')

PATH = current_dir

class APICallFailedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class APICallRetryException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class XIQ:
    def __init__(self, user_name=None, password=None, token=None):
        self.URL = "https://api.extremecloudiq.com"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = "Bearer " + token
        else:
            try:
                self.__getAccessToken(user_name, password)
            except ValueError as err:
                print(err)
                raise SystemExit
            except HTTPError as err:
               print(err)
               raise SystemExit
            except Exception as err:
                log_msg = f"Failed to generate token for XIQ: {str(err)}"
                logger.error(log_msg)
                print(log_msg)
                raise SystemExit   
        self.pageSize = 100
        self.timeout = 14400 # 4 hours - if LRO runs longer than this the script will skip waiting for it to complete
        self.delete_attempts = 10 # number of attempts to delete PCG users

    #API CALLS
    def __get_api_call(self, url):
        try:
            rawResponse = requests.get(url, headers= self.headers)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        try:
            response = self.__checkResponse(rawResponse, url)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        return response
    
    def __post_api_call(self, url, payload):
        try:
            rawResponse = requests.post(url, headers= self.headers, data=payload)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        response = self.__checkResponse(rawResponse, url)
        return response
    
    ## LRO Call
    def __post_lro_call(self, url, payload):
        try:
            rawResponse = requests.post(url, headers=self.headers, data=payload)
        except requests.exceptions.ConnectionError as e:
            print(e)
        if rawResponse.status_code != 202:
            log_msg = f"Error - HTTP Status Code: {str(rawResponse.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = rawResponse.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{rawResponse.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"\n\n{data}")
            raise APICallFailedException(log_msg)
        data = rawResponse.headers
        # return the URL needed to check the status and collect data for the LRO
        return data['Location'], int(data['Retry-After'])
    
    def __delete_api_call(self, url, payload=None):
        try:
            rawResponse = requests.delete(url, headers= self.headers, data=payload)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        response = self.__checkDeleteResponse(rawResponse, url)
        return response
    
    def __checkResponse(self, rawResponse, url):
        if rawResponse is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if rawResponse.status_code not in [200, 201, 202]:
            log_msg = f"Error - HTTP Status Code: {str(rawResponse.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = rawResponse.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{rawResponse.text}")
            else:
                logging.warning(f"Full error details: {data}")
                if 'error_message' in data:
                    logging.warning(f"Error message from XIQ: {data['error_message']}")

            raise APICallFailedException(log_msg) 
        try:
            data = rawResponse.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(rawResponse.status_code)}")
            raise APICallFailedException("Unable to parse the data from json response")
        return data
    
    def __checkDeleteResponse(self, rawResponse, url):
        if rawResponse is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if rawResponse.status_code not in [200, 201, 202]:
            log_msg = f"Error - HTTP Status Code: {str(rawResponse.status_code)}"
            logger.error(f"{log_msg}")
            if rawResponse.status_code == 504:
                logger.error(rawResponse.text)
                raise APICallRetryException("Gateway Timeout - this may be a temporary issue")
            try:
                data = rawResponse.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{rawResponse.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"\n\n{data}")
            raise APICallFailedException(log_msg) 
        return 'Success'
    

    def __getAccessToken(self, user_name, password):
        info = "get XIQ token"
        success = 0
        url = self.URL + "/login"
        payload = json.dumps({"username": user_name, "password": password})
        try:
            data = self.__post_api_call(url=url,payload=payload)
        except APICallFailedException as e:
            print(f"API to {info} failed with {e}")
            print('script is exiting...')
            raise SystemExit
        else:
            success = 1
        if success != 1:
            print("failed to get XIQ token. Cannot continue to import")
            print("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data.get("access_token")
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg)

    #PPSK USER MANAGEMENT  
    def retrievePPSKUsers(self, usergroupID):
        """Retrieves multiple PPSK users via API using pagination."""
        page = 1
        pageCount = 1
        ppskUsers = []
        while page <= pageCount:
            # Get the next page of the ppsk users
            url = self.URL + "/endusers?page=" + str(page) + "&limit=" + str(self.pageSize) + "&user_group_ids=" + usergroupID
            try:
                rawList = self.__get_api_call(url=url)
            except APICallFailedException as err:
                raise APICallFailedException(err)
            except Exception as err:
                raise APICallFailedException(err)
            ppskUsers = ppskUsers + rawList.get('data')
            pageCount = rawList.get('total_pages')
            print(f"completed page {page} of {pageCount} collecting PPSK Users")
            page = rawList['page'] + 1 
        return ppskUsers

    def createPPSKUser(self, name, mail, usergroupID):
        """Create a single PPSK user via API."""
        info = "create PPSK user"    
        url = self.URL + "/endusers"
        payload = json.dumps({"user_group_id": usergroupID ,"name": name,"user_name": name,"password": "", "email_address": mail, "email_password_delivery": mail})
        try:
            data = self.__post_api_call(url=url,payload=payload)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        except Exception as err:
                raise APICallFailedException(err)
        logger.info(f"successfully created PPSK user {name}")
        return True
    
    def deletePPSKUser(self, userId):
        """Delete a single PPSK user via API."""
        url = self.URL + "/endusers/" + str(userId)
        try:
            response = self.__delete_api_call(url)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        except APICallRetryException as err:
            raise APICallRetryException(err)
        except Exception as err:
                raise APICallFailedException(err)
        return True
    
    #PCG User Management
    def __checkPCGUsersCount(self, policy_id):
        """Check the number of PCG users for a given policy."""
        url = self.URL + "/pcgs/key-based/network-policy-" + str(policy_id) + "/users?page=1&limit=1"
        try:
            rawData = self.__get_api_call(url=url)
        except APICallFailedException as err:
            raise APICallFailedException(f"API to retrieve PCG user count failed with {err}")
        except Exception as err:
            raise APICallFailedException(f"API to retrieve PCG user count failed with {str(err)}")
        return rawData.get('total_count')
    
    def retrievePCGUsers(self, policy_id):
        """Retrieves multiple PCG users via API using pagination."""
        page = 1
        pageCount = 1
        PCGUsers = []
        while page <= pageCount:
            # get the next page of the pcg users
            url = self.URL + "/pcgs/key-based/network-policy-" + str(policy_id) + "/users?page=" + str(page) + "&limit=" + str(self.pageSize)
            try:
                rawList = self.__get_api_call(url=url)
            except APICallFailedException as err:
                raise APICallFailedException(f"API to retrieve PCG users failed with {err}")
            except Exception as err:
                raise APICallFailedException(f"API to retrieve PCG users failed with {str(err)}")
            PCGUsers = PCGUsers + rawList.get('data')
            pageCount = rawList.get('total_pages')
            print(f"completed page {page} of {pageCount} collecting PCG Users for policy id {policy_id}")
            page = rawList['page'] + 1
        return PCGUsers

    def addPCGUsers(self, policy_id, pcg_users, user_group_name): 
        """Create multiple PCG users via API."""
        lro_running = True
        url = self.URL + "/pcgs/key-based/network-policy-" + str(policy_id) + "/users?async=true"
        payload = json.dumps({"users": [{"name": name, "email": email, "user_group_name": user_group_name} for name, email in pcg_users]})
        try:
            lro_url, retry_time = self.__post_lro_call(url=url,payload=payload)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        except Exception as err:
                raise APICallFailedException(err)
        # set a timeout for the LRO
        timeout_time = int(time.time()) + self.timeout
        data = None
        while lro_running:
            if retry_time < 3:
                logger.warning(f"Retry time of {retry_time} seconds is too low, setting to 30 seconds")
                logger.warning(f"LRO url: {lro_url}", extra={'file_only': True})
                retry_time = 30 # time in seconds
            print(f"LRO call in progress, waiting {retry_time} seconds before checking status")
            time.sleep(int(retry_time))
            rawData = self.__get_api_call(url=lro_url)
            if rawData['done'] == True:
                if 'error' in rawData:
                    logger.error("There was an error with the long-running operation:")
                    logger.error(f"Error: {rawData['error']['error_message']}")
                else:
                    logger.info("The long-running operation has completed successfully.")
                    data = None
                    data = rawData.get('response', {}).get('status') 
                lro_running = False # break the loop
            else:
                if rawData['metadata']['status'] != "RUNNING":
                    logger.error(f"It appears that the long-running operation failed. The status is {rawData['metadata']['status']}. Exiting wait loop.")
                    logger.error(json.dumps(rawData, indent=4))
                    lro_running = False # break the loop
                else:
                    print("The long-running operation is still running..")
                    if int(time.time()) >= timeout_time:
                        logger.warning("The long-running operation has exceeded the timeout time. Exiting wait loop.")
                        lro_running = False # break the loop
        if data:
            logger.debug(f"Creating PCG users took {int(time.time() - (timeout_time - self.timeout))} seconds")
            return True
        else:
            print("LRO failed")
            logger.error(rawData)
            raise APICallFailedException("LRO to add PCG users failed") 
    
    def deletePCGUsers(self, policy_id, pcg_users):
        """Delete multiple PCG users via API."""
        pre_count = int(self.__checkPCGUsersCount(policy_id))
        user_ids = [user_id for user_id, email in pcg_users]
        url = self.URL + "/pcgs/key-based/network-policy-" + str(policy_id) + "/users"
        payload = json.dumps({"user_ids": user_ids})
        delete_running = True
        attempts = 1
        while delete_running and attempts <= self.delete_attempts:
            try:
                data = self.__delete_api_call(url=url,payload=payload)
            except APICallFailedException as err:
                raise APICallFailedException(err)
            except APICallRetryException as err:
                logger.warning(f"Error occurred when deleting PCG users: {str(err)}.")
                print(f"Attempt {attempts + 1} of {self.delete_attempts}. Retrying in 60 seconds...")
                time.sleep(60) # wait a minute and try again
            except Exception as err:
                    raise APICallFailedException(err)
            else:
                time.sleep(30) # wait 30 seconds before checking the count again
                post_count = int(self.__checkPCGUsersCount(policy_id))
                if post_count != pre_count - len(pcg_users):
                    logger.warning(f"Not all PCG users were deleted successfully. Pre-delete count: {pre_count}, Post-delete count: {post_count}.")
                    print(f"Attempt {attempts} of {self.delete_attempts}.{' Retrying in 60 seconds...' if attempts < self.delete_attempts else ''}")
                    time.sleep(60) # wait a minute and try again
                else:
                    delete_running = False # break the loop
            attempts += 1
        if attempts >= self.delete_attempts:
            raise APICallFailedException("Failed to delete PCG users after multiple attempts.")
        return True