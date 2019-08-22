#! /bin/python
import os.path
import sys, getopt
import requests
import json
import zipfile

tuleap_url = ""
access_key = ""

def send_request( url, authKey ):
    """Send a request
    
        Send a request using the provided url and authentication key.
        Raise an exception if the request fails.
        When successful, return the json data replied by the server
    """
    try:
        headers = {'Accept' : 'application/json', 'X-Auth-AccessKey' :authKey }
        with requests.get(url, headers=headers) as r:
            r = requests.get(url, headers=headers) 
            r.raise_for_status()
            return json.loads(r.text)
    except: 
        raise Exception("Request failed : {} {}".format(r.status_code, json.loads(r.text)['error']['message']))

def send_request_no_check( url, authKey ):
    """Send a request that could fail
    
        Send a request using the provided url and authentication key.
        Return the request directly, possibly including an error code.
    """
    headers = {'Accept' : 'application/json', 'X-Auth-AccessKey' :authKey }
    r = requests.get(url, headers=headers)
    return r
       

def tup_get_project_list():  
    """Get the list of all the projects to which we have access
        A project is a dictionnary containing several fields such as id, uri, label, shortname, ...        
    """
    return send_request(tuleap_url + '/api/projects?limit=32&query=%7B%22is_member_of%22%3A%20true%7D', access_key ) 

def tup_get_project(project_id):  
    """Get a given project"""
    return send_request(tuleap_url + '/api/projects/' + project_id, access_key )   

def tup_list_projects(args):    
    if (len(args) > 0):
        raise Exception("tup_list_projects: takes no arguments")   
    print("\nID\tProject Name\n")
    for project in tup_get_project_list():
        print("{}\t{}".format(project['id'], project['label']))        

def tup_get_package_list(project_id):  
    r = send_request_no_check(tuleap_url + '/api/projects/' + str(project_id) + '/frs_packages', access_key )
    if (r.status_code == 200):
        return json.loads(r.text)
    else:
        return []
  
def tup_get_package(package_id):  
    return send_request(tuleap_url + '/api/frs_packages/' + str(package_id), access_key )   

def tup_get_release_list(package_id):  
    r = send_request_no_check(tuleap_url + '/api/frs_packages/' + str(package_id) + '/frs_release', access_key )
    if (r.status_code == 200):
        return json.loads(r.text)['collection']
    else:
        return []

def tup_list_package_in_project(project_name, project_id):    
    r = send_request_no_check(tuleap_url + '/api/projects/' + str(project_id) + '/frs_packages', access_key )
    package_list = json.loads(r.text)
    if (r.status_code == 200):
        for package in package_list:
            print("{} ({}) - {} ({})".format(project_name, project_id, package['label'], package['id']))
    
def tup_list_package(params):    
    """ List all packages. If a project ID or name is provided, only lists the packages of that project
    """    
    if (len(params) > 1):
        raise Exception("tup_list_package: takes zero or one argument.")   
    
    print("\nProject Name (Project ID) - Package Name (Package ID)\n")
    if (not params):
        # list packages for all projects
        project_list = send_request(tuleap_url + '/api/projects?limit=32&query=%7B%22is_member_of%22%3A%20true%7D', access_key )
        for project in project_list:
            tup_list_package_in_project( project['label'], project['id'])
    else:
        # list packages in project passed as argument
        (project_name, project_id) = tup_find_project(params[0])
        tup_list_package_in_project(project_name, project_id)
    
def tup_find_project(project_name_or_id):          
    try:
        project_id = int(project_name_or_id)
        return ( tup_get_project(project_name_or_id)['label'], project_name_or_id )
    except ValueError:
        for project in tup_get_project_list():
            if (( project['label'] == project_name_or_id) or ( project['shortname'] == project_name_or_id )):
                return (project_name_or_id, project['id'])
    raise Exception("Invalid project name or ID")


