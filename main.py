import copy
import json
import asyncio

import discord
from discord.ext import commands

import DatabaseTools
import GeneralUtils
import ClashInterface

bot = commands.Bot(command_prefix="c!", intents=discord.Intents(65535))
bot.remove_command("help")

with open("tokens.json", "r") as tokenfile:
    tokens = json.loads(tokenfile.read())

with open("BotAdmins.json", "r") as adminFile:
    admins = json.loads(adminFile.read())


##############################
# - Command Base Functions - #
##############################

async def _getMembers(msg : discord.Message):
    emojisDict = {
        "wo0"       : "<:wo0:1043539783357579264>",
        "wo1"       : "<:wo1:1043539784926248960>",
        "cw0"       : "<:cw0:1043476284770099240>",
        "cw1"       : "<:cw1:1043476286112272414>",
        "cg0"       : "<:cg0:1043476282136084520>",
        "cg1"       : "<:cg1:1043476283381780610>",
        "cc0"       : "<:cc0:1043476279061643274>",
        "cc1"       : "<:cc1:1043476280630325289>",
        "coctrophy" : "<:coctrophy:1043481716490244128>",
        "townhall"  : "<:townhall:1043483318215254078>",
        "activity"  : "<:activity:1043484073462607984>",
        "tl0"       : "<:tl0:1043539822976966706>",
        "tl1"       : "<:tl1:1043539824205910118>",
        "tl2"       : "<:tl2:1043539825736810638>",
        "tl3"       : "<:tl3:1043539827041255484>",
        "tl4"       : "<:tl4:1043539828173705238>",
        "tl5"       : "<:tl5:1043539829838839909>",
        "tl6"       : "<:tl6:1043539831495598130>",
        "tl7"       : "<:tl7:1043539832753889290>",
        "tl8"       : "<:tl8:1043539834003800064>"
    }
    
    clan = DatabaseTools.GetPrimaryClan(msg.guild.id)
    members = ClashInterface.GetMembers(tokens["CoC"]["token"], clan)

    fullMemberDetails = {}

    for member in members:
        memberInfo = {}
        memberInfo["BasicInfo"] = member
        memberInfo["ProfileInfo"] = ClashInterface.GetPlayerInfo(tokens["CoC"]["token"], member["tag"].replace("#", ""))

        fullMemberDetails[member["name"]] = memberInfo
    
    # Calculates how man embeds are needed
    totalMessages = len(list(fullMemberDetails.keys()))//10 + bool(len(list(fullMemberDetails.keys()))%10)

    # Creates a list of however many embeds needed
    messages = ["" for _ in range(totalMessages)]

    for index, memberName in enumerate(list(fullMemberDetails.keys())):
        messageSegment = "> "
        messageSegment += emojisDict["wo1"] if fullMemberDetails[memberName]["ProfileInfo"]["warPreference"] == "in" else emojisDict["wo0"]
        messageSegment += " `|` "
        messageSegment += emojisDict["cw1"]
        messageSegment += emojisDict["cg1"]
        messageSegment += emojisDict["cc1"]
        messageSegment += " `|` "
        messageSegment += emojisDict["tl" + str(GeneralUtils.GetLeagueID(fullMemberDetails[memberName]["ProfileInfo"]))]
        messageSegment += " " + memberName

        messages[index//10] += messageSegment + "\n"

    for message in messages:
        await msg.channel.send(message)

async def _getClanInfo(msg):
    clan = DatabaseTools.GetPrimaryClan(msg.guild.id)
    clanInfo = ClashInterface.GetClanInfo(tokens["CoC"]["token"], clan)
    embed = discord.Embed(title=clanInfo["name"], description=clanInfo["description"], colour=0xC22F43) # creating an embed for the help message
    embed.set_thumbnail(url=clanInfo["badgeUrls"]["small"]) # using the bot profile picture as an image on the embed
    #embed.set_footer(text="CoC Manager | v0.1.0") # creating a footer for the embed
    embed.add_field(name="**Clan Info:**", value=f"""
        **Members:** {clanInfo['members']}
        **Capital Peak Level:** {clanInfo['clanCapital']['capitalHallLevel']}
    """, inline=False)
    await msg.channel.send(embed=embed)

async def _getCapRaid(msg):
    clan = DatabaseTools.GetPrimaryClan(msg.guild.id)
    clanInfo = ClashInterface.GetClanInfo(tokens["CoC"]["token"], clan)
    capRaidInfo = ClashInterface.GetPreviousRaidWeekend(tokens["CoC"]["token"], clan)
    msgEmbed = discord.Embed(title=clanInfo["name"], description=f"Raid Weekend: {capRaidInfo['startTime'][6:8]}/{capRaidInfo['startTime'][4:6]}/{capRaidInfo['startTime'][0:4]}", colour=0xC22F43) # creating an embed for the help message
    msgEmbed.set_thumbnail(url=clanInfo["badgeUrls"]["small"]) # using the bot profile picture as an image on the embed
    msgEmbed.set_footer(text="Raid Weekend Info") # creating a footer for the embed
    membersText = "".join([f"**{member['name']}** - {member['capitalResourcesLooted']} - {member['attacks']}/{member['attackLimit']+member['bonusAttackLimit']}\n" for member in sorted(capRaidInfo["members"], key=lambda a:a['capitalResourcesLooted'], reverse=True)])
    
    msgEmbed.add_field(name="__Participants__", value=membersText, inline=False)

    await msg.channel.send(embed=msgEmbed)

async def _updateMembers(server, channel, *args, **kwargs):
    channelID, messageID = DatabaseTools.GetMemberMessages(server.id)[0]
    membersPerPage = 12

    # Deal with the args
    args = list(args)
    argsTypeCount = {
        "str" : 0,
        "int" : 0
    }

    VALIDSORTCODES = ["role", "alpha", "trophies", "gold"]

    for index, arg in enumerate(args):
        if await GeneralUtils.IsInt(arg):
            args[index] = int(arg)
            argsTypeCount["int"] += 1
        else:
            argsTypeCount["str"] += 1

    if argsTypeCount["int"] == 1:
        for arg in args:
            if isinstance(arg, int):
                membersPerPage = arg
    
    if argsTypeCount["str"] > 0:
        sortOrder = []
        for arg in args:
            if isinstance(arg, str):
                cleanArg = arg.lower()
                cleanArg.replace("alphabetical", "alpha")
                if cleanArg in VALIDSORTCODES:
                    sortOrder.append(cleanArg)
                else:
                    await channel(f"`{arg}` is not a valid sort code")
                    return
    else:
        sortOrder = ["role", "alpha"]

    # Gets info on the clan
    clan = DatabaseTools.GetPrimaryClan(server.id)
    clanInfo = ClashInterface.GetClanInfo(tokens["CoC"]["token"], clan) 

    # Gets the clan members info and orders the members by role
    clanMembers = ClashInterface.GetMembers(tokens["CoC"]["token"], clan)

    # Gets the previous raid weekend participants and their details
    raidWeekendMembers = ClashInterface.GetPreviousRaidWeekend(tokens["CoC"]["token"], clan)['members']
    rwParticipants = [_rwMember['name'] for _rwMember in raidWeekendMembers]

    # Creates a detailed clan members dict
    fullClanMembers = {}

    for member in clanMembers:
        memberName = member['name']
        if memberName in rwParticipants:
            rwMemberInfo = raidWeekendMembers[rwParticipants.index(memberName)]
            memberGold = rwMemberInfo['capitalResourcesLooted']
            memberAttacks = f"{rwMemberInfo['attacks']}/{rwMemberInfo['attackLimit']+rwMemberInfo['bonusAttackLimit']}"
        else:
            memberGold = 0
            memberAttacks = "0/0"
            
        
        memberDetails = {
            "Trophies" : member['trophies'],
            "BuilderTrophies" : member['versusTrophies'],
            "Role" : member['role'],
            "Level" : member['expLevel'],
            "TroopsDonated" : member['donations'],
            "TroopsRecived" : member['donationsReceived'],
            "ClanRank" : member['clanRank'],
            "RWGold" : memberGold,
            "RWAttacks" : memberAttacks
        }

        fullClanMembers[memberName] = memberDetails
    member = None

    clanMemberOrderedNames = await GeneralUtils.OrderClanMembers(fullClanMembers, sortOrder)

    # Creates a blank embed template
    blankEmbed = discord.Embed(title=clanInfo["name"], description="__**Members**__", colour=0xC22F43)
    blankEmbed.set_thumbnail(url=clanInfo["badgeUrls"]["small"]) # using the bot profile picture as an image on the embed
    
    # Calculates how man embeds are needed
    totalEmbedPages = len(clanMembers)//membersPerPage + bool(len(clanMembers)%membersPerPage)

    # Creates a list of however many embeds needed
    embeds = [copy.deepcopy(blankEmbed) for _ in range(totalEmbedPages)]

    # Adds the page counter in the embed footer
    for index, embed in enumerate(embeds):
        embed.set_footer(text = f"Page {index+1}/{totalEmbedPages}")


    # Adds the members to the embeds
    for index, clanMemberName in enumerate(clanMemberOrderedNames):
        clanMemberInfo = fullClanMembers[clanMemberName]

        raidWeekendText = f"{clanMemberInfo['RWGold']} - {clanMemberInfo['RWAttacks']}"
        
        newEmbedValue = f"""
            Role: {clanMemberInfo['Role'].replace('admin', 'elder').capitalize()}
            Trophies: {clanMemberInfo['Trophies']}
            Raid Weekend: 
            {raidWeekendText}
        """
        embeds[index//membersPerPage].add_field(name = f"__{clanMemberName}__", value = newEmbedValue)

    membersMessageChannel = await bot.fetch_channel(channelID)
    membersMessage = await membersMessageChannel.fetch_message(messageID)

    currentEmbed = 0

    components = discord.ui.View()
    components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled=True, emoji = "⏪", custom_id = "FullLeft"))
    components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled=True, emoji = "◀️", custom_id = "Left"))
    components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled=False, emoji = "▶️", custom_id = "Right"))
    components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled=False, emoji = "⏩", custom_id = "FullRight"))

    await membersMessage.edit(content="", embed = embeds[currentEmbed], view = components)

    if "interaction" in list(kwargs.keys()):
        await kwargs["interaction"].response.send_message(content = "Members message updated!")
    else:
        await channel.send("Members updated")



    waitingForResponse = True
    while waitingForResponse:
        try:
            interaction = await bot.wait_for("interaction", timeout=60.0)

            if interaction.message.id == membersMessage.id:
                if interaction.data['custom_id'] == "Right":
                    currentEmbed += 1
                elif interaction.data['custom_id'] == "Left":
                    currentEmbed -= 1
                elif interaction.data['custom_id'] == "FullRight":
                    currentEmbed = totalEmbedPages - 1
                elif interaction.data['custom_id'] == "FullLeft":
                    currentEmbed = 0
            
            components = discord.ui.View()
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = currentEmbed == 0, emoji = "⏪", custom_id = "FullLeft"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = currentEmbed == 0, emoji = "◀️", custom_id = "Left"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = currentEmbed == totalEmbedPages-1, emoji = "▶️", custom_id = "Right"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = currentEmbed == totalEmbedPages-1, emoji = "⏩", custom_id = "FullRight"))

            #await membersMessage.edit(content="", embed = embeds[currentEmbed], view = components)
            await interaction.response.edit_message(content="", embed = embeds[currentEmbed], view = components)



        except asyncio.TimeoutError:
            components = discord.ui.View()
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = True , emoji = "⏪", custom_id = "FullLeft"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = True , emoji = "◀️", custom_id = "Left"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = True , emoji = "▶️", custom_id = "Right"))
            components.add_item(discord.ui.Button(style = discord.ButtonStyle.blurple, disabled = True , emoji = "⏩", custom_id = "FullRight"))

            await membersMessage.edit(content = "", embed = embeds[currentEmbed], view = components)
            waitingForResponse = False

