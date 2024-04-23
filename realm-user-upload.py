import os
import sys
import json
import zipfile
import configparser
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError, KeycloakPostError

OLD_REALM_NAME = ""
NEW_REALM_NAME = sys.argv[1]
FILENAME = sys.argv[2]

# Init Connection
config = configparser.ConfigParser()
creds_file = os.path.expanduser("~/.ssh/mycreds")
config.read(creds_file)
keycloak_admin = KeycloakAdmin(
    server_url=config.get("myvars", "myurl"),
    username=config.get("myvars", "myuser"),
    password=config.get("myvars", "mypass"),
    realm_name=NEW_REALM_NAME)


# -----------------------------------------------------------------------------------
def extractData():
    global OLD_REALM_NAME
    if not os.path.exists("data"):
        os.mkdir("data")
    
       
    for file in os.listdir():
        if file.startswith(FILENAME) and file.endswith(".zip"):
            OLD_REALM_NAME = file[6:-4]
            print(f"Found data file {file} of realm {OLD_REALM_NAME}")
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall('data')
            print(">>>> Extracted to data folder!")
            return
    raise Exception("Zip file not found!")

# -----------------------------------------------------------------------------------
def updateRealm():
    realm_data = {}
    with open(f"data/realms/{OLD_REALM_NAME}.json", 'r') as file:
        realm_data = json.load(file)
        realm_data['users'] = keycloak_admin.get_users({})
        realm_data['realm'] = NEW_REALM_NAME
        realm_data.pop('id')
        
        try:
            keycloak_admin.update_realm(realm_name=NEW_REALM_NAME, payload=realm_data)
        except Exception as e:
            print("Error when update realm data!\n", str(e))

# -----------------------------------------------------------------------------------
def getListUsername() -> list:
    if not os.path.exists("data") or not os.path.exists("data/users"):
        raise Exception("User data folder not found!")
    list_files = os.listdir("data/users")
    if list_files:
        return [file.split(".jso")[0] for file in list_files if file.endswith("json")]
    else:
        return []

def readUserData(username="admin") -> dict:
    if username:
        user_data = {}
        with open(f"data/users/{username}.json", 'r') as file:
            user_data = json.load(file)
            try:
                user_data.pop('id')
            except:
                pass
        return user_data
    raise Exception("Username cannot be empty!")

def createUser(user_dict={}) -> str:
    try:
        list_groups = []
        if "groups" in user_dict.keys():
            list_groups = [group['name'] for group in user_dict['groups']]
            user_dict.pop("groups")
        list_roles = []
        if "roles" in user_dict.keys():
            list_roles = [role['name'] for role in user_dict['roles']]
            user_dict.pop("roles")
            if f"default-roles-{OLD_REALM_NAME}" in list_roles:
                list_roles[list_roles.index(f"default-roles-{OLD_REALM_NAME}")] = f"default-roles-{NEW_REALM_NAME}"

        user = keycloak_admin.create_user(user_dict, exist_ok=True)
        print("Created user", user_dict["username"])
        
        if list_groups:
            print(f"This user belongs to {len(list_groups)} groups")
            group_query = keycloak_admin.get_groups({})
            for group in group_query:
                if group['name'] in list_groups:
                    print(f"-> Adding user to group {group['name']}")
                    keycloak_admin.group_user_add(user, group["id"])
        if list_roles:
            print(f"This user belongs to {len(list_roles)} roles")
            role_query = keycloak_admin.get_realm_roles({})
            for role in role_query:
                if role['name'] in list_roles:
                    print(f"-> Adding user to role {role['name']}")
                    keycloak_admin.assign_realm_roles(user, role)

    except KeycloakGetError:
        print("User already exists!")
    except Exception as e:
        print("error when create user {}!\n".format(user_dict["username"]), str(e))

def getAllUsers():
    list_users = keycloak_admin.get_users({})
    if list_users:
        print(f"Found {len(list_users)} users!")
        for user in list_users:
            print(f"- Id: {user['id']} ~ Username: {user['username']}")

