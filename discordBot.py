import logging
import re
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from datetime import timedelta
import asyncio

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True  

Token = 'TON TOKEN'

client = commands.Bot(command_prefix='+', intents=intents)

BAD_TERMS = [
    "fdp", "ntm", "FDP", "NTM", "Ntm", "Fdp", "bz", "pute", 
    "Negro", "nga", "nigger", "Nga", "negro", "nigga", "tg", "Tg"
] # tu peut add + de mot

URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

@client.event
async def on_ready():
    try:
        await client.change_presence(
            status=discord.Status.idle,
            activity=discord.Streaming(name="", url="https://www.twitch.tv/byilhann") # Change le name par le nom de votre serveur
        )
        print(f'Logged in as {client.user}')
    except Exception as e:
        print(f'An error occurred: {e}')
        

@client.event
async def on_connect():
    print("Bot has connected to Discord")

@client.event
async def on_disconnect():
    print("Bot has disconnected from Discord")

@client.event
async def on_error(event, *args, **kwargs):
    print(f"An error occurred: {event}")
    print(args)
    print(kwargs)

client.remove_command('help')

@client.command(name="help")
async def help_gen(ctx, source: str = None):

    embed = discord.Embed(
        title="Liste des Commandes",
        description="Voici toutes les commandes disponibles sur ce serveur :",
        color=discord.Color.blue()
    )
    embed.add_field(name="+help", value="Affiche cette liste de commandes", inline=False)
    embed.add_field(name="+clear <nombre>", value="Enleves le nombre de message que vous avez choisis", inline=False)
    embed.add_field(name="+ban <id>", value="ban la personne choisis", inline=False)
    embed.add_field(name="+unban <id>", value="Unban la personne choisis", inline=False)
    embed.add_field(name="+lock", value="Lock le channel", inline=False)
    embed.add_field(name="+unlock", value="Unlock le channel", inline=False)
    embed.add_field(name="+jail <id>", value="Add le role pour jail", inline=False)
    embed.add_field(name="+unjail <id>", value="Remove le role pour jail", inline=False)

    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if any(term.lower() in message.content.lower() for term in BAD_TERMS):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, attention à ton langage !")
        try:
            await message.author.timeout(timedelta(seconds=60), reason="Utilisation de termes interdits")
            await message.channel.send(f"{message.author.mention} a été mis en sourdine pendant 60 secondes.")
        except Exception as e:
            print(f"Erreur lors de la mise en sourdine : {e}")
        return

    if URL_REGEX.search(message.content):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, les liens ne sont pas autorisés !")
        try:
            await message.author.timeout(timedelta(seconds=60), reason="Envoi de liens non autorisés")
            await message.channel.send(f"{message.author.mention} a été mis en sourdine pendant 60 secondes")
        except Exception as e:
            print(f"Erreur lors de la mise en sourdine {e}")
        return

    if "ping" in message.content.lower():
        await message.channel.send("pong")

    await client.process_commands(message)

@client.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Mets un nombre positif")
        return
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  
        await ctx.send(f"Deleted {len(deleted) - 1} messages", delete_after=5)  
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete messages")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred: {e}")

@client.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member == ctx.author:
        await ctx.send("Vous ne pouvez pas vous bannir vous-même")
        return

    try:
        await member.ban(reason=reason)
        await ctx.send(f'{member} a été banni')
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de bannir ce membre")
    except Exception as e:
        await ctx.send(f"Une erreur est survenue {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Membre non trouvé")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("mot mal ecris ou manque de carachtère")
    else:
        await ctx.send("Une erreur est survenue.")

@client.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, member_id: int, *, reason=None):
    if ctx.author.id == member_id:
        await ctx.send("Vous ne pouvez pas vous débannir vous-même")
        return

    try:
        # Récupère les membres bannis
        banned_users = [entry async for entry in ctx.guild.bans()]
        member = discord.utils.get(banned_users, id=member_id)

        if member is None:
            await ctx.send("Ce membre n'est pas banni ou n'existe pas")
            return

        await ctx.guild.unban(member.user, reason=reason)
        await ctx.send(f'{member.user} a été débanni')
    except discord.Forbidden:
        await ctx.send("Je n'ai pas la permission de débannir ce membre")
    except Exception as e:
        await ctx.send(f"Une erreur est survenue {e}")

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("ID de membre invalide")
    else:
        await ctx.send("Une erreur est survenue")




@client.command()
@commands.has_permissions(administrator=True)
async def lock(ctx):
    role = ctx.guild.default_role 
    try:
        
        await ctx.channel.set_permissions(role, send_messages=False)
        await ctx.send("Le salon est maintenant verrouillé ")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite lors du verrouillage du salon {e}")

@lock.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Tu n'as pas les permissions pour utiliser cette commande")
    else:
        await ctx.send("Une erreur s'est produite lors de l'exécution de la commande")

@client.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    role = ctx.guild.default_role 
    try:
        
        await ctx.channel.set_permissions(role, send_messages=True)
        await ctx.send("Le salon est maintenant déverrouillé")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite lors du déverrouillage du salon {e}")

@unlock.error
async def unlock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Tu n'as pas les permissions pour utiliser cette commande")
    else:
        await ctx.send("Une erreur s'est produite lors de l'exécution de la commande")

@client.command(name="jail")
@commands.has_permissions(manage_roles=True)
async def jail(ctx, member: discord.Member):
    # Met le id de ton bot discord par "YOUR_ROLE_ID"
    role = discord.utils.get(ctx.guild.roles, id=YOUR_ROLE_ID)
    
    if role is None:
        await ctx.send("Role pas trouvé")
        return
    
    await member.add_roles(role)
    await ctx.send(f"Rôle ajouté à {member.name}")
    print(f'Rôle ajouté à {member.name}')


@client.command(name="unjail")
@commands.has_permissions(manage_roles=True)
async def unjail(ctx, member: discord.Member):
    # Met le id de ton bot discord par "YOUR_ROLE_ID"
    role = discord.utils.get(ctx.guild.roles, id=YOUR_ROLE_ID)
    
    if role is None:
        await ctx.send("Role pas trouvé")
        return
    
    await member.remove_roles(role)
    await ctx.send(f"Rôle retiré de {member.name}")
    print(f'Rôle retiré de {member.name}')


if __name__ == "__main__":
    print("Starting bot...")
    client.run(Token)