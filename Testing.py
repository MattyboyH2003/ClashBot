from ClashInterface import GetClanInfo
import json

with open("tokens.json", "r") as tokenfile:
    token = json.loads(tokenfile.read())["CoC"]["token"]

print(GetClanInfo(token, "2PCJP0L0P"))