# -----------------------------------------------------------------------------------
def getListGroups() -> list:
    if not os.path.exists("data") or not os.path.exists("data/groups"):
        raise Exception("Group data folder not found!")
    list_files = os.listdir("data/groups")
    if list_files:
        return [file.split(".")[0] for file in list_files if file.endswith("json")]
    else:
        return []

def readGroupData(group_name="") -> dict:
    if group_name:
        group_data = {}
        with open(f"data/groups/{group_name}.json", 'r') as file:
            group_data = json.load(file)
            try:
                group_data.pop('id')
            except:
                pass
        return group_data
    raise Exception("Group name cannot be empty!")

def createGroup(group_dict={}) -> str:
    list_roles = []
    if "realmRoles" in group_dict.keys():
        list_roles = [role['name'] for role in group_dict['realmRoles']]
        group_dict.pop("realmRoles")
        if f"default-roles-{OLD_REALM_NAME}" in list_roles:
            list_roles[list_roles.index(f"default-roles-{OLD_REALM_NAME}")] = f"default-roles-{NEW_REALM_NAME}"

    try:
        group = keycloak_admin.create_group(group_dict)
        print("Created group", group_dict["name"])

        if list_roles:
            print(f"This group belongs to {len(list_roles)} roles")
            role_query = keycloak_admin.get_realm_roles({})
            for role in role_query:
                if role['name'] in list_roles:
                    print(f"-> Adding group to role {role['name']}")
                    keycloak_admin.assign_group_realm_roles(group, role)
    except KeycloakPostError:
        print(f"Group {group_dict['name']} already exists. Please delete this group and run again!")
    except Exception as e:
        print("error when assign roles to group {}!\n".format(group_dict["name"]), str(e))


def getAllGroups():
    list_groups = keycloak_admin.get_groups({})
    if list_groups:
        print(f"Found {len(list_groups)} groups!")
        for group in list_groups:
            print(f"- Id: {group['id']} ~ Group name: {group['name']}")

# -----------------------------------------------------------------------------------
def getListRoles() -> list:
    if not os.path.exists("data") or not os.path.exists("data/roles"):
        raise Exception("Roles data folder not found!")
    list_files = os.listdir("data/roles")
    if list_files:
        return [file.split(".")[0] for file in list_files if file.endswith("json")]
    else:
        return []

def readRoleData(role_name="") -> dict:
    if role_name:
        role_data = {}
        with open(f"data/roles/{role_name}.json", 'r') as file:
            role_data = json.load(file)
            try:
                role_data.pop('id')
            except:
                pass
        return role_data
    raise Exception("Role name cannot be empty!")

def createRole(role_dict={}) -> str:
    try:
        role = keycloak_admin.create_realm_role(role_dict)
        print("Created role", role_dict["name"])
    except KeycloakPostError:
        print(f"Role {role_dict['name']} already exists. Please delete this role and run again!")
    except Exception as e:
        print("error when create role {}!\n".format(role_dict["name"]), str(e))

def getAllRoles():
    list_roles = keycloak_admin.get_realm_roles()
    if list_roles:
        print(f"Found {len(list_roles)} roles!")
        for role in list_roles:
            print(f"- Id: {role['id']} ~ Role name: {role['name']}")


if __name__=='__main__':
    extractData()

    print("\nUploading Roles...")
    roles = getListRoles()
    for role in roles:
        if role == f"default-roles-{OLD_REALM_NAME}":
            continue
        print("\n- Creating role", role)
        role_dict = readRoleData(role)
        createRole(role_dict)
    print("\nAll roles in realm:")
    getAllRoles()
    print("="*40)

    print("Uploading Groups...")
    groups = getListGroups()
    for group in groups:
        print("\n- Creating group", group)
        group_dict = readGroupData(group)
        createGroup(group_dict)
    print("\nAll groups in realm:")
    getAllGroups()
    print("="*40)

    print("Uploading Users...")
    usernames = getListUsername()
    for username in usernames:
        print("\n- Creating user", username)
        user_dict = readUserData(username=username)
        createUser(user_dict)
        print('-'*30)
    print("\nAll user in realm:")
    getAllUsers()
    print("="*40)

    print("Updating Realm data...")
    updateRealm()
    print("="*40)

    print("Finished!")
