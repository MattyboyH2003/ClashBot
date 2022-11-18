import json
import urllib3

baseURL = "https://api.clashofclans.com/v1/"

http = urllib3.PoolManager()


def _SendRequest(endpoint = "", fields = {}, headers = {}, resultType = "JSON"):

    print(f"Sending request to {endpoint}")
    response = http.request("GET", f"{baseURL}{endpoint}", fields = fields, headers = headers)


    if response.status == 200:
        response = response.data.decode('utf-8')
        if resultType == "JSON":
            response = json.loads(response)

        return response
    else:
        print(response.status)
        print(response.data)

        exit()

def GetMembers(token, clan):
    endpoint = f"clans/%23{clan}/members"
    fields = {"limit" : 50}
    headers = {"Authorization" : f"Bearer {token}"}

    response = _SendRequest(endpoint, fields, headers)["items"]

    with open("ClashInterface/SavedData/members.json", "w") as f:
        f.write(json.dumps(response))

    return response

def GetPreviousRaidWeekend(token, clan):
    endpoint = f"clans/%23{clan}/capitalraidseasons"
    fields = {"limit" : 1}
    headers = {"Authorization" : f"Bearer {token}"}

    response = _SendRequest(endpoint, fields, headers)["items"][0]

    with open("ClashInterface/SavedData/capraid.json", "w") as f:
        f.write(json.dumps(response))

    return response

def GetPreviousClanWar(token, clan):
    endpoint = f"clans/%23{clan}/warlog"
    fields = {"limit" : 1}
    headers = {"Authorization" : f"Bearer {token}"}

    response = _SendRequest(endpoint, fields, headers)["items"]

    with open("ClashInterface/SavedData/clanWar.json", "w") as f:
        f.write(json.dumps(response))

    return response

def GetClanInfo(token, clan):
    endpoint = f"clans/%23{clan}"
    fields = {}
    headers = {"Authorization" : f"Bearer {token}"}

    response = _SendRequest(endpoint, fields, headers)


    return response

if __name__ == "__main__":
    with open("tokens.json", "r") as tokenFile:
        token = json.loads(tokenFile.read())["CoC"]["token"]
