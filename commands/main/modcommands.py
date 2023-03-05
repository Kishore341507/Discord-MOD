import discord
from discord.ext import commands
import typing
from botmain import client
from datetime import datetime , date , time , timedelta
import re
import asyncio
import json
from discord.ext.commands import BucketType, cooldown
import traceback
from discord.ui import Button , View , Select , TextInput
import chat_exporter
import io
import time
import random
from discord import app_commands


time_regex = re.compile(r"(\d{1,5}(?:[.,]?\d{1,5})?)([smhd])")
time_dict = {"h":3600, "s":1, "m":60, "d":86400}

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        matches = time_regex.findall(argument.lower())
        time = 0
        for v, k in matches:
            try:
                time = time_dict[k]*float(v)
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v)) 
        if time == 0 :
            time = 2419200
            argument = "28days"              
        return time , argument

class Reactionview(View):
    
    def __init__(self , timeout ,link ):
        super().__init__(timeout=timeout)
        self.add_item(discord.ui.Button(label='Orignal Message', url=link)) 


class Modcommands(commands.Cog):

    def __init__(self , client):
        self.client = client
        self.starbord = {}
        # self.info = {'emoji': [], 'channel': 966022735333572638, 'reaction_count': 8, 'staff_count': 3}
               
 
    # @app_commands.command()
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_guild=True)
    # async def ad(self , interaction , attachment : discord.Attachment , link : typing.Optional[str]= "https://www.ajio.com/shop/sneaker-store" ,  text : typing.Optional[str] = "Hey! I just finished The AJIO SneakerQuest Game and unlocked cool AJIO vouchers to get the world's finest Sneakers. You can play this too!" , button_label : typing.Optional[str] = "CLICK ME TO WIN SNEAKERS" ,  title : typing.Optional[str] = None):
    #     embed = discord.Embed(color= discord.Color.blue() , title= title , description= f"[{text}]({link})" , url= link) 
    #     embed.set_author(name= "AJIO.COM" , url = link , icon_url= "https://cdn.discordapp.com/attachments/1059511042604015696/1069137540227018852/Ajio-Logo_1.webp" )
    #     view = discord.ui.View(timeout= None)
    #     view.add_item(discord.ui.Button( style= discord.ButtonStyle.link , url= link , label= button_label ))
    #     embed.set_image(url = attachment.url)
    #     await interaction.response.send_message("done" , ephemeral = True)
    #     await interaction.followup.send(embed = embed , view = view)


    @commands.hybrid_command(name= "bot-dev-form")
    @commands.guild_only()
    async def botdevform(self , ctx):
        await ctx.interaction.response.send_modal(Feedback())
      

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def av(self,ctx,user:typing.Optional[discord.Member]=None, size:typing.Optional[int]=4096):
        user = user or ctx.author
        embed = discord.Embed(color=0x00000 , description = user.mention, timestamp = datetime.now())
        embed.set_author(name = user, icon_url = user.display_avatar)
        embed.set_image(url = user.display_avatar.with_size(size))
        await ctx.send(embed=embed) 


    @commands.hybrid_command(aliases=["w"])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def whois(self,ctx,user:typing.Optional[discord.Member]=None):
        user = user or ctx.author
        embed = discord.Embed(color=0x00000 , description = user.mention, timestamp = datetime.now())
        embed.set_author(name = user, icon_url = user.display_avatar)
        embed.add_field(name = "Joined", value = f"- <t:{int(user.joined_at.timestamp())}:F>\n- <t:{int(user.joined_at.timestamp())}:R>")
        embed.add_field(name = "Registered", value = f"- <t:{int(user.created_at.timestamp())}:F>\n- <t:{int(user.created_at.timestamp())}:R>")
        roles = " "
        for x in reversed(user.roles):
            roles = roles + f"{x.mention} "
        embed.add_field(name = f"Roles[{len(user.roles)}]", value = roles, inline = False)
        perms = " "
        for x in user.guild_permissions.elevated():
            if x[1] is True:
                perms = perms + f"{x[0].capitalize()} ,"
        # embed.add_field(name = "Key Permission", value = (perms.rstrip(",")).replace("_"," "), inline = False)
        embed.set_footer(text = f"{user.id} chaisuta op")
        embed.set_thumbnail(url = user.display_avatar)
        await ctx.send(embed=embed) 

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def warn(self , ctx , user : discord.Member ,*, reason : str):
        await ctx.defer()
        await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time , guild_id ) VALUES ($1 , $2 , $3 , $4 , $5 , $6 )' , user.id , "Warn" , str(ctx.author) , reason , datetime.now().timestamp() , ctx.guild.id )
        embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been warned***")
        embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ You have been warned in {ctx.guild.name} server \n**Reason** - {reason}")
        await ctx.send(embed = embed)
        try :
            await user.send(embed = embed2)
        except :
            pass

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def modlogs(self , ctx , user : discord.Member , not_in_server : typing.Optional[str] = None):
        if not_in_server is not None : 
            user_id =int(not_in_server)
            user = not_in_server
        else:
            user_id = user.id    
        await ctx.defer()
        data = await client.db.fetch('SELECT * FROM modlogs WHERE user_id = $1 AND guild_id = $2 ORDER BY "case" DESC '  , user_id , ctx.guild.id)
        dis = " "
        for case in data:
                mod = ctx.guild.get_member(case['mod_id'])
                if mod is None or ctx.guild.me :
                    mod = case['mod']
                dis = dis + f"**Case {case['case']}**\n**Action** - {case['action']}\n**Mod** - {mod}\n**Reason** - {case['reason']} , <t:{case['time']}:R>\n"
                if case['duration'] is not None :
                    dis = dis + f"**Duration** - {case['duration']}\n\n"
                else:
                    dis = dis + "\n" 
        embed = discord.Embed(color= discord.Color.blue() , title= f"{user}'s Modlogs" , description=dis)
        await ctx.send( embed = embed)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members = True)
    async def delwarn(self , ctx , case : int):
        await ctx.defer()
        x = await client.db.execute('DELETE FROM modlogs WHERE "case" = $1 AND guild_id = $2'  , int(case) , ctx.guild.id)
        await ctx.send(f"{x} case from logs ✅")

    
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members = True)
    async def kick(self , ctx, user: discord.Member, *, reason=None):
        await ctx.defer()
        embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been kicked***")
        embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ You have been kicked from {ctx.guild.name} server \nReason = {reason}")
        try :
            await user.send(embed = embed2)
        except :
            pass    
        asyncio.sleep(1)
        await user.kick(reason=reason)
        await ctx.send(embed = embed)
        await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time , guild_id ) VALUES ($1 , $2 , $3 , $4 , $5 , $6 )' , user.id , "Kick" , str(ctx.author) , reason , datetime.now().timestamp() , ctx.guild.id)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members = True)
    async def ban(self ,ctx, user: discord.Member, *, reason:str=None):
        await ctx.defer()
        embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been Baned***")
        embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ You have been Banned from {ctx.guild.name} server \n Reason = {reason}")
        if ctx.author.id == 591011843552837655 :
            await ctx.send(embed = embed)
            return
        try :
            await user.send(embed = embed2)
        except :
            pass
           
        asyncio.sleep(1)
        await user.ban(reason=reason)
        await ctx.send(embed = embed)
        await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time , guild_id ) VALUES ($1 , $2 , $3 , $4 , $5 , $6)' , user.id , "Ban" , str(ctx.author) , reason , datetime.now().timestamp() , ctx.guild.id)
        
    # @commands.hybrid_command()
    # @commands.guild_only()
    # @commands.has_permissions(ban_members = True)
    # async def unban(self, ctx, user:int, *, reason:str=None):
    #     await ctx.defer()
    #     banned_users = await ctx.guild.bans()
    #     for ban_entry in banned_users:
    #         member = ban_entry.user
    #         if user == member.id:
    #             await ctx.guild.unban(member)
    #             embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has UnBaned***")
    #             await ctx.send(embed = embed)
    #             await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time ) VALUES ($1 , $2 , $3 , $4 , $5 )' , user , "UnBan" , str(ctx.author) , reason , datetime.now().timestamp())
    #             return
    #     await ctx.send("cant find this user in server banned List")


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def movevc(self , ctx , from_vc : discord.VoiceChannel , to_vc : discord.VoiceChannel ):
        await ctx.defer()
        i = 0
        for members in from_vc.members:
            i = i + 1
            await members.move_to(to_vc)
        await ctx.send(f"Done {i} user(s) moved from {from_vc.mention} to {to_vc.mention}")

    @commands.hybrid_command(aliases=["wv"])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def whichvc(self , ctx , user : discord.Member = None):
        await ctx.defer()
        Rauthor = None
        if ctx.message.reference is not None:
            msg = ctx.message.reference.cached_message
            Rauthor = msg.author
        user = user or Rauthor or ctx.author
        data = user.voice
        if data is None :
            await ctx.send(f"{user} is Not in a VC")
        else:
            await ctx.reply(data.channel.mention)    

    @commands.hybrid_command(aliases=["ap"])
    @commands.guild_only()
    async def addperms(self,ctx, user:discord.Member):
        
        channel = ctx.channel
        
        if not channel.permissions_for(ctx.author).manage_channels:
            await ctx.send(f"you are not allowed to change channel perms" , delete_after = 3 )
            return
        
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        overwrite.view_channel = True
        await channel.set_permissions(user, overwrite=overwrite)
        await ctx.send(f"{user.mention} has been added to {channel.mention}")


    @commands.hybrid_command(aliases=["rp"])
    @commands.guild_only()
    async def removeperms(self,ctx,*, user: discord.Member):
       
        channel = ctx.channel
        
        if not channel.permissions_for(ctx.author).manage_channels:
            await ctx.send(f"you are not allowed to change channel perms" , delete_after = 3 )
            return 
        
        await channel.set_permissions(user, overwrite=None)
        await ctx.send(f"{user.mention} has been removed from {channel.mention}")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def dump(self , ctx , role : typing.Optional[discord.Role] = None , type : typing.Optional[typing.Literal['u' , 'n' , 'i' , 't']] = None , format : typing.Optional[typing.Literal['e']] = None , ping : typing.Optional[bool] = False ):
        await ctx.channel.typing()
        if role is None :
            role = ctx.guild.default_role
        if type == None :
            list = [f"{x} , {x.id} , {x.mention}" for x in role.members]
        if type == 'u' :
            list = [f"{x}" for x in role.members]
        elif type == 'n' :
            list = [f"{x.nick or x}"  for x in role.members]
        elif type == 'i' :
            list = [ f"{x.id}" for x in role.members]
        elif type == 't' :
            list = [ x.mention for x in role.members]
            
        if format is None :
            text = '\n'.join(list)
        elif format == 'e':
            list = [f"{i+1}. {x}" for i , x in enumerate(list)  ]
            text = '\n'.join(list)
        try :     
            await ctx.send(text , allowed_mentions = discord.AllowedMentions(users= ping) )      
        except :
            txt = open("test.txt" , "w")
            new_file = txt.write(text)
            txt.close()
            file = discord.File( "test.txt" , filename= "dump.txt"   )
            await ctx.send(file = file)          
            
            
    @dump.error
    async def xxx(self , ctx , error):
       await ctx.send(error)
   
   
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def drag(self , ctx ,  user : typing.Optional[discord.Member] = None ,  channel : typing.Optional[discord.VoiceChannel] = None, to_user : typing.Optional[discord.Member] = None):
        await ctx.defer()
        Rauthor = None
        
        if ctx.message.reference is not None:
            msg = ctx.message.reference.cached_message
            Rauthor = msg.author
        user = user or Rauthor 
        if channel is None :
            channel2 = None
            if to_user is not None:
                if to_user.voice is None:
                    await ctx.send(f"{to_user} is not in vc.")
                    return
                channel2 = to_user.voice.channel
            channel = channel2 or ctx.author.voice.channel 
            if channel == None:
                await ctx.send("You didn't provide a vc or else you are not in vc")
                return
        data = user.voice
        if user.id == 752114356682227823 :
                await ctx.send("nope , not allowed")
                return
        if data is None :
            await ctx.send(f"{user} is Not in a VC")
        else:
            if not channel.permissions_for(ctx.author).connect:
                await ctx.send(f"you are not allowed to drag user in {channel.mention}")
                return
            await user.move_to(channel)
            await ctx.reply(f"{user} dragged to {channel.name}")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members = True)
    async def sup(self , ctx , channel : typing.Optional[discord.VoiceChannel] = None , time : TimeConverter = [120 , "2min"]):
        await ctx.defer()
        
        if channel is None :
            channel = ctx.author.voice.channel
            if channel == None:
                await ctx.send("You didn't provide a vc or else you are not in vc")
                return
        
        await channel.set_permissions( ctx.guild.default_role , use_voice_activation = False )
        await ctx.send(f"{channel.mention} is sup. for next {time[1]}")
        await asyncio.sleep(time[0])
        await channel.set_permissions( ctx.guild.default_role , use_voice_activation = None)
        await ctx.reply(f"{channel.mention} is Open Now")


    @commands.hybrid_command(aliases=["nickname" , "name"])
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames = True)
    async def nick(self , ctx ,  user : discord.Member ,  *,nickname : str = None):
        await ctx.defer()
        await user.edit(nick=nickname)
        await ctx.send(f"Nickname updated for user {user} to {nickname}")

    
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)
    async def purge(self , ctx, limit: int):
        await ctx.defer()
        await ctx.channel.purge(limit=limit)
        await ctx.send("Done")
        await ctx.channel.purge(limit=1)

    @commands.hybrid_command(aliases=["moderations" , "moderation"])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def muted(self , ctx):
        await ctx.defer()
        dis = " "
        for user in ctx.guild.members:
            if user.is_timed_out():
                dis = dis + f"{user} `{user.id}` - <t:{int(user.timed_out_until.timestamp())}:R> \n"
        embed = discord.Embed(color=discord.Colour.blue() , title = "Muted user's" , description=dis )        
        await ctx.send(embed = embed)      

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def mute(self , ctx , user : discord.Member , duration : typing.Optional[TimeConverter] = [2419200 , "28days"] , * , reason : str = None):
        await ctx.defer()
        await user.timeout( timedelta(seconds=duration[0])  )
        time = datetime.now().timestamp() + int(duration[0])
        embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been Muted***")
        embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ ***You have been Muted from {ctx.guild.name} server , Unmute*** <t:{int(time)}:R> \n**Reason** - {reason}")
        await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time , duration , guild_id) VALUES ($1 , $2 , $3 , $4 , $5 , $6 , $7 )' , user.id , "Mute" , str(ctx.author) , reason , datetime.now().timestamp() , duration[1]  , ctx.guild.id)
        await ctx.send(embed = embed)
        try :
            await user.send(embed = embed2)
        except :
            pass

    @commands.hybrid_command(aliases=['vm'])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def vmute(self , ctx , user : discord.Member):
        await user.edit(mute = True)
        await ctx.send(f"{user} is muted in vc's")

    @commands.hybrid_command(aliases=['vum'])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def vunmute(self , ctx , user : discord.Member):
        await user.edit(mute = False)
        await ctx.send(f"{user} is unmuted in vc's now")   

    @commands.hybrid_command(aliases=["out" , "to"])
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def timeout(self , ctx , user : discord.Member = None):
        await ctx.defer()
        Rauthor = None
        if ctx.message.reference is not None:
            msg = ctx.message.reference.cached_message
            Rauthor = msg.author
        user = user or Rauthor    
        await user.timeout( timedelta(seconds=60))
        time = datetime.now().timestamp() + 60
        embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been Temporarily Muted***")
        embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ ***You have been Muted from {ctx.guild.name} server , Unmute*** <t:{int(time)}:R> \n**Reason** - Temporarily mute")
        #await ctx.send(embed = embed)
        await ctx.message.add_reaction( random.choice(ctx.guild.emojis) )
        try :
            await user.send(embed = embed2)
        except :
            pass        

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members = True)
    async def unmute(self , ctx , user : discord.Member , * , reason : str = None):
        await ctx.defer()
        if user.is_timed_out():
            await user.timeout(None)
            embed = discord.Embed(color=discord.Color.green() , description=f"✅ ***{user} has been Unmuted***")
            embed2 = discord.Embed(color=discord.Color.red() , description=f"✅ ***You have been Unmuted from {ctx.guild.name} server***")
            await client.db.execute('INSERT INTO modlogs(user_id , action , mod , reason , time , guild_id) VALUES ($1 , $2 , $3 , $4 , $5 , $6 )' , user.id , "Unmute" , str(ctx.author) , reason , datetime.now().timestamp() , ctx.guild.id )
            await ctx.send(embed = embed)
            try :
                await user.send(embed = embed2)
            except :
                pass
        else :
            embed = discord.Embed(color=discord.Color.red() , description=f"❎ ***{user} is not muted***")  
            await ctx.send(embed = embed)         

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(kick_members = True)
    async def reason(self, ctx , case:int , * , reason : str):
        x = await client.db.execute('UPDATE modlogs SET "reason" = $1 WHERE "case" = $2 AND guild_id = $3'  , reason , case , ctx.guild.id )
        await ctx.send(f"{x} **case**\nReason - {reason}")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def sm(self , ctx, seconds: int = 0):
         await ctx.channel.edit(slowmode_delay=seconds)
         if seconds==0:
            await ctx.reply(f"slowmode removed !")
         else:
            await ctx.reply(f"Set the slowmode in this channel to {seconds} seconds!")
    
    # cant be change (will be dynamic soon)
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def rule(self , ctx , no : int):
      embed = discord.Embed(color = discord.Color.red())         
      if no == 1:
        embed.title = "`R1` Be Kind and Respectful"
        embed.description= "Do not organize, participate in, or encourage harassment of others, be kind and humble to everyone. Be mature, stop the debate before it becomes an argument"
        await ctx.send(embed = embed )
      elif no == 2:
        embed.title = " `R2` No Nsfw Interactions"
        embed.description="Our server is completely against all sorts of NSFW content. Keep the server appropriate for everyone. Violation of this rule will directly impact your public profile and may lead to consequences"
        await ctx.send(embed = embed)
      elif no == 3:
        embed.title = "`R3` Respect Other's privacy"
        embed.description= "Respect people's personal information, no doxing or exposing addresses, social media, real names, relationships, sexualities, etc."
        await ctx.send(embed = embed )
      elif no == 4:
        embed.title = "`R4` Discord Community Guidelines"
        embed.description= "Anyone using discord is asked to strictly follow discord's community guidelines and Terms of Service."
        await ctx.send(embed = embed )
      elif no == 5:
        embed.title = "`R5` No Spamming"
        embed.description= "There are no mass texting channels, including copy-paste, large paragraphs, mass mentions, or space blocks."
        await ctx.send(embed = embed )
      elif no == 6:
        embed.title = "`R6` Respect to our Staff"
        embed.description= "Our staff works constantly for the betterment of the server and thus taunting/messing with any of the staff members is a punishable offense and will not be tolerated. If the issue with the staff is not resolved the members are asked to contact the higher authority to decide whatever has to be done."
        await ctx.send(embed = embed )
      elif no == 7:
        embed.title = "`R7` Mods are Friendly"
        embed.description= "Please don't hesitate to tag a mod or admin if you have a problem or suggestion so we can try to help or resolve it."
        await ctx.send(embed = embed )
      elif no == 8:
        embed.title = "`R8` Rules are Important"
        embed.description= "Be attentive and cautious of rules, you will be warned, muted, or banned depending on the severity of your rule violation."
        await ctx.send(embed = embed )
      elif no == 9:
        embed.title = "`R9` Banned Word"
        embed.description= "Well yes, its finally happening . here's the link for all the banned words on the server. Bypassing completely banned words by any means will result in punishment.(note : obviously we cant cover the entire dictionary filled with derogatory terms, so please use common sense while engaging with other server members)."
        await ctx.send(embed = embed )


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(ban_members = True)
    async def say(self, ctx,*, what : str):
        await ctx.message.delete()
        await ctx.send(f'{what}')

       
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)
    async def purgeuser(self , ctx, user : discord.Member  , limit: int):
        await ctx.defer()
        def check(m):
            return m.author == user
        await ctx.channel.purge(limit=limit , check = check)

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)    
    async def banword(self , ctx, word : str ):
        rules = await ctx.guild.fetch_automod_rules()
        rule = None 
        for i in reversed(rules) :
            if i.name == "Rumblez Mod":
                rule = i
        if rule is None :
          rule = await ctx.guild.create_automod_rule(name = "Rumblez Mod" , event_type = discord.AutoModRuleEventType.message_send , trigger=  discord.AutoModTrigger(  keyword_filter =[word]), actions = [discord.AutoModRuleAction( channel_id=None , duration=None)]  ,enabled = True) 
          await ctx.send(f"`{word}` has been added in automod word list")
          return   
        lis = rule.trigger.keyword_filter
        lis.append(word)
        await rule.edit(trigger = discord.AutoModTrigger(keyword_filter = lis ) )
        await ctx.send(f"`{word}` has been added in automod word list")


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)    
    async def unbanword(self , ctx, word : str ):
        rules = await ctx.guild.fetch_automod_rules()
        rule = None 
        for i in reversed(rules) :
            if i.name == "Rumblez Mod":
                rule = i
        if rule is None:
            await ctx.send("No word baned by me")
            return         
        lis = rule.trigger.keyword_filter
        try:
            lis.remove(word)
        except :    
            await ctx.send(f"{word} is not in my word-ban list")
            await ctx.author.send(f"word ban list - ```{lis}```")
            return
        await rule.edit(trigger = discord.AutoModTrigger(keyword_filter = lis ) )
        await ctx.send(f"`{word}` has been removed from automod word list")

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)    
    async def showword(self , ctx ):
        rules = await ctx.guild.fetch_automod_rules()
        rule = None 
        for i in reversed(rules) :
            if i.name == "Rumblez Mod":
                rule = i
        if rule is None :
          rule = await ctx.guild.create_automod_rule(name = "Rumblez Mod" , event_type = discord.AutoModRuleEventType.message_send , trigger=  discord.AutoModTrigger(  keyword_filter =[]), actions = [discord.AutoModRuleAction( channel_id=None , duration=None)]  ,enabled = True) 
        lis = rule.trigger.keyword_filter
        await ctx.send(f"```{lis}```")


    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages = True)    
    async def getembed(self , ctx , id : str ):
        msg = await ctx.channel.fetch_message(int(id))
        lis = msg.embeds
        data = ' '
        for embed in lis :
            x = embed.to_dict()
            x.pop("type")
            await ctx.send(f'```json\n{{"embeds": [{json.dumps(x)}]}}```')


    @commands.hybrid_command()
    @commands.guild_only()
    @cooldown(1, 600, BucketType.user)
    async def request(self , ctx , channel : discord.VoiceChannel):
        await ctx.defer()
        data = ctx.author.voice
        if data is None :
            await ctx.send(f"you are not in vc")
            ctx.command.reset_cooldown(ctx)
            return  
        
        view = MyView(timeout=300 , ctx = ctx , channel= channel)    
        msg = await ctx.send(f"{ctx.author} wants to join {channel.mention} , will be dragged if all channel members approve by reacting this message" , view = view)
  
    @request.error
    async def request_error(self,ctx , error):
        if isinstance(error, commands.CommandOnCooldown):
            sec = int(error.retry_after)
            min , sec = divmod(sec, 60)
            message = f"⌚ | you cant use this command for next {min}min {sec}seconds."
            await ctx.author.send(message)
            return 
        else :
            await ctx.send(error)     

    # @commands.Cog.listener()
    # async def on_reaction_add(self, reaction, user):
    #    if (reaction.emoji in self.info['emoji_id'] and reaction.count >= self.info['reaction_count']) or (user.id == 591011843552837655 and reaction.emoji == "<:Paod_Indian:995169982633750648>" ) :
           
    #        channel = user.guild.get_channel(self.info['channel'])
    #        if reaction.message.id in self.starbord :
    #            message = await channel.fetch_message(self.starbord[reaction.message.id])
    #            await message.edit( content =  f" {reaction}x{reaction.count} , {reaction.message.channel.mention}")
    #            return
               
    #        count = 0
    #        mem = []
    #        role = user.guild.get_role(1040222134594707486)
    #        async for i in reaction.users() :
    #            if role in i.roles :
    #                count += 1
    #            if i.id ==  591011843552837655 :
    #                count += 3   
    #            if len(mem) <= 2:    
    #                 mem.append(i.name)    
    #        if count <= self.info['staff_count'] :  
    #            return
           
    #        embed = discord.Embed(description= reaction.message.content )
    #        embed.set_author(name= reaction.message.author , icon_url= reaction.message.author.display_avatar )
    #        try :
    #             embed.set_image(url= reaction.message.attachments[0].url)
    #        except :
    #            pass    
    #        view = Reactionview(None, reaction.message.jump_url)
    #        msg = await channel.send(f" {reaction}x{reaction.count} , {reaction.message.channel.mention}" , embed = embed ,view = view  )
    #        self.starbord[reaction.message.id] = msg.id
           
                     
    # @app_commands.command()
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_guild=True)
    # async def starbord(self , interaction , emoji : typing.Optional[str] , channel : typing.Optional[discord.TextChannel] , reaction_count : typing.Optional[int] , staff_count : typing.Optional[int] ):
    #     if emoji :
    #         if emoji in self.info['emoji'] :
    #             self.info['emoji'].remove(emoji)
    #         else :    
    #             self.info['emoji'].append(emoji)
    #     if channel :
    #         self.info['channel'] = channel.id
    #     if reaction_count :
    #         self.info['reaction_count'] = reaction_count
    #     if staff_count :
    #         self.info['staff_count'] = staff_count
    #     await interaction.response.send_message(self.info) 



