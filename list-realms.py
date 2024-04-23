import os
import configparser
from keycloak import KeycloakAdmin


# Init Connection
config = configparser.ConfigParser()
creds_file = os.path.expanduser("~/.ssh/mycreds-master")
config.read(creds_file)
keycloak_admin = KeycloakAdmin(
    server_url=config.get("myvars", "myurl"),
    username=config.get("myvars", "myuser"),
    password=config.get("myvars", "mypass"),
    realm_name="master")

list_realms = keycloak_admin.get_realms()
for realm in list_realms:
    print(realm['realm'])
