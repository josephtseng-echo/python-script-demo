#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
'''
base object
'''


import redis
import ConfigParser
import os
import logging
import logging.config
import datetime
import MySQLdb
import requests
import datetime
import time


class Base(object):
    # 配置文件后缀名
    _config_file_suffix = '.conf'
    # 配置文件路径，相对路径
    _config_file_path = '../data/'

    # new config
    _cf = None
    # new redis
    _redis = None
    # new logger
    _logger = None
    # config set
    _config_set = "test"
    # new mysql
    _mysql = None
    
    def __init__(self, config_set = None):
        if config_set != None:
            self._config_set = config_set
        # init config 
        self.initConfig()
        # init redis object
        self.initRedis()
        # init log object
        self.initLog()
        # init new mysql
        self.initMysql()

    def initMysql(self):
        if self._mysql == None:
            db_host = self._cf.get('mysql', 'host')
            db_user = self._cf.get('mysql', 'user')
            db_pass = self._cf.get('mysql', 'pass')
            db_name = self._cf.get('mysql', 'name')
            db_charset = self._cf.get('mysql', 'charset')
            self._mysql = MySQLdb.connect(host = db_host,
                                     user = db_user,
                                     passwd = db_pass,
                                     db = db_name,
                                     charset = db_charset)
            
    def initLog(self):
        '''
        new logger
        '''
        if self._logger == None:
            logging.config.fileConfig(self._config_file_path + "logging.conf")
            self._logger = logging.getLogger("bianalysisApp")
    
    def initConfig(self):
        '''
        get config data
        
        secs = cf.sections()
        print secs;

        opts = cf.options('redis')
        print opts

        kvs = cf.items('redis')
        print kvs

        value = cf.get(opts, item)
        '''        
        configFileName = self._config_file_path + str(self._config_set) + self._config_file_suffix
        if os.path.exists(configFileName) == True:
            try:
                self._cf = ConfigParser.ConfigParser()
                self._cf.read(configFileName)
            except:
                self._logger.error("对不起，配置文件不存在!")
                sys.exit()
        else:
            self._logger.error("对不起，配置文件不存在!")
            sys.exit()
        
    def initRedis(self):
        '''
        new redis
        '''
        if self._redis == None:
            redis_host = self._cf.get('redis', 'host')
            redis_port = self._cf.get('redis', 'port')
            redis_db = self._cf.get('redis', 'db')
            pool = redis.ConnectionPool(host = redis_host,
                                        port = redis_port,
                                        db = redis_db)
            self._redis = redis.StrictRedis(connection_pool=pool)
            
    def getNowDatetime(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def getRedisListMultiply(self, queueName):
        '''
        通过发送lua脚本批量获取redis list
        '''
        lua = """
        local key = KEYS[1]
        local n = ARGV[1]
        if not n or not key then
            return nil
        end

        local ret = {}
        for i=1,n do
            local v = redis.call("lpop", key)
            if v then
                ret[#ret+1] = v
            else
                break
            end
        end

        return ret
        """
        list = []
        try:
            getQueueMultiply = self._redis.register_script(lua)
            list = getQueueMultiply(keys=[queueName], args=[10])
        except:
            self._logger.error("get queue multiply error")
        return list

    def sendRtxContent(self, sendTitle, sendContent):
        rtx_send_users = self._cf.get('base', 'rtx_send_users')
        rtx_server_url = self._cf.get('base', 'rtx_server_url')
        rtx_app_id = self._cf.get('base', 'rtx_app_id')
        rtx_app_key = self._cf.get('base', 'rtx_app_key')
        postData = {
            'appId' : rtx_app_id,
            'appKey' : rtx_app_key,
            'userName' : rtx_send_users,
            'title' : sendTitle,
            'content' : sendContent
        }
        try:
            r = requests.post(rtx_server_url, data=postData, timeout = 5)
            if r.status_code == requests.codes.ok:
                return True
            else:
                self._logger.error("send rtx error")
                return False
        except:
            self._logger.error("send rtx except")
            return False


    def sendPhoneContent(self, sendContent):
        phone_send_users = self._cf.get('base', 'phone_send_users')
        phone_server_url = self._cf.get('base', 'phone_server_url')
        postData = {
            'to' : phone_send_users,
            'content' : sendContent
        }
        try:
            r = requests.post(phone_server_url, data=postData, timeout = 5)
            if r.status_code == requests.codes.ok:
                return True
            else:
                self._logger.error("send phone error")
                return False
        except:
            self._logger.error("send phone except")
            return False


    def getOldTimeStampBySecond(self, oldTimeSecond1, oldTimeSecond2):
        result = []
        nowTime =  datetime.datetime.now()
        for i in range(oldTimeSecond1, oldTimeSecond2):
            t = int(time.time()) - i
            result.append(t)
        return result
