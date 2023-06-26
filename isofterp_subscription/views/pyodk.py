
from pyodk import Client


with Client() as client:
    print(client.projects.list())