class MyView(View):

    def __init__(self ,  timeout , ctx , channel):
        super().__init__(timeout = timeout)
        self.ctx = ctx 
        self.channel = channel
        self.reactions = []

    @discord.ui.button(label = "0"  , emoji = "➕" , style=discord.ButtonStyle.green)  
    async def button1(self ,interaction ,  button ):

        if interaction.user in self.reactions :
            await interaction.response.send_message(f"you already voted" , ephemeral = True)
        elif interaction.user in self.channel.members :
            self.reactions.append(interaction.user)
            button.label = str(int(button.label) + 1 )
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("vote added" , ephemeral = True)
        else :
            await interaction.response.send_message(f"you are not in {self.channel.mention}" , ephemeral = True)    

        if (set(self.channel.members)).issubset(set(self.reactions)) and (len(self.channel.members) != 0):
            if self.ctx.author.voice == None :
                await interaction.followup.send(f"{self.ctx.author.mention} drag approved but your are not in vc") 
                return
            await self.ctx.author.move_to(self.channel)


class button(discord.ui.View):

    def __init__(self , lis):
        self.lis = lis
        super().__init__()

    @discord.ui.button(label = "Click ME" , style=discord.ButtonStyle.red)
    async def button1(self , interaction ,  button ):
        await interaction.response.send_modal(Feedback2(lis = self.lis))
        self.stop()


