# tup : Tuleap Package Manager

## Introduction
tup is a CLI tool to manage software packages stored on a Tuleap server. It uses the tuleap REST API to provide several functionalities.

## Dependencies
To run tup, you need python 3 with the python Requests package installed.

## Usage
### Configuration
To perform any operation, tup needs 2 informations : 
- the url of the Tuleap server
- a valid API key to use

These information should be put in a json file with the following format :


        {
            "tuleap_url" : "https://my_tuleap_server.com",
            "tuleap_key" : "__REMOVED__"
        }

The file can then be saved as ".tuleap_config" in your home directory, or passed as argument to tup using the --config= command line option.


### Command list
tup is always invoked with a command and other optional arguments :

    tup.py [--config=path_to_config_file] command [parameters]

The available commands are :
1. **help** : Display the help

        Usage :
        tup.py help  [command]

2. **list-projects** : List all projects to which the user has access

        Usage : 
        tup.py list-projects

3. **list-packages** : list all packages or all package in a given project to which the user has access

        Usage :
        tup.py list-packages [project_name_or_id]

4. **list-releases** : list all releases to which the user has access in a given package

        Usage :
        tup.py list-releases package_name_or_id

5. **search** : search projects, packages and files for given keyword

        Usage :
        tup.py search [keyword]

6. **get** : download a given release

        Usage:
        tup.py get release_id path

7. **get-latest** : download the latest release in a given package

        Usage:
        tup.py get package_name_or_id path

8. **put** : create a new release in a given package. The release name, a zip file containing the release, the release note and a changelog must be provided.

        Usage :
        tup.py put package_id release_name zip_file release_note changelog

### Troubleshoot
If you get an error :

    [ERROR] HTTPSConnectionPool ...  certificate verify failed: self signed certificate in certificate chain 

You probably have to install a custom certificate. To do so, you can add it at the end of your cacert.pem file, which is typically located in your python install directory, e.g, */usr/lib/python3.7/site-packages/certifi/cacert.pem*

    cat my_CA.pem >> /usr/lib/python3.7/site-packages/certifi/cacert.pem