def tup_find_package(package_name_or_id):          
    try:
        package_id = int(package_name_or_id)
        return ( tup_get_package(package_id)['label'], package_name_or_id )
    except ValueError:
        for project in tup_get_project_list():
            package_list = tup_get_package_list(project['id'])
            for package in package_list:
                if ( package['label'] == package_name_or_id):
                    return( package_name_or_id, package['id'] )
    raise Exception("Invalid package name or ID")


def tup_list_releases(args):
    if (len(args) != 1):
        raise Exception("tup_list_releases: must have 1 parameter")   
    (package_name, package_id) = tup_find_package(args[0])
    r = send_request_no_check(tuleap_url + '/api/frs_packages/' + str(package_id) + '/frs_release', access_key )
    if (r.status_code == 200):
        release_collection = json.loads(r.text)
        nb_releases = release_collection['total_size']
        releases_list = release_collection['collection']
    else:
        nb_releases = 0
        releases_list = []
    
    print("\nThere are {} releases available in package {} ({})\n".format(nb_releases, package_name, package_id ))
    for release in releases_list:
        print("- {} ({})".format(release['name'], release['id'] ))
        for file in release['files']:
            print("\t{} ({})".format(file['name'], file['id']))         
        print("")

def tup_search(args):
    if (len(args) == 0):
        keyword = ""
    else:
        keyword = args[0].lower()

    project_name_printed = False
    for project in tup_get_project_list():
        if (keyword in project['label'].lower()):
            print("Project \"{}\" (id {})".format(project['label'], project['id']))
            project_name_printed = True
        for package in tup_get_package_list(project['id']):
            if (keyword in package['label'].lower()):
                if ( not project_name_printed ):
                    print("Project \"{}\" (id {})".format(project['label'], project['id']))
                    project_name_printed = True
                print("   └─── package \"{}\" (id {})".format(package['label'], package['id']))
                for release in (tup_get_release_list( package['id'])):
                    print("           └─── release \"{}\" (id {}) ".format(release['name'], release['id']))

def tup_download(args):
    if (len(args) != 2):
        raise Exception("tup_download: must have 2 parameters: release_id + path")   
    release_id = args[0]
    target = args[1]
    release = send_request(tuleap_url + '/api/frs_release/' + str(release_id), access_key )
    print("Downloading {} to {}\n".format(release['name'], target))
    print("File list:")
    for file in release['files']:
        print("\t-- " + file['name'])

    if not os.path.exists(target):
        os.makedirs(target)

    # download all files
    for file in release['files']:
        binFile = send_request_no_check(tuleap_url + file['download_url'], access_key )
        open(target + '/' + file['name'], 'wb').write(binFile.content)
        # unzip .zip files
        if ('.zip' == os.path.splitext(file['name'])[1] ):
            with zipfile.ZipFile(target + '/' + file['name'], 'r') as zip:
                zip.extractall(target)
                os.remove(target + '/' + file['name'])

def tup_upload_release(args):
    if (len(args) != 5):
        raise Exception("tup_upload_release: must have 5 parameters")   
    print(args)
    package_id = args[0]
    release_name = args[1]
    zip_file = os.path.expanduser(args[2])
    
    with open(os.path.expanduser(args[3])) as rn, open(os.path.expanduser(args[4])) as changelog, open(zip_file, "rb") as binFile:
        # Create a new release
        payload = { 'package_id' : package_id, 'name' : release_name, 'release_note' : rn.read(), 'changelog' : changelog.read() }
        url = tuleap_url + "/api/frs_release"
        headers = {'Accept' : 'application/json', 'X-Auth-AccessKey' :access_key }
        r = requests.post(url, data=payload, headers=headers)
        new_release = json.loads(r.text)
        if (r.status_code == 201):    
            print("Created release {} with ID {} in package {}".format(new_release['name'], new_release['id'], new_release['package']['label']))
        else:
            raise Exception(new_release['error']['message'])
        
        # Upload binary file
        print("Uploading {}".format(zip_file))
        file_size = os.path.getsize(zip_file)
        payload = { 'release_id' :  new_release['id'], 'name' : os.path.basename(zip_file), 'file_size' : file_size }
        url = tuleap_url + "/api/frs_files"
        headers = {'Accept' : 'application/json', 'X-Auth-AccessKey' :access_key }
        r = requests.post(url, data=payload, headers=headers)
        tus_url = tuleap_url + json.loads(r.text)["upload_href"]
        headers = {
                    'Content-Type' : 'application/offset+octet-stream', 
                    'X-Auth-AccessKey' : access_key,
                    'Content-Length' : str(file_size),
                    'Upload-Offset' : '0',
                    'Tus-Resumable' : '1.0.0'
                  }
        r = requests.patch(tus_url, data=binFile, headers=headers)

