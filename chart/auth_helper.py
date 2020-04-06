import yaml
from requests_oauthlib import OAuth2Session
import os
import time
import json


###from graph_helper.py
from requests_oauthlib import OAuth2Session

graph_url = 'https://graph.microsoft.com/v1.0'
####
extention_id = 'com.contosohab.parents'

# This is necessary for testing with non-HTTPS localhost
# Remove this if deploying to production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# This is necessary because Azure does not guarantee
# to return scopes in the same case and order as requested
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

# Load the oauth_settings.yml file
stream = open('oauth_settings.yml', 'r')
settings = yaml.load(stream, yaml.SafeLoader)
authorize_url = '{0}{1}'.format(settings['authority'], settings['authorize_endpoint'])
token_url = '{0}{1}'.format(settings['authority'], settings['token_endpoint'])

# Method to generate a sign-in url
def get_sign_in_url():
    # Initialize the OAuth client
    aad_auth = OAuth2Session(settings['app_id'],
        scope=settings['scopes'],
        redirect_uri=settings['redirect'])

    sign_in_url, state = aad_auth.authorization_url(authorize_url, prompt='login')

    return sign_in_url, state

# Method to exchange auth code for access token
def get_token_from_code(callback_url, expected_state):
    # Initialize the OAuth client
    aad_auth = OAuth2Session(settings['app_id'],
        state=expected_state,
        scope=settings['scopes'],
        redirect_uri=settings['redirect'])

    token = aad_auth.fetch_token(token_url,
        client_secret = settings['app_secret'],
        authorization_response=callback_url)

    return token

def store_token(request, token):
    request.session['oauth_token'] = token

def store_user(request, user):
    request.session['user'] = {
        'is_authenticated': True,
        'name': user['displayName'],
        'email': user['mail'] if (user['mail'] != None) else user['userPrincipalName']
    }

def get_token(request):
    token = request.session['oauth_token']
    if token != None:
        # Check expiration
        now = time.time()
        # Subtract 5 minutes from expiration to account for clock skew
        expire_time = token['expires_at'] - 300
        if now >= expire_time:
            # Refresh the token
            aad_auth = OAuth2Session(settings['app_id'],
                token = token,
                scope=settings['scopes'],
                redirect_uri=settings['redirect'])

            refresh_params = {
                'client_id': settings['app_id'],
                'client_secret': settings['app_secret'],
            }
            new_token = aad_auth.refresh_token(token_url, **refresh_params)

            # Save new token
            store_token(request, new_token)

            # Return new access token
            return new_token

        else:
            # Token still valid, just return it
            return token

def remove_user_and_token(request):
    if 'oauth_token' in request.session:
        del request.session['oauth_token']

    if 'user' in request.session:
        del request.session['user']


### From graph_helper.py


def get_user(token):
    graph_client = OAuth2Session(token=token)
    # Send GET to /me
    user = graph_client.get('{0}/me'.format(graph_url))
    # Return the JSON result
    return user.json()

def get_calendar_events(token):
    graph_client = OAuth2Session(token=token)

    # Configure query parameters to
    # modify the results
    query_params = {
        '$select': 'subject,organizer,start,end',
        '$orderby': 'createdDateTime DESC'
    }

    # Send GET to /me/events
    events = graph_client.get('{0}/me/events'.format(graph_url), params=query_params)
    # Return the JSON result
    return events.json()


    ## by cho

def get_hab_root(token):
    graph_client = OAuth2Session(token=token)
    hab_root = graph_client.get("{0}/groups?$filter=mailNickname eq 'hab_root'".format(graph_url))
    hab_root = hab_root.json()

    if hab_root['value']!=[]:
        return hab_root

    else:
        return False


    # Return the JSON result


def get_group_members(token,group_id):
    graph_client = OAuth2Session(token=token)

    # Send GET to /me/events
    members = graph_client.get('{0}/groups/{1}/members'.format(graph_url,group_id))
    # Return the JSON result
    return members.json()


def get_parents_hab(token,group_id):
    graph_client = OAuth2Session(token=token)
    member_of = (graph_client.get('{0}/groups/{1}/memberOf'.format(graph_url,group_id))).json()

    if member_of['value'] != []:
        rawdata = graph_client.get('{0}/groups/{1}/extensions'.format(graph_url,group_id)).json()

        if rawdata['value']!=[]:
            hab_parents = rawdata['value'][0]['parents']
            return hab_parents

        else:
            return False        

    else :
        return "GO_TO_INDEX"