async def _linkClan(msg : discord.Message, clanID):
    if msg.author.guild_permissions.administrator:
        linked = DatabaseTools.LinkClan(msg.guild.id, clanID)

        if linked:
            await msg.send(f"Servers primary clan set to {clanID}")
        else:
            await msg.send(f"Setting primary clan failed, please check the clan tag is valid")
    else:
        await msg.send("Only administrators can run this command")


########################
# - General Commands - #
########################

@bot.command()
async def help(message): #Help command which lists all bot commands
    botInfo = await bot.fetch_user(bot.user.id)
    embed = discord.Embed(title="Help Menu", description="These are all the commands available", colour=0xC22F43) # creating an embed for the help message
    embed.set_thumbnail(url=botInfo.display_avatar.url) # using the bot profile picture as an image on the embed
    embed.set_footer(text="CoC Manager | v0.1.0") # creating a footer for the embed
    embed.add_field(name="Commands:", value="""
    `c!getMembers` - Use this command to list all members in the clan
    `c!updateMembers` - Use this command to update the members message
    `c!getCapitalRaidInfo` - Use this command to get info about the previous raid weekend
    `c!getClanInfo` - Use this command to get info about the clan
    """, inline=False)
    await message.channel.send(embed=embed) # sending the help embed to the channel to command was sent in

