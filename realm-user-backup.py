import os
import json
import configparser
import zipfile
from keycloak import KeycloakAdmin

# Init Connection
REALM_NAME = "master"

config = configparser.ConfigParser()
creds_file = os.path.expanduser("~/.ssh/mycreds")
config.read(creds_file)
keycloak_admin = KeycloakAdmin(
    server_url=config.get("myvars", "myurl"),
    username=config.get("myvars", "myuser"),
    password=config.get("myvars", "mypass"),
    realm_name=config.get("myvars", "myrealm"))

if not os.path.exists("data"):
    os.mkdir("data")
if not os.path.exists("data/users"):
    os.mkdir("data/users")
if not os.path.exists("data/realms"):
    os.mkdir("data/realms")
if not os.path.exists("data/groups"):
    os.mkdir("data/groups")
if not os.path.exists("data/roles"):
    os.mkdir("data/roles")

def zipData():
    filename = f"realm_{REALM_NAME}.zip"
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk('data'):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, 'data'))
    print("\n>>>Compressed into file", filename)

def cleanOldJson(directory=""):
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                pass

def getGroupsOfUser(uid=""):
    if uid:
        list_groups = keycloak_admin.get_user_groups(uid)
        return list_groups
    else:
        print("Username can not empty!")

def getRolesOfUser(uid=""):
    if uid:
        list_groups = keycloak_admin.get_realm_roles_of_user(uid)
        return list_groups
    else:
        print("Username can not empty!")

def getRolesOfGroup(gid=""):
    if gid:
        list_groups = keycloak_admin.get_group_realm_roles(gid)
        return list_groups
    else:
        print("Username can not empty!")

def getAllUsers():
    list_users = keycloak_admin.get_users({})
    cleanOldJson("data/users")
    if list_users:
        print(f"Found {len(list_users)} users!")
        for user in list_users:
            user['groups'] = getGroupsOfUser(user["id"])
            user['roles']  = getRolesOfUser(user["id"])
            user_json = json.dumps(user)
            with open(f"data/users/{user['username']}.json", "w") as file:
                file.write(user_json)
                print(f"Save user {user['username']} to json")
        return list_users
    else:
        return []

def getRealmData():
    realm = keycloak_admin.get_realm(REALM_NAME)
    cleanOldJson("data/realms")
    if realm:
        print(f"Found {REALM_NAME} data")
        realm_json = json.dumps(realm)
        with open(f"data/realms/{REALM_NAME}.json", "w") as file:
            file.write(realm_json)
            print(f"Saved to {REALM_NAME}.json")
        return realm

def getAllGroups():
    list_groups = keycloak_admin.get_groups()
    cleanOldJson("data/groups")
    if list_groups:
        print(f"Found {len(list_groups)} groups!")
        for group in list_groups:
            group['realmRoles']  = getRolesOfGroup(group["id"])
            group_json = json.dumps(group)
            with open(f"data/groups/{group['name']}.json", "w") as file:
                file.write(group_json)
                print(f"Save group {group['name']} to json")
        return list_groups
    else:
        return []

def getRealmRoles():
    list_realm_roles = keycloak_admin.get_realm_roles()
    cleanOldJson("data/roles")
    if list_realm_roles:
        print(f"Found {len(list_realm_roles)} roles!")
        for role in list_realm_roles:
            role_json = json.dumps(role)
            with open(f"data/roles/{role['name']}.json", "w") as file:
                file.write(role_json)
                print(f"Save role {role['name']} to json")
        return list_realm_roles
    else:
        return []


# Main Script
if __name__=='__main__':
    getAllUsers()
    getRealmData()
    getAllGroups()
    getRealmRoles()

    zipData()
