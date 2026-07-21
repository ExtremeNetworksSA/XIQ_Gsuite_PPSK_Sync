#!/usr/bin/env python3
import sys
import logging
from collections import defaultdict
from app.logger import logger
from app.xiq_api import XIQ, APICallFailedException
from app.gsuite import GSuite, GAPIFailedException
# other imports
logger = logging.getLogger('XIQ-GSuite-PPSK_Sync.Main')

####################################
# written by:   Tim Smith
# e-mail:       tismith@extremenetworks.com
# date:         15 June 2026
# version:      3.0.1
####################################

# Global Variables - ADD CORRECT VALUES
gs_domain = 'Domain Name'

#XIQ MaxPageSize (max is 100)
pageSize = 100

#XIQ_username = "enter your ExtremeCloudIQ Username"
#XIQ_password = "enter your ExtremeCLoudIQ password"
####OR###
## TOKEN permission needs - enduser, pcg:key, lro
XIQ_token = "****"

group_roles = [
    # GSuite GROUP Name, XIQ group ID
    ("GSuite GROUP Name", "XIQ group ID"),
    ("GSuite GROUP Name", "XIQ group ID")
]

PCG_Enable = False

PCG_Mapping = {
    "XIQ User Group ID" : {
        "UserGroupName": "XIQ User Group Name",
        "policy_id": "Network Policy ID associated with PCG",
         "policy_name": "Network Policy name associated with PCG"
    }
}


extended_username_format = False # Set to True if you want to use the extended username format for PPSK users. 
# If True, name would be <Google username>_<email>
# If False, the name would be just the <Google username>


def get_ppsk_user_id_by_email(ppsk_users, email):
    for user in ppsk_users:
        if user.get('email_address') == email:
            return user.get('id')
    logger.info(f"No PPSK user found with email {email}", extra={'file_only': True})
    return None

def get_ppsk_user_group_by_id(ppsk_users, user_id):
    for user in ppsk_users:
        if user.get('id') == user_id:
            return user.get('user_group_id')
    logger.info(f"No PPSK user found with ID {user_id}", extra={'file_only': True})
    return None

def get_pcg_user_id_by_email(pcg_users, email):
    for user in pcg_users:
        if user.get('email') == email:
            return user.get('id')
    logger.info(f"No PCG user found with email {email}", extra={'file_only': True})
    return None



