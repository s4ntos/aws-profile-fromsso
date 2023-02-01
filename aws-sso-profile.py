import configparser
import glob
import argparse
import sys
import os
import boto3 
import json


def main():
    config = configparser.ConfigParser()
    parser = argparse.ArgumentParser(description='Retrieves AWS credentials from SSO for use with CLI/Boto3 apps.')


    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Show verbose output, messages, etc.')
    
    parser.add_argument('-s', '--IdentityStoreId',
                        nargs=1,
                        dest='IdentityStoreId',
                        required=True,
                        help='IdentityStoreId for AWS')


    args = parser.parse_args()

    global VERBOSE_MODE
    VERBOSE_MODE = args.verbose

    config.read(os.path.expanduser('~') + '\.aws\\config')
    
    list_of_files = glob.glob(os.path.expanduser('~') + '\.aws\\sso\cache\\*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    
    with open(latest_file) as json_file:
        data = json.load(json_file)
 
    print("profiles available:", config.sections())
    accountId_profile = {}
    for profile in config.sections():
        if config[profile]['sso_account_id'] not in accountId_profile:
            accountId_profile[config[profile]['sso_account_id']] = profile
    print(accountId_profile)
    print("currenttoken Expires at :", data['expiresAt'])
    client_sso = boto3.client('sso')   
    response_accounts = client_sso.list_accounts(accessToken=data['accessToken'])
    for account in response_accounts['accountList']:
        response_roles = client_sso.list_account_roles(accessToken=data['accessToken'],accountId=account['accountId'])
        print(response_roles['roleList'])
        count=0
        for role in response_roles['roleList']:
            try:
                if account['accountId'] in accountId_profile:
                    accountSession = accountId_profile[account['accountId']]
                else:
                    accountSession = "profile " + account['accountName'] 
                if count != 0 :
                    accountSession += ( "_" + role['roleName'].lower() )
                count +=1  
            except Exception as e:
                print(account, role)
        if accountSession not in config.sections():
            config.add_section(accountSession)
            sso_start_url = 'https://' + args.IdentityStoreId[0] + '.awsapps.com/start'
            config.set(accountSession, 'sso_start_url', sso_start_url)
            config.set(accountSession, 'sso_region', 'eu-central-1')
            config.set(accountSession, 'sso_account_id' , account['accountId'] )
            config.set(accountSession, 'sso_role_name', role['roleName'])
            config.set(accountSession, 'region', 'eu-central-1')
            config.set(accountSession, 'output', 'json')
    print("profiles available:", config.sections())    
    # Writing our configuration file to 'example.cfg'
    with open('config', 'w') as configfile:
        config.write(configfile)
    
if __name__ == "__main__":
    main()
