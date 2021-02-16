import actions


def botManager(w, message):
    author = message.author
    guild = message.guild
    if guild.owner == author:
        return True
    if author.guild_permissions.administrator:
        return True
    if author.guild_permissions.manage_guild:
        return True
    if message.author.id in getSetting(w, "manageUsers"):
        return True
    included_managing_roles = [
        r for r in message.author.roles if r.id in getSetting(w, "manageRoles")
    ]
    if len(included_managing_roles) > 0:
        return True
    return False


def onlyInDM(w, message):
    return type(message.channel) == discord.DMChannel


def onlyInChannel(w, message):
    return type(message.channel) == discord.TextChannel


def onlyInActiveChannel(w, message):
    return message.channel.id in getSetting(w, "activeChannels")


def guard(condition):
    def guard_decorator(command):
        @functools.wraps(command)
        async def guard_func(w, message, args):
            if condition(w, message):
                await command(w, message, args)

        return guard_func


# Command Handlers
@guard(botManager)
async def cStop(w, message, args):
    actions.stop()


@guard(botManager)
async def cReload(w, message, args):
    actions.reload()


@guard(botManager)
async def cSnapshot(w, message, args):
    actions.snapshot()


@guard(botManager)
async def cRestore(w, message, args):
    if len(args) != 2:
        return

    actions.restore(args[1])


@guard(botManager)
async def cPull(w, message, args):
    if len(args) != 3:
        return

    actions.pull(args[1], args[2])


@guard(botManager)
async def cSettings(w, message, args):
    if len(args) == 1:
        await message.channel.send("```python\n{}```".format(w.settings))
        return

    option = args[1]

    if option == "prefix" and len(args) > 2:
        updateSetting(w, "prefix", args[2])
        await message.channel.send("Prefix changed to {}".format(args[2]))

    elif option == "logset" and onlyInChannel(w, message):
        updateSettings(w, "logChannel", message.channel.id)
        await message.channel.send(
            "{} will now log exceptions in this channel after it is restarted".format(
                getSettings(w, "name")
            )
        )

    elif option == "adduser" and len(message.mentions) > 0:
        updateSetting(
            w,
            "manageUsers",
            getSetting(w, "manageUsers").append(message.mentions[0].id),
        )
        await message.channel.send(
            "{0.mention} added to the manager list".format(message.mentions[0])
        )

    elif option == "removeuser" and len(message.mentions) > 0:
        updateSetting(
            w,
            "manageUsers",
            getSetting(w, "manageUsers").remove(message.mentions[0].id),
        )
        await message.channel.send(
            "{0.mention} removed from the manager list".format(message.mentions[0])
        )

    elif option == "addrole" and len(message.role_mentions) > 0:
        updateSetting(
            w,
            "manageRoles",
            getSetting(w, "manageRoles").append(message.role_mentions[0].id),
        )
        await message.channel.send(
            "Role {0.mention} added to the manager list".format(
                message.role_mentions[0]
            )
        )

    elif option == "removerole" and len(message.role_mentions) > 0:
        updateSetting(
            w,
            "manageRoles",
            getSetting(w, "manageRoles").remove(message.role_mentions[0].id),
        )
        await message.channel.send(
            "Role {0.mention} removed from the manager list".format(
                message.role_mentions[0]
            )
        )

    elif option == "addchannel":
        if len(message.channel_mentions) > 0:
            channel = message.channel_mentions[0]
        elif onlyInChannel(w, message):
            channel = message.channel
        else:
            return

        updateSetting(
            w, "activeChannels", getSetting(w, "activeChannels").append(channel.id)
        )
        await message.channel.send("Now active in {0.mention}".format(channel))

    elif option == "removechannel":
        if len(message.channel_mentions) > 0:
            channel = message.channel_mentions[0]
        elif onlyInChannel(w, message):
            channel = message.channel
        else:
            return

        updateSetting(
            w, "activeChannels", getSetting(w, "activeChannels").remove(channel.id)
        )
        await message.channel.send("No longer active in {0.mention}".format(channel))


@guard(botManager)
def cTestException(w, message, args):
    l = []
    print(l[0])


permissions = {
    "category": ["in_category", "manage_channel"],
    "channel": ["read_messages", "send_messages", "embed_links"],
}


@guard(botManager)
async def cTestPermissions(w, message, args):
    guild = message.guild
    category = message.channel.category
    channel = message.channel
    missing = []

    def join(a):
        return lambda b: (a, b)

    if "guild" in w.permissions:

        def permissionPredicate(permission):
            return hasattr(guild.me.guild_permissions, permission) and not getattr(
                guild.me.guild_permissions, permission
            )

        missing += map(
            join("guild"), filter(permissionPredicate, w.permissions["guild"])
        )

    if "category" in w.permissions and category:

        def permissionPredicate(permission):
            return hasattr(
                category.permissions_for(channel.guild.me), permission
            ) and not getattr(category.permissions_for(channel.guild.me), permission)

        missing += map(
            join("category"), filter(permissionPredicate, w.permissions["category"])
        )

    if "channel" in w.permissions:

        def permissionPredicate(permission):
            return hasattr(
                channel.permissions_for(channel.guild.me), permission
            ) and not getattr(channel.permissions_for(channel.guild.me), permission)

        missing += map(
            join("channel"), filter(permissionPredicate, w.permissions["channel"])
        )

    await message.channel.send(
        "**Missing permissions**\n```{}```".format(guild, json.dumps(missing))
    )


async def cHelp(w, message, args):
    commands = ", ".join(commandHandlers.keys())
    await message.channel.send("**Commands**\n```{}```".format(commands))


defaultCommands = {
    # Bot Manager
    "stop": cStop,
    "reload": cReload,
    "snapshot": cSnapshot,
    "restore": cRestore,
    "pull": cPull,
    "settings": cSettings,
    "exception": cTestException,
    "permissions": cTestPermissions,
    # General
    "help": cHelp,
}


def hasPrefix(message, prefix):
    chars = len(prefix)
    if chars == 0:
        return True
    if message.content[:chars] == prefix:
        return True
    return False


def parseMessage(message, prefix):
    args = message.content.split(" ")
    args[0] = args[0][len(prefix) :]
    command = args[0].lower()

    return command, args


async def runCommand(w, message):
    prefix = getSetting(w, "prefix")

    if not hasPrefix(message, prefix):
        return

    command, args = parseMessage(message, prefix)

    if command in commandHandlers:
        handler = commandHandlers[command]
        await handler(w, message, args)
    else:
        await message.channel.send("Unknown command {}".format(command))
        return


async def handleCommand(w, message):
    try:
        await runCommand(w, message)
        db.commit()
    except Exception as e:
        logger.exception("Error executing command: {}", message)
        db.rollback()