@bot.command()
async def get(msg, item : str, *args):
    item = item.lower()
    args = [str(i).lower() for i in args]

    func = None
    failMsg = f"No command found for `c!get {item} {''.join([str(i) for i in args]).removesuffix(' ')}`"
    nextArgs = [msg]

    if item == "members" or item == "clanmembers":
        func = _getMembers
    elif item == "claninfo":
        func = _getClanInfo
    elif item == "clan":
        if args:
            if args[0] == "info":
                func = _getClanInfo
            elif args[0] == "members":
                func = _getMembers
        else:
            func = _getClanInfo

    if func:
        await func(*nextArgs)
    else:
        await msg.channel.send(failMsg)

@bot.command()
async def update(msg, item : str, *args):
    item = item.lower()
    args = [str(i).lower() for i in args]

    func = None
    failMsg = f"No command found for `c!get {item} {''.join([str(i) for i in args]).removesuffix(' ')}`"
    nextArgs = [msg]

    if item == "members":
        func = _updateMembers

    if func:
        await func(msg.guild, msg.channel, *nextArgs)
    else:
        await msg.channel.send(failMsg)


######################
# - Slash Commands - #
######################

@bot.tree.command(name = "updatemembers", description = "Update/Refresh this servers members list message") #, guild=discord.Object(id=1023939580963061850)
async def slashUpdateMembers(interaction: discord.Interaction):
    await _updateMembers(interaction.guild, interaction.channel, interaction = interaction)