def set_parents(token,group_id):
    graph_client = OAuth2Session(token=token)
    print(group_id)
    members = (get_group_members(token,group_id))['value']

    #header ='Content-type: application/json'
    headers = {'content-type':'application/json'}


    extention_dic = {
            "@odata.type":"microsoft.graph.openTypeExtension",
            "extensionName":extention_id,
            "parents":str(group_id),
            }

    #post_data = post_data + json.dumps(extention_dic)
    #print(post_data)

    gr_members = []

    for member in members:
        if member['@odata.type']=='#microsoft.graph.group':
            gr_members.append(member)

    if gr_members == []:
        print('Set_Parents Done : {0}'.format(group_id))
        return 'Set_Parents Done'

    else:
        for group in gr_members:
            print('set parents for group: {0} : {1}'.format(group['id'],group['displayName']))
            post_url = '{0}/groups/{1}/extensions'.format(graph_url,group['id'])
            res = graph_client.post(post_url,headers=headers,json=extention_dic)
            print(res.json())
            set_parents(token,group['id'])

def delete_parents(token,group_id):
    graph_client = OAuth2Session(token=token)
    print(group_id)
    members = (get_group_members(token,group_id))['value']

    gr_members = []

    for member in members:
        if member['@odata.type']=='#microsoft.graph.group':
            gr_members.append(member)

    if gr_members == []:
        print('Delete Parents Done : {0}'.format(group_id))
        return 'Delete Parents Done'

    else:
        for group in gr_members:
            print('delete parents for group: {0} : {1}'.format(group['id'],group['displayName']))
            delete_url = '{0}/groups/{1}/extensions/{2}'.format(graph_url,group['id'],extention_id)
            res = graph_client.delete(delete_url)
            print(res)
            delete_parents(token,group['id'])

def get_tree(token,group_id,parents):

    # { 'child':[] 형식으로..}
    parents['child']=[]
    members = get_group_members(token,group_id)['value']

    if len(members)==0:
        return 'No child members'

    else:
        for member in members:
            if member['@odata.type']=='#microsoft.graph.group':
                get_tree(token,member['id'],member)
                parents['child'].append(member)                

        return parents

def get_hab(token,group_id,parents):

    # { 'child':[] 형식으로..}
    parents['child']=[]
    members = get_group_members(token,group_id)['value']

    if len(members)==0:
        return 'No child members'

    else:
        for member in members:
            member['type']=member.pop('@odata.type')
            if member['type']=='#microsoft.graph.group':
                get_hab(token,member['id'],member)
                parents['child'].append(member)

            elif member['type']=='#microsoft.graph.user':
                parents['child'].append(member)

        return parents        

def get_group(token,groupid):
    graph_client = OAuth2Session(token=token)
    group = graph_client.get('{0}/groups/{1}'.format(graph_url,groupid))    

    return group.json()




def searchByPhone(token,last4,last4only):
    graph_client = OAuth2Session(token=token)
    userlist = []
    nextpage = False
    result=[]
    selectquery='?$select=displayName,businessPhones,mail,jobTitle,Department,mobilePhone'

    users = graph_client.get('{0}/users{1}'.format(graph_url,selectquery)).json()
    userlist.append(users['value'])

    if '@odata.nextLink' in users: 
        nextpageurl = users['@odata.nextLink']
        nextpage = True
        while nextpage:
            nextpageusers = graph_client.get(nextpageurl).json()
            userlist.append(nextpageusers['value'])
            if '@odata.nextLink' in nextpageusers:
                nextpageurl = nextpageusers['@odata.nextLink']
            
            else:
                nextpage = False

    if last4only:
        for users in userlist:
            for user in users:
                if (user['mobilePhone'] != None) :
                    if last4 in user['mobilePhone'][-4:]:
                        result.append(user)

                if (user['businessPhones']!= []):
                    for businessPhone in user['businessPhones']:
                        if last4 in businessPhone[-4:]:
                            result.append(user)        


    else:         
        for users in userlist:
            for user in users:
                if (user['mobilePhone'] != None) :
                    mobilePhone = user['mobilePhone'].replace(' ','').replace('-','')
                    if last4 in mobilePhone:
                        result.append(user)

                if (user['businessPhones']!= []):
                    for businessPhone in user['businessPhones']:
                        businessPhoneProcessed = businessPhone.replace(' ','').replace('-','')
                        if last4 in businessPhoneProcessed :
                            result.append(user)
                                        
    
    return result
   
