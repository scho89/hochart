from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from chart.auth_helper import get_sign_in_url, get_token_from_code, store_token, store_user, remove_user_and_token, get_token,get_user,get_hab_root,get_group_members,set_parents,get_parents_hab,delete_parents,get_tree,get_group,get_hab
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt

###for search function
from chart.auth_helper import searchByPhone

# Create your views here.

@xframe_options_exempt
def index(request):
    token,context = verify_signin(request)

    if token:
        hab_root = get_hab_root(token)

        if hab_root: 

            if 'hab' in request.session:
                print('session hab true')
                context['hab']=request.session['hab']

                pass                

            else:
                hab_dic = get_hab(token,hab_root['value'][0]['id'],hab_root)
                context['hab']=hab_dic
                request.session['hab']=hab_dic


            return render(request,'chart/index.html',context)

        else:
            return HttpResponseRedirect(reverse('chart:sethab'))

    else:
        return signin(request)


def detail(request,groupid):
    print('start detail view')
    context = initialize_context(request)

    if(context['user']['is_authenticated']):
        token = get_token(request)
        rawdata = get_group_members(token,groupid)

    groups=[]
    users=[]

    for item in rawdata['value']:
        if item['displayName'] != None:
            if item['@odata.type'] == '#microsoft.graph.group':
                groups.append(item)
            elif item['@odata.type'] == '#microsoft.graph.user':
                users.append(item)

    context['groups']=groups
    context['users']=users

    habparents = get_parents_hab(token,groupid)
    context['parents_id']=habparents

    if habparents:
        if habparents == "GO_TO_INDEX":
            return render(request,'chart/index.html',context)

        else:
            return render(request,'chart/detail.html',context) 

    else:
        context['hab_error']={'msg':'HAB configuration is not completed.','url':'chart:sethab'}
        return render(request,'chart/error.html',context)  


def sethab(request):
    context = initialize_context(request)
    if(context['user']['is_authenticated']):
        token = get_token(request)
        hab_root = get_hab_root(token)
    
    
    if hab_root:
        delete_parents(token,hab_root['value'][0]['id'])
        set_parents(token,hab_root['value'][0]['id'])
        return HttpResponse("HAB setting is completed. Go back to page /chart")

    else:
        print('HAB_ROOT is not found.')
        return HttpResponse('Hierarchical Addressbook Root is not found.<br>Alias of HAB root need to set "hab_root"')
    
    

def deletehab(request):
    context = initialize_context(request)
    
    if(context['user']['is_authenticated']):
        token = get_token(request)
        hab_root = get_hab_root(token)
        delete_parents(token,hab_root['value'][0]['id'])


    return HttpResponse('HAB setting is removed.')


def tree(request,groupid):
    context = initialize_context(request)

    if(context['user']['is_authenticated']):
        token = get_token(request)

    parents = get_group(token,groupid)
    tree_dic = get_tree(token,groupid,parents)

    context['tree']=tree_dic
    print(tree_dic)


    return render(request,'chart/tree.html',context=context)

def treeroot(request):
    token,context = verify_signin(request)

    if token:
        hab_root = get_hab_root(token)
        
        if hab_root:

            if 'tree' in request.session:
                print('session tree true')
                context['tree']=request.session['tree']
                pass                

            else:
                tree_dic = get_tree(token,hab_root['value'][0]['id'],hab_root)
                context['tree']=tree_dic
                request.session['tree']=tree_dic

            return render(request,'chart/treeroot.html',context=context)

        else:
            return HttpResponse('Hierarchical Addressbook Root is not found.<br>Alias of HAB root need to set "hab_root"')

    else:
        return signin(request)
    

def hab(request):
    token,context = verify_signin(request)

    if token:
        hab_root = get_hab_root(token)
        
        if hab_root:

            if 'hab' in request.session:
                print('session hab true')
                context['hab']=request.session['hab']

                pass                

            else:
                hab_dic = get_hab(token,hab_root['value'][0]['id'],hab_root)
                context['hab']=hab_dic
                request.session['hab']=hab_dic

            print(request.session['hab'])            
            return render(request,'chart/habroot.html',context=context)

        else:
            return HttpResponse('Hierarchical Addressbook Root is not found.<br>Alias of HAB root need to set "hab_root"')

    else:
        return signin(request)


def who(request):
    token,context = verify_signin(request)

    if token:

        return render(request,'chart/who.html',context)

    else:
        return signin(request)

def searchLast4(request):
    token,context = verify_signin(request)

    if token:

        last4 = request.POST['phoneLast4']
        if 'checkOnlyLast4' in request.POST:
            last4only = bool(request.POST['checkOnlyLast4'])
        else:
            last4only = False

        search_result = searchByPhone(token,last4,last4only)
        print(search_result)
        context['users']=search_result

        return render(request,'chart/whoResult.html',context)

    else:
        return signin(request)


##################

def verify_signin(request):
    context = initialize_context(request)

    if(context['user']['is_authenticated']):
        token = get_token(request)
        return token,context

    else:
        return False,False


############

def initialize_context(request):
    context = {}

    # Check for any errors in the session
    error = request.session.pop('flash_error', None)

    if error != None:
        context['errors'] = []
        context['errors'].append(error)

    # Check for user in the session
    context['user'] = request.session.get('user', {'is_authenticated': False})
    return context


def signin(request):

    # Get the sign-in URL
    sign_in_url, state = get_sign_in_url()
    # Save the expected state so we can validate in the callback
    request.session['auth_state'] = state
    # Redirect to the Azure sign-in page
    return HttpResponseRedirect(sign_in_url)

    #return HttpResponse("Sign in page")
    #return render(request,'chart/index.html')

def callback(request):

    # Get the state saved in session
    expected_state = request.session.pop('auth_state', '')
    # Make the token request
    token = get_token_from_code(request.get_full_path(), expected_state)

    # Get the user's profile
    user = get_user(token)

    # Save token and user
    store_token(request, token)
    store_user(request, user)

    return HttpResponseRedirect(reverse('chart:index'))
#    return HttpResponse("Callback page")

