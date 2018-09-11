#! /usr/bin/python3
# modified from https://linuxacademy.com/blog/geek/creating-an-irc-bot-with-python3/
#written in python 3.7
#created for clover_steel
# https://pypi.org/project/strawpoll.py/ pip install strawpoll.py
import socket
import datetime
import math
import sys
import os
import time

#defining connection variables
irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = 'irc.chat.twitch.tv'	#same for all twitch IRC
password = ""#obtained from -> http://www.twitchapps.com/tmi/		this is different for every channel
channel =  ""
AdminName = ""
bot_nickname = ""
exit_code = ""#"nini bot"

commands = {}

def joinchan(channel): # connecting to channel
	irc_socket.send(bytes("JOIN #%s\n" %channel,"UTF-8"))#joining the twitch chat to send messages
	ircmsg = ""
	while ircmsg.find("End of /NAMES list") == -1:	#this was in every example i found. doesnt seem to be needed but left it in
		ircmsg = irc_socket.recv(2048).decode("UTF-8")
		ircmsg = ircmsg.strip('\n\r')
		print(ircmsg)

def ping():
    irc_socket.send(bytes("PONG! \r\n","UTF-8"))#responds to server pings

def sendMsg(msg,channel): #function to send out messages
	#print("PRIVMSG %s :%s\r\n" % ("#%s" %(channel.lower()), msg))
	irc_socket.send(bytes("PRIVMSG %s :%s\r\n" % ("#%s" %(channel.lower()), msg),"UTF-8"))

def load_commands(commands): #loads response commands from commands.txt
	if os.path.exists("commands.txt"):	#if .txt exists
		f = open("commands.txt")#opens.txt
		for line in f:
			if ':' in line: #make sure line has command and response format
				line_partition = line.rpartition(':') #line split into 2 tuple [commands, output]
				output = line_partition[2]
				if ",," in line_partition[0]: # see if more than one command is in first tuple
					command_split = line_partition[0].split(',,') #splits command into tuples [command0, command1, command2...]
					#print(command_split)
					for key in command_split: #iterates command_split
						key = key.strip('\n\r')
						key = key.strip()
						commands[key] = output.strip()
				else:
					commands[line_partition[0]]= output.strip() #if only one command and one output exist on the line
	else:
		f = open("commands.txt",'w+')#else creates file and prompts user to create commands
		f.close()
		f = open("commands.txt", 'w')
		f.write("This is how you format commands. Please use a new line for each command\n\n")
		f.write("input command: output command\n\n")
		f.write("input ,, another input: both inputs work for the same output\n\n")
		print("A commands.txt file has been added to the current directory\nPlease close the window and create your commands")
	f.close()

def load_settings(): #pulls login settings from auth.txt
	if os.path.exists("auth.txt"): #if exists pull info from .txt
		f = open("auth.txt")
		line = f.readline()	#reads preloaded .txtfile
		line_partition = line.split(':')#splits into 5 partitions[channel,admin,nickname,exit_code,oauth:,password]
		f.close()
		partition = [line_partition[0],line_partition[1],line_partition[2],line_partition[3],"oauth:" + line_partition[5]] #merges oauth: and password since partition pulls them apart
		return partition
	else:	#else create file and fill with new info
		f = open("auth.txt",'w+')
		f.close()
		with open("auth.txt", 'a') as f:
			channel = input("What channel do you want to join? \n>>")
			f.write(channel.lower() + ":")
			temp = input("Are you the owner of this channel?\nYes:NO\n>>")
			temp = temp.lower()
			if 'y' in temp:
				AdminName = channel.lower()
				f.write(format(channel + ":"))
			else:
				AdminName = input("What is your Username?\n>>")
				f.write(AdminName.lower() + ":")
			bot_nickname = input("What is your bot's nickname?\nThis is for server connection and doesn't mean anything\n>>")
			f.write(bot_nickname + ":")
			exit_code = input("What do you want your exit command to be?\nThis command can be typed in the twitch chat to close the bot\nThis will not case sensitive\n>>")
			f.write(exit_code + ":")
			password = input("Sign into the twitch account you wish to be the bot.\nUsing this link << http://www.twitchapps.com/tmi/ >>\nGenerate an oauth for the account\nEnter it here >>")
			f.write(password)
	line_partition = [channel,AdminName,bot_nickname,exit_code,password]
	return line_partition		#returns user entered data

def main():
    line_partition = load_settings()
    load_commands(commands)
    channel = line_partition[0].lower()
    AdminName = line_partition[1].lower()
    bot_nickname = line_partition[2]
    exit_code = line_partition[3].lower()
    password = line_partition[4]

    #print(commands)

    irc_socket.connect((server,6667))
    irc_socket.send(bytes("PASS %s\n" %password,"UTF-8"))
    irc_socket.send(bytes("NICK %s\n" %bot_nickname,"UTF-8"))

    joinchan(channel) #connects bot to channel

    uptime = datetime.datetime.now()
    last_command_time = datetime.datetime.now()
    sendMsg("Good Morning!",channel)
    print("good morning!\n")
    ircmsg = ""

    while 1:	#waits for chat input and responds accordingly to commands.txt
    	ircmsg = irc_socket.recv(2048).decode("UTF-8")
    	ircmsg = ircmsg.strip('\n\r')
    	print(ircmsg)
    	if ircmsg.find("PRIVMSG") != -1:
    		name = ircmsg.split('!',1)[0][1:]
    		message = ircmsg.split("PRIVMSG",1)[1].split(':',1)[1].lower()
    		print(name + message)
    		if len(name) < 17:
    			if name.lower() == AdminName.lower() and message.strip().lower() == exit_code:
    				sendMsg("GoodNight!",channel)
    				irc_socket.send(bytes("QUIT\n","UTF-8"))
    				return
    			elif message.lower() == "!uptime":
    				current_time = datetime.datetime.now() - uptime
    				sendMsg(bot_nickname + " has been awake for: " + str(current_time),channel)
    			else:
    				for k,v in commands.items():
    					if message.lower() == k.lower() and ((datetime.datetime.utcnow() - last_command_time).seconds > 2): ## if message matches and more than 2 seconds have passed
    						sendMsg(v,channel)
    						last_command_time = datetime.datetime.utcnow()
    	else:
    		if ircmsg.find("PING :") != -1: # pings back to the twitch server
    			ping()

main()