@bot.tree.context_menu(name = "Update Members")
async def contextUpdateMembers(interaction: discord.Interaction, user: discord.Member):
    await _updateMembers(interaction.guild, interaction.channel, interaction = interaction)

#########################
# - Specific Commands - #
#########################

@bot.command()
async def getMembers(msg):
    await _getMembers(msg)

@bot.command()
async def getCapitalRaidInfo(msg):
    await _getCapRaid(msg)

@bot.command()
async def getClanWarInfo(msg):
    clan = DatabaseTools.GetPrimaryClan(msg.guild.id)
    newMessageContent = ClashInterface.GetPreviousClanWar(tokens["CoC"]["token"], clan)

    await msg.channel.send(newMessageContent)

@bot.command()
async def getClanInfo(msg):
    await _getClanInfo(msg)

@bot.command()
async def clanInfo(msg):
    await _getClanInfo(msg)

@bot.command()
async def updateMembers(msg, *args):
    await _updateMembers(msg.guild, msg.channel, *args)

@bot.command()
async def linkClan(msg, *args):
    await _linkClan(msg, args[0])

@bot.command()
async def getEmojis(msg, *args):
    if msg.author.id in [admins[adminName]["id"] for adminName in list(admins.keys())]:
        print(await msg.guild.fetch_emojis())