class Feedback(discord.ui.Modal, title='PLAYGROUND BOT DEV. FORM'):

    mail = discord.ui.TextInput(
        label="What's your mail ID?",
        style=discord.TextStyle.short,
        placeholder='(ex -abc123@mail.com)',
        custom_id= "What's your mail ID?"
    )

    age = discord.ui.TextInput(
        label="What's your current age?",
        style=discord.TextStyle.short,
        placeholder='type your age here in numbers',
        custom_id= "What's your current age?"
    )

    time = discord.ui.TextInput(
        label="How much time?",
        style=discord.TextStyle.short,
        placeholder='(ex- 5hrs - 6hrs)',
        custom_id= "How much time?"
    )

    async def on_submit(self, interaction: discord.Interaction):
        lis = [self.mail , self.age , self.time ]
        view = button(lis  = lis)
        await interaction.response.send_message(f'Hmm Almost done , click the button!!!', ephemeral=True ,view=view )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong.{error}', ephemeral=True)

class Feedback2(discord.ui.Modal, title='PLAYGROUND BOT DEV. FORM 2'):
    
    def __init__(self , lis):
        self.lis = lis
        super().__init__()


    q1 = discord.ui.TextInput(
        label="Q1",
        style=discord.TextStyle.paragraph,
        placeholder='Why do you want to apply for bot dev?',
        max_length=300 , 
        custom_id= 'Why do you want to apply for bot dev?'

    )

    q2 = discord.ui.TextInput(
        label="Q2",
        style=discord.TextStyle.paragraph,
        placeholder='Do you have any previous experience of bot dev?',
        max_length=300 , 
        custom_id= 'Do you have any previous experience of bot dev?'

    )

    q3 = discord.ui.TextInput(
        label="Q3",
        style=discord.TextStyle.paragraph,
        placeholder='How much knowledge do you have about discord and discord bots? (Please explain everything you know)',
        max_length=300 , 
        custom_id= 'How much knowledge do you have about discord and discord bots? (Please explain everything you know)'
    )

    q4 = discord.ui.TextInput(
        label="Q4",
        style=discord.TextStyle.paragraph,
        placeholder="which language do you prefer?",
        max_length=300 ,
        custom_id= "which language do you prefer?"
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.lis.extend([self.q1 ,self.q2 , self.q3 , self.q4 ])
        channel = interaction.guild.get_channel(983364730452332564)
        embed = discord.Embed(title= "Playground - MOD Form" , color= discord.Color.blurple() , description= f"{interaction.user} , {interaction.user.id}")
        for i in self.lis : 
            embed.add_field(name= i.custom_id , value= i.value)  
        await interaction.response.send_message(f'Thanks for your Responce! 💙', ephemeral=True)
        await channel.send("<@591011843552837655> " , embed = embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong.{error}', ephemeral=True)



async def setup(client):
   await client.add_cog(Modcommands(client))         
