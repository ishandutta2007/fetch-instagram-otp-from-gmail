import httplib2
import os
from oauth2client import client, tools, file
import base64
from googleapiclient import errors, discovery
import constants
from bs4 import BeautifulSoup
import base64

def get_oath_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, constants.CREDENTIAL_FILE_NAME)
    store = file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(constants.CLIENT_SECRET_FILE, constants.SCOPES)
        flow.user_agent = constants.APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print(('Storing credentials to ' + credential_path))
    return credentials

def list_messages_matching_query(service, user_id, query=''):
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query,
                                                    pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def get_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        # print('Message snippet: %s' % message['snippet'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def is_useful(headers):
    count = 0
    for header in headers:
        if header['name']=='Subject' and header['value'].strip()=='Verify Your Account':
            count += 1
        if header['name']=='From' and header['value'].strip()=='Instagram <security@mail.instagram.com>':
            count += 1
    if count == 2:
        return True
    else:
        return False

def get_code(msg):
    bodydata = msg['payload']['body']['data']
    decoded_bodydata = base64.urlsafe_b64decode(bodydata)
    soup = BeautifulSoup(decoded_bodydata, features="html.parser")
    f = soup.find('font')
    return f.contents[0]

def main():
    credentials = get_oath_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    messages = list_messages_matching_query(service, "me", query=constants.QUERY_TERM)
    for message in messages:
        msg = get_message(service, "me", message['id'])
        headers = msg['payload']['headers']
        if is_useful(headers):
            print(get_code(msg))
            # break

if __name__ == '__main__':
    main()