############################
# - @bot.event functions - #
############################

@bot.event
async def on_command_error(msg, error): # Function that runs when an unidentified command is called
    await msg.channel.send(error)

@bot.event
async def on_ready(): # Function that runs when bot goes online
    # Print online messages to the console
    print("------")
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

    # Update the bots status
    await bot.change_presence(activity=discord.Game(name="Clash of Clans"))

    # Send a message to the dev channel to say the bot is online
    channel = bot.get_channel(1034065407147003915)
    await channel.send("Bot Online")

    # sync the slash comamnds
    await bot.tree.sync()

bot.run(tokens["Discord"]["token"]) # Run the bot


"""
Emojis:
[
    <Emoji id=1023940188491239444 name='clanbadge' animated=False managed=False>, 
    <Emoji id=1032958637678792704 name='c000' animated=False managed=False>, 
    <Emoji id=1032958645794775141 name='c001' animated=False managed=False>, 
    <Emoji id=1032958656607694909 name='c010' animated=False managed=False>, 
    <Emoji id=1032958665554141205 name='c011' animated=False managed=False>, 
    <Emoji id=1032958673036783667 name='c100' animated=False managed=False>, 
    <Emoji id=1032958679311454248 name='c101' animated=False managed=False>, 
    <Emoji id=1032958686206885888 name='c110' animated=False managed=False>, 
    <Emoji id=1032958693832151130 name='c111' animated=False managed=False>, 
    <Emoji id=1043476279061643274 name='cc0' animated=False managed=False>, 
    <Emoji id=1043476280630325289 name='cc1' animated=False managed=False>, 
    <Emoji id=1043476282136084520 name='cg0' animated=False managed=False>, 
    <Emoji id=1043476283381780610 name='cg1' animated=False managed=False>, 
    <Emoji id=1043476284770099240 name='cw0' animated=False managed=False>, 
    <Emoji id=1043476286112272414 name='cw1' animated=False managed=False>, 
    <Emoji id=1043481716490244128 name='coctrophy' animated=False managed=False>, 
    <Emoji id=1043483318215254078 name='townhall' animated=False managed=False>, 
    <Emoji id=1043484073462607984 name='activity' animated=False managed=False>, 
    <Emoji id=1043539783357579264 name='wo0' animated=False managed=False>, 
    <Emoji id=1043539784926248960 name='wo1' animated=False managed=False>, 
    <Emoji id=1043539822976966706 name='tl0' animated=False managed=False>, 
    <Emoji id=1043539824205910118 name='tl1' animated=False managed=False>, 
    <Emoji id=1043539825736810638 name='tl2' animated=False managed=False>, 
    <Emoji id=1043539827041255484 name='tl3' animated=False managed=False>, 
    <Emoji id=1043539828173705238 name='tl4' animated=False managed=False>, 
    <Emoji id=1043539829838839909 name='tl5' animated=False managed=False>, 
    <Emoji id=1043539831495598130 name='tl6' animated=False managed=False>, 
    <Emoji id=1043539832753889290 name='tl7' animated=False managed=False>, 
    <Emoji id=1043539834003800064 name='tl8' animated=False managed=False>
]
"""