
async def GetLongest(*strs):
    if strs:
        longest = strs[0]
        for i in strs:
            if len(i) > len(longest):
                longest = i
        
        return longest
    else:
        return None


# Big ass recursive sorting algorithm
async def OrderClanMembers(clanMemberDetails : dict, sortKeys = ["trophies"]):
    #print("Ordering Clan Members")
    memberNames = list(clanMemberDetails.keys())
    #print(f"Starting Members: {len(memberNames)}")
    return await _orderClanMembers(clanMemberDetails, memberNames, sortKeys)

async def _orderClanMembers(clanMembersInfo : dict, orderedNames : list, sortKeys : list):
    #print("Starting Sort")
    #print(f"First Key: {sortKeys[0]}")
    #print(f"Remaining Keys: {sortKeys[1:]} \n\n")
    namesTree = await _orderClanMembersRecc(clanMembersInfo, orderedNames, sortKeys[0], sortKeys[1:])

    #print(namesTree)

    unfoldedTree = await _ReadTree(namesTree)

    #print(len(unfoldedTree))
    #print(unfoldedTree)

    return unfoldedTree

async def _orderClanMembersRecc(clanMembersInfo : dict, orderedNames : list, currentKey : str, remainingKeys: list):
    #print(f"Starting With: {orderedNames}")
    
    keyFunc = {
        "alpha" : _NameSplit,
        "role" : _RoleSplit,
        "gold" : _GoldSplit,
        "trophies" : _TrophiesSplit,
    }

    if len(remainingKeys) > 1:
        nextKey = remainingKeys[0]
        remainingKeys = remainingKeys[1:]
    elif len(remainingKeys) == 1:
        nextKey = remainingKeys[0]
        remainingKeys = []
    else:
        nextKey = None 

    # Split into ordered sublists
    #print(f"splitting based on '{currentKey}'")
    splitNames = await keyFunc[currentKey](clanMembersInfo, orderedNames)
    #print(f"result: {splitNames}")
    #print(F"next key: {nextKey}, remaining keys: {remainingKeys}\n")

    if nextKey != None: 
        for index, sublist in enumerate(splitNames):
            splitNames[index] = await _orderClanMembersRecc(clanMembersInfo, sublist, nextKey, remainingKeys)
    
    return splitNames

async def _RoleSplit(memberDetails : dict, names : list) -> list:
    rolesDict = {
        "leader" : 0,
        "coLeader" : 1,
        "admin" : 2,
        "elder" : 2,
        "member" : 3
    }
    
    sortLambda = lambda roleName: rolesDict[roleName]

    tempDict = {}

    for name in names:
        if memberDetails[name]['Role'] not in list(tempDict.keys()):
            tempDict[memberDetails[name]['Role']] = [name]
        else:
            tempDict[memberDetails[name]['Role']].append(name)

    orderedKeys = sorted(list(tempDict.keys()), key = sortLambda)

    return [tempDict[key] for key in orderedKeys]

async def _TrophiesSplit(memberDetails : dict, names : list) -> list:
    tempDict = {}

    for name in names:
        if str(memberDetails[name]['Trophies']) not in list(tempDict.keys()):
            tempDict[str(memberDetails[name]['Trophies'])] = [name]
        else:
            tempDict[str(memberDetails[name]['Trophies'])].append(name)
    
    orderedKeys = sorted(list(tempDict), key = lambda a:int(a), reverse=True)

    return [tempDict[key] for key in orderedKeys]

async def _GoldSplit(memberDetails : dict, names : list) -> list:
    tempDict = {}

    for name in names:
        if str(memberDetails[name]['RWGold']) not in list(tempDict.keys()):
            tempDict[str(memberDetails[name]['RWGold'])] = [name]
        else:
            tempDict[str(memberDetails[name]['RWGold'])].append(name)
    
    orderedKeys = sorted(list(tempDict), key = lambda a:int(a), reverse=True)

    return [tempDict[key] for key in orderedKeys]

async def _NameSplit(memberDetails : dict, names : list) -> list:
    tempDict = {}

    for name in names:
        if name not in list(tempDict.keys()):
            tempDict[name] = [name]
        else:
            tempDict[name].append[name]
    
    orderedKeys = sorted(list(tempDict))

    return [tempDict[key] for key in orderedKeys]

async def _ReadTree(tree) -> list:
    valuesRead = []
    for item in tree:
        if isinstance(item, list):
            valuesRead.extend(await _ReadTree(item))
        else:
            valuesRead.append(item)
    return valuesRead

async def IsInt(item : str):
    validNumbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    validInt = True
    for char in item:
        if char not in validNumbers:
            validInt = False
    
    return validInt

# Return league ID from player data
def GetLeagueID(playerData : dict):
    leagues = ["Unranked", "Bronze", "Silver", "Gold", "Crystal", "Master", "Champion", "Titan"]

    if "league" in list(playerData.keys()):
        playerLeagueFull = playerData["league"]["name"]
        for idx, league in enumerate(leagues):
            if league in playerLeagueFull:
                return idx

    return 0 # Unranked or some other error that should'ntv'e happened also how do you spell should''nt'v'e ; Like This --> Shouldn't've :) ; thank you smile :)

# Calculate the last clan games based on the datetime give
def CalculateLastClanGames(date : str):
    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])

    if day >= 28: # This Month
        return f"{year}-{month}-28 00:00:00"
    else: # Last Month
        if month > 1: # This Year
            return f"{year}-{month-1}-28 00:00:00"
        else: # Last Year
            return f"{year-1}-12-28 00:00:00"

def CalculateClanGamesBetween(updatedFor : str, lastClanGames : str) -> int:
    yearDiff = int(updatedFor[0:4]) - int(lastClanGames[0:4])
    monthDiff = int(updatedFor[5:7]) - int(lastClanGames[5:7])

    totalDiff = 12*yearDiff + monthDiff

    return -totalDiff