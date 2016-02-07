#!/usr/bin/env python3
# -*- coding: utf-8 -*

import sys
import binascii
import json

from pysnmp.entity.rfc3413.oneliner import cmdgen

import configparser

import telegram

agentaddress = ""
agentcommunity = ""
telegramToken = ""
admin_chat_id = None

def init():
    if len(sys.argv)<1:
        print ("Please supply a configuration file")
        sys.exit(1)
    try:
        configfilename = sys.argv[1]
        config = configparser.ConfigParser()
        config.read(configfilename)
        global agentaddress
        global agentcommunity
        global telegramToken
        agentaddress = config['snmp']['agentaddress']
        agentcommunity = config['snmp']['agentcommunity']
        telegramToken = config['telegram']['token']
    except:
        print ("Error reading the configuration")
        sys.exit(2)
    global admin_chat_id
    try:
        admin_chat_id = config['telegram']['admin_chat_id']
    except:
        admin_chat_id = None

    


def get_snmp_info(query_name="",query_location=""):
    global agentaddress
    global agentcommunity
    agentport = 161
    infos = []
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.bulkCmd(
        cmdgen.CommunityData(agentcommunity),
        cmdgen.UdpTransportTarget((agentaddress,agentport)),
        0,
        25,
        (1,3,6,1,4,1,15983,1,1,4,4,1,1,5),
    )
    if (errorIndication or errorStatus):
 #       print ("Error getting names")
        sys.exit(1)

    for (name, val), in varBinds:
        if name.asTuple()[:14] != (1,3,6,1,4,1,15983,1,1,4,4,1,1,5):
            continue
        try:
            location = str(val).strip()
            tableindex = name.asTuple()[14]
        except:
            pass
        else:
#            print (userid)
            errorIndication, errorStatus, errorIndex, varBindsHost = cmdGen.getCmd(
                cmdgen.CommunityData(agentcommunity),
                cmdgen.UdpTransportTarget((agentaddress, agentport)),
                '1.3.6.1.4.1.15983.1.1.4.4.1.1.2.'+str(tableindex),
                '1.3.6.1.4.1.15983.1.1.4.4.1.1.8.'+str(tableindex),
                '1.3.6.1.4.1.15983.1.1.4.4.1.1.9.'+str(tableindex),
                '1.3.6.1.4.1.15983.1.1.4.4.1.1.12.'+str(tableindex),
                '1.3.6.1.4.1.15983.1.1.4.4.1.1.22.'+str(tableindex)
                )
            if errorIndication or errorStatus:
                continue
            for namehost,valhost in varBindsHost:
                if namehost.asTuple()[13] == 2:
                    mac = binascii.b2a_hex(valhost.asOctets())
                elif namehost.asTuple()[13] == 8:
                    name = str(valhost)
                elif namehost.asTuple()[13] == 9:
                    ssid = str(valhost)
                elif namehost.asTuple()[13] == 12:
                    rssi = int(valhost)
                elif namehost.asTuple()[13] == 22:
                    os = str(valhost)
                #if (query_location in location) and (query_name in name):
            if (query_name in name.strip().lower()) and (query_location in location.strip().lower()):
                infos.append( {'name':name,'mac':mac,'location':location,'rssi':rssi,'ssid':ssid,'os':os } )
    return infos

def reply_start(bot,update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Welcome!")
    admin_text="New user: {fromuser}, chatid: {chatid}".format(fromuser=(update.message.from_user.first_name+' '+update.message.from_user.last_name+' aka '+update.message.from_user.username),chatid=update.message.chat_id)
    print(admin_text)
    global admin_chat_id
    if admin_chat_id is not None:
        bot.sendMessage(chat_id=admin_chat_id,text=admin_text)


def reply_name(bot,update,args):
    if len(args) != 1:
        bot.sendMessage(chat_id=update.message.chat_id,text="Invalid number of parameters")
    else:
        name = args[0].split('@')[0].strip().lower()
        infos = get_snmp_info(query_name=name)
        if len(infos) > 0:
            text = '\n'.join([ ', '.join([ row[column] for column in ['name','location','os'] ]) for row in infos ])
        else:
            text = 'Not found'
        bot.sendMessage(chat_id=update.message.chat_id,text=text)

def reply_location(bot,update,args):
    if len(args) != 1:
        bot.sendMessage(chat_id=update.message.chat_id,text="Invalid number of parameters")
    else:
        location = args[0].strip().lower()
        infos = get_snmp_info(query_location=location)
        if len(infos) > 0:
            text = '\n'.join([ ', '.join([ row[column] for column in ['name','location','os'] ]) for row in infos ])
        else:
            text = 'Not found'
        bot.sendMessage(chat_id=update.message.chat_id,text=text)

def reply_unknown(bot,update):
    bot.sendMessage(chat_id=update.message.chat_id,text="Command not found")
        
def main():
    print ("Reading config")
    init()
    global telegramToken
    print ("Initialazing bot")
    updater = telegram.Updater(token=telegramToken)
    updater.dispatcher.addTelegramCommandHandler('start', reply_start)
    updater.dispatcher.addUnknownTelegramCommandHandler(reply_unknown)
    updater.dispatcher.addTelegramCommandHandler('name', reply_name)
    updater.dispatcher.addTelegramCommandHandler('location', reply_location)
    print ("polling...")
    updater.start_polling()






if __name__ == "__main__":
    main()    
