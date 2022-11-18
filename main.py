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


############################
# - async base functions - #
############################

async def _getMembers(msg):
    message = ""
    
    clan = DatabaseTools.GetPrimaryClan(msg.guild.id)
    members = ClashInterface.GetMembers(tokens["CoC"]["token"], clan)
    for member in members:
        message += f"{member['name']}\n"
    
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