def main():
    if 'XIQ_token' not in globals():
        try:
            x = XIQ(username=XIQ_username,password=XIQ_password)
        except:
            print(f"API to create XIQ session failed with {e}")
            print("exiting script...")
            raise SystemExit
    else:
        x = XIQ(token=XIQ_token)
 
    ListOfGSgroups, ListOfXIQUserGroups = zip(*group_roles)

    # Collect PPSK users
    ppsk_users = []
    for usergroupID in ListOfXIQUserGroups:
        try:
            ppsk_users += x.retrievePPSKUsers(usergroupID)
        except APICallFailedException as err:
            logger.error(f"API to retrieve PPSK users failed with {err}")
            print("script exiting....")
            raise SystemExit
    logger.info("Successfully parsed " + str(len(ppsk_users)) + " XIQ users")

    # Collect PCG Users if enabled
    if PCG_Enable == True:
        pcg_capture_success = True
        pcg_users = []
        for pcg_policy in PCG_Mapping.values():
            try:
                pcg_users += x.retrievePCGUsers(pcg_policy['policy_id'])
            except APICallFailedException as err:
                pcg_capture_success = False
                logger.error(f"API to retrieve PCG users failed with {err}")
                continue
            logger.info(f"Successfully parsed {len(pcg_users)} PCG users from policy {pcg_policy['policy_name']}")

    # load Gsuite API
    gsuite = GSuite(gs_domain)
    #Collect Gsuite Users
    gs_users = {}
    gs_capture_success = True
    for gs_group_name,xiq_user_role in group_roles:
        try:
            gs_results = gsuite.retrieveGSUsers(gs_group_name)
        except GAPIFailedException as e:
            print(e)
            print("script exiting....")
            raise SystemExit
        except:
            log_msg = ("Unknown Error: Failed to retrieve users from Gsuite")
            print(log_msg)
            print("script exiting....")
            raise SystemExit
        for gs_entry in gs_results:
            if extended_username_format:
                username = f"{gs_entry['name']}_{gs_entry['email']}"
            else:
                username = gs_entry['name']
            if username not in gs_users:
                try:
                    gs_users[username] = {
                        "accountEnabled": True if (gs_entry['status']=='ACTIVE') else False,
                        "email": gs_entry['email'],
                        "username": gs_entry['email'],
                        "xiq_role": xiq_user_role
                    }
                except:
                    log_msg = (f"Unexpected error: {sys.exc_info()[0]}")
                    print(log_msg)
                    gs_capture_success = False
                    continue
    logger.info("Successfully parsed " + str(len(gs_users)) + " GSuite users")


    batch_size = 100 # batch count for PCG users if enabled

    # Precompute sets for O(1) lookups
    current_ppsk_user_names = {d.get('user_name') for d in ppsk_users if isinstance(d, dict) and 'user_name' in d }
    current_pcg_user_names = {d.get('name') for d in pcg_users if isinstance(d, dict) and 'name' in d } if PCG_Enable else set()   

    # Track Error counts
    ppsk_create_error = 0
    pcg_create_error = 0
    ppsk_del_error = 0
    pcg_del_error = 0

    # Make a list of PPSK users to create
    ad_disabled = []
    new_ppsk_users = []
    pcg_batch = defaultdict(list) if PCG_Enable else None  # List to collect successful PPSK users for PCG

    # Step 1: Identify new users for PPSK
    for name, details in gs_users.items():
        # Safely access email and accountEnabled status
        email = details.get('email')
        user_account_control = details.get('accountEnabled')
        # Skip if email is missing
        if not email or email == '[]':
            logger.warning(f"User {name} doesn't have an email set and will not be created in xiq")
            continue
        if name not in current_ppsk_user_names and user_account_control != False:
            xiq_role = details.get('xiq_role')
            if PCG_Enable == True and str(xiq_role) in PCG_Mapping:
                if name not in current_pcg_user_names:
                    pcg_batch[xiq_role].append((name, email))
                else:
                    logger.info(f"User {name} already exists in PCG, skipping PCG creation")
            else:
                new_ppsk_users.append((name, email, xiq_role))
        elif details['accountEnabled'] == False:
            ad_disabled.append(name)
        total_users = sum(len(PCGUsers) for PCGUsers in pcg_batch.values()) if pcg_batch else 0
        # If batch size reached, process the batch
        if total_users >= batch_size:
            for xiq_role, PCGUsers in pcg_batch.items():
                if not PCGUsers:
                    continue
                policy_id = PCG_Mapping[str(xiq_role)]['policy_id']
                policy_name = PCG_Mapping[str(xiq_role)]['policy_name']
                user_group_name = PCG_Mapping[str(xiq_role)]['UserGroupName']
                try:
                    logger.info(f"Adding {len(PCGUsers)} users to PCG policy {policy_name}")
                    pcg_response = x.addPCGUsers(policy_id, PCGUsers, user_group_name)
                except APICallFailedException as err: 
                    logger.error(f"API to add PCG users to policy {policy_name} failed with {err}")
                    logger.error(f"List of PCG users failed to add: {str(PCGUsers)}", extra={'file_only': True})
                    pcg_create_error += len(PCGUsers)
                    continue 
                except Exception as err:
                    logger.error(f"API to add PCG users to policy {policy_name} failed with {str(err)}")
                    logger.error(f"List of PCG users failed to add: {str(PCGUsers)}", extra={'file_only': True})
                    pcg_create_error += len(PCGUsers)
                    continue
                logger.info(f"Successfully added {len(PCGUsers)} users to PCG policy {policy_name}")
                logger.info(f"List of PCG users added: {str(PCGUsers)}", extra={'file_only': True})
            pcg_batch = defaultdict(list)  # Reset batch

    # Process any remaining users in the batch
    total_users = sum(len(PCGUsers) for PCGUsers in pcg_batch.values()) if pcg_batch else 0
    if PCG_Enable and total_users > 0:
        # Process any remaining users in the batch
        for xiq_role, PCGUsers in pcg_batch.items():
            if not PCGUsers:
                continue
            policy_id = PCG_Mapping[str(xiq_role)]['policy_id']
            policy_name = PCG_Mapping[str(xiq_role)]['policy_name']
            user_group_name = PCG_Mapping[str(xiq_role)]['UserGroupName']
            try:
                logger.info(f"Adding {len(PCGUsers)} users to PCG policy {policy_name}")
                pcg_response = x.addPCGUsers(policy_id, PCGUsers, user_group_name)
            except APICallFailedException as err: 
                logger.error(f"API to add PCG users to policy {policy_name} failed with {err}")
                logger.error(f"List of PCG users failed to add: {str(PCGUsers)}", extra={'file_only': True})
                pcg_create_error += len(PCGUsers)
                continue 
            except Exception as err:
                logger.error(f"API to add PCG users to policy {policy_name} failed with {str(err)}")
                logger.error(f"List of PCG users failed to add: {str(PCGUsers)}", extra={'file_only': True})
                pcg_create_error += len(PCGUsers)
                continue
            logger.info(f"Successfully added {len(PCGUsers)} users to PCG policy {policy_name}")
            logger.info(f"List of PCG users added: {str(PCGUsers)}", extra={'file_only': True})
        pcg_batch = defaultdict(list)
    
    # Process new PPSK users
    if new_ppsk_users:
        # Step 2: Create PPSK users
        for name, email, xiq_role in new_ppsk_users:
            try:
                user_created = x.createPPSKUser(name, email, xiq_role)
            except APICallFailedException as err:
                logger.error(f"API to create PPSK user {name} failed with {err}")
                ppsk_create_error += 1
                continue
            except Exception as err:
                logger.error(f"API to create PPSK user {name} failed with {str(err)}")
                ppsk_create_error += 1
                continue  

    # Make a list of users to delete
    if gs_capture_success:
         # Remove disabled accounts from ad users
        for name in ad_disabled:
            logger.info(f"User {name} is disabled in Google.")
            del gs_users[name]
    
        pcg_users_to_delete = defaultdict(list) if PCG_Enable else None
        ppsk_users_to_delete = []

        for ppsk_user in ppsk_users:
            user_group_id = ppsk_user['user_group_id']
            email = ppsk_user['email_address']
            ppsk_user_id = ppsk_user['id']
            username = ppsk_user['user_name']
            # check if any xiq user is not included in Google users
            if not any(d == username for d in gs_users):
                if PCG_Enable == True and str(user_group_id) in PCG_Mapping:
                    if pcg_capture_success == False:
                        log_msg = f"Due to PCG read failure, user {email} cannot be deleted"
                        logger.error(log_msg)
                        print(log_msg)
                        ppsk_del_error+=1
                        pcg_del_error+=1
                        continue
                    # If PCG is Enabled, Users need to be deleted from PCG group before they can be deleted from User Group
                    pcg_user_id = get_pcg_user_id_by_email(pcg_users, email)
                    if pcg_user_id is not None:
                        pcg_users_to_delete[user_group_id].append((ppsk_user_id, email)) 
                        # If batch size reached, process the batch
                        if sum(len(PCGUserIds) for PCGUserIds in pcg_users_to_delete.values()) >= batch_size:
                            for xiq_role, pcg_users_ids in pcg_users_to_delete.items():
                                if not pcg_users_ids:
                                    continue
                                policy_id = PCG_Mapping[str(xiq_role)]['policy_id']
                                policy_name = PCG_Mapping[str(xiq_role)]['policy_name']
                                max_pcg_user_count = 500 # Max PCG users allowed to delete in one call
                                for i in range(0, len(pcg_users_ids), max_pcg_user_count):
                                    pcg_user_batch = pcg_users_ids[i:i + max_pcg_user_count]
                                    print(f"Deleting {len(pcg_user_batch)} users from PCG policy {policy_name}")
                                    try:
                                        result = x.deletePCGUsers(policy_id, pcg_user_batch)
                                    except APICallFailedException as err:
                                        logger.error(f"API to delete {len(pcg_user_batch)} PCG users from policy {policy_name} failed with {err}")
                                        logger.error(f"List of PCG users ids failed: {str(pcg_user_batch)}", extra={'file_only': True})
                                        pcg_del_error += 1
                                        continue
                                    except Exception as err:
                                        logger.error(f"API to delete {len(pcg_user_batch)} PCG users from policy {policy_name} failed with {str(err)}")
                                        logger.error(f"List of PCG users ids failed: {str(pcg_user_batch)}", extra={'file_only': True})
                                        pcg_del_error += 1
                                        continue
                                    if result:
                                        logger.info(f"Successfully deleted {len(pcg_user_batch)} PCG users from policy {policy_name}")
                                        logger.info(f"List of PCG users ids deleted: {str(pcg_user_batch)}", extra={'file_only': True})
                            pcg_users_to_delete = defaultdict(list)  # Reset batch
                    else:
                        logger.warning(f"User {email} not found in PCG, skipping PCG deletion")
                        pcg_del_error += 1
                # Add to PPSK users to delete
                ppsk_users_to_delete.append((ppsk_user_id, email))

        # Process any remaining users in the batch
        if PCG_Enable == True and pcg_capture_success == True:
            if sum(len(PCGUserIds) for PCGUserIds in pcg_users_to_delete.values()) > 0:
                for xiq_role, pcg_users_ids in pcg_users_to_delete.items():
                    if not pcg_users_ids:
                        continue
                    policy_id = PCG_Mapping[str(xiq_role)]['policy_id']
                    policy_name = PCG_Mapping[str(xiq_role)]['policy_name']
                    print(f"Deleting {len(pcg_users_ids)} users from PCG policy {policy_name}")
                    try:
                        result = x.deletePCGUsers(policy_id, pcg_users_ids)
                    except APICallFailedException as err:
                        logger.error(f"API to delete {len(pcg_users_ids)} PCG users from policy {policy_name} failed with {err}")
                        logger.error(f"List of PCG users ids failed: {str(pcg_users_ids)}", extra={'file_only': True})
                        pcg_del_error += len(pcg_users_ids)
                        continue
                    except Exception as err:
                        logger.error(f"API to delete {len(pcg_users_ids)} PCG users from policy {policy_name} failed with {str(err)}")
                        logger.error(f"List of PCG users ids failed: {str(pcg_users_ids)}", extra={'file_only': True})
                        pcg_del_error += len(pcg_users_ids)
                        continue
                    if result:
                        logger.info(f"Successfully deleted {len(pcg_users_ids)} PCG users from policy {policy_name}")
                        logger.info(f"List of PCG users ids deleted: {str(pcg_users_ids)}", extra={'file_only': True})
                pcg_users_to_delete = defaultdict(list)  # Reset batch
        # Step 3: Delete PPSK users
        for ppsk_user_id, email in ppsk_users_to_delete:
            try:
                result = x.deletePPSKUser(ppsk_user_id)
            except APICallFailedException as err:
                logger.error(f"API to delete PPSK user ID {ppsk_user_id} failed with {err}")
                ppsk_del_error += 1
                continue
            except Exception as err:
                logger.error(f"API to delete PPSK user ID {ppsk_user_id} failed with {str(err)}")
                ppsk_del_error += 1
                continue
            if result:
                    logger.info(f"User {email} - {ppsk_user_id} was successfully deleted.")


        if ppsk_create_error:
            logger.info(f"There were {ppsk_create_error} errors creating PPSK users on this run.")
        if pcg_create_error:
            logger.info(f"There were {pcg_create_error} errors creating PCG users on this run.")
        if ppsk_del_error:
            logger.info(f"There were {ppsk_del_error} errors deleting PPSK users on this run.")
        if pcg_del_error:
            logger.info(f"There were {pcg_del_error} errors deleting PCG users on this run.")

    else:
        logger.warning("No users will be deleted from XIQ because of the error(s) in reading Google users")

if __name__ == '__main__':
	main()