def tup_help(*args):
    if (len(args) and len(args[0]) == 1) and (args[0][0] in command_list):
        print("Description : \n\t{}\n".format(command_descriptions[args[0][0]]))
        print("Usage : \n\t./tup.py {} {}\n".format(args[0][0], command_usage[args[0][0]]))
    else:
        print("\nWelcome to tup !\n")
        print("tup is a CLI tool to manage software packages stored on a Tuleap server\n")
        print("Usage:")
        print("./tup.py [--config=path_to_config_file] command [parameters]")
        print("\nList of available commands : ")    
        for cmd in command_list:
            print("\t{}".format(cmd))
        print("\nType ./tup.py help command_name for details about a command")
    exit(1)

def parse_args(argv):
    configFile = ''
    try:
        opts,args = getopt.getopt(argv, "", ["config="])
    except getopt.GetoptError:
        tup_help()

    for opt, arg in opts:
        if opt == '--config':
            configFile=arg

    # No authentication key provided, try default path
    if ( configFile == '' ):
        configFile = "~/.tuleap_config"

    try:
            config = json.loads(open(os.path.expanduser(configFile)).read())    
            access_key = config['tuleap_key']
            tuleap_url = config['tuleap_url']
    except Exception as e:
        print("[ERROR] Cannot load tuleap URL and access key")
        print("\nYou must pass a config file as parameter or have a config file named \".tuleap_config\" in your home directory ({}/.tuleap_config)".format(os.path.expanduser("~")))
        print("\nThis file is a json config file with two fields indicating the URL of the tuleap server and an API access key to use")
        print("\nExample :\n")
        print("{")
        print("    \"tuleap_url\" : \"https://mytuleapserver.com")
        print("    \"tuleap_key\" : \"REMOVED_create_your_own_key_in_your_profile_in_the_web_interface_and_copy_it_here\"")
        print("}")
        exit(1)

    if (not args):
        tup_help()

    command = args[0];
    parameters = args[1:]   


    return ( tuleap_url, access_key, command, parameters )

command_list = { 
    'help'          : tup_help,
    'list-projects' : tup_list_projects, 
    'list-packages' : tup_list_package,
    'list-releases' : tup_list_releases,
    'get' : tup_download,
    'put' : tup_upload_release,
    'search' : tup_search,
}

command_usage = {
    'help'                  : " [command]",
    'list-projects'         : "", 
    'list-packages'         : "[project_name_or_id]",
    'list-releases'         : "[package_name_or_id]",
    'get'                   : "release_id path",
    'put'                   : "package_id release_name zip_file release_note changelog",
    'search'                : "[keyword]"
}

command_descriptions = {
    'help'              : "Print the help",
    'list-projects'     : "List all projects to which the user has access", 
    'list-packages'     : "List packages to which the user has access", 
    'list-releases'     : "List releases to which the user has access",
    'get'               : "Download a given release.",
    'put'               : "Create a new release in a given package",
    'search'            : "Search projects, packages and files for given keyword"
}

def main(argv):
    global access_key, tuleap_url   
    tuleap_url, access_key, command, parameters = parse_args(argv)

    try:
        command_list[command](parameters)
    except KeyError as e:
        print("\n[ERROR] Invalid command : {}\n".format(e))
        tup_help([command])
    except Exception as e:
        print("\n[ERROR] {}\n\nUsage: ".format(e))
        tup_help([command])
    
    
if __name__ == "__main__":
    main(sys.argv[1:])



