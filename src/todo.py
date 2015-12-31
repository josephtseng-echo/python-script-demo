#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
'''
BI业务逻辑处理
'''
import json
import MySQLdb
from base import Base
import time
import datetime
import random

class Todo(Base):

    def _init_(self, config_set):
        Base.__init__(config_set)


    def alarm(self):
        self.alarmBase()
        self.alarmQps()
        self.alarmQpsByM()
        # check server
        self.alarmSendRtx()
        self.alarmSendPhone()


    def alarmSendPhone(self):
        '''
        短信告警
        '''
        phone_send_check_nums = int(self._cf.get('base', 'phone_send_check_nums'))
        queueNameKey = 'redis_alarm_queue_name_qps';
        redis_alarm_queue_name = self._cf.get('bianalysis', queueNameKey)
        check_len = int(self._redis.llen(redis_alarm_queue_name))
        if check_len > phone_send_check_nums:
            self.sendPhoneContent("实时预警队列有积压未处理，请注意！")
        queueNameKey = 'redis_alarm_queue_name_base';
        redis_alarm_queue_name = self._cf.get('bianalysis', queueNameKey)
        check_len = self._redis.llen(redis_alarm_queue_name)
        if check_len > phone_send_check_nums:
            self.sendPhoneContent("实时预警队列有积压未处理，请注意！")        
        

    def alarmSendRtx(self):
        '''
        检测超过阀值入库的条数进行RTX报警
        '''        
        timeMinute = time.strftime('%M',time.localtime(time.time()))
        checkList = ['01', '10', '20', '30', '40', '50']
        checkTimeMinute = checkList.count(timeMinute)
        if checkTimeMinute > 0:
            beforeTimeHour = time.strftime('%Y-%m-%d %H',time.localtime(time.time()-60*60))+':00:00'
            nowTimeHour = time.strftime('%Y-%m-%d %H',time.localtime(time.time()))+':00:00'
            sql = "SELECT COUNT(*) AS NUMS FROM `tm_storm_statistics` WHERE\
            alarmStatisticsDatetime > '%s' and alarmStatisticsDatetime <= '%s' "
            cursor = self._mysql.cursor()
            cursor.execute(sql % (beforeTimeHour, nowTimeHour))
            result = cursor.fetchone()
            nums = 0;
            if result[0]:
                nums = int(result[0])
            if nums >= int(self._cf.get('base', 'rtx_send_check_nums')):
                #print "todo send rtx"
                self.sendRtxContent("统计告警", "统计上一个小时超过阀值太多，请注意！")
        
    def alarmTodo(self, queueName):
        '''
        告警处理
        '''
        list = self.getRedisListMultiply(queueName)
        queue_len = len(list)
        # test data
        #queuePopStr = '{"alarmName":"10.1.16.129:80","alarmType":1,"alarmVal":5000,"alarmDatetime" : "2015-05-01 00:00:00", "alarmServerId" : 3}'
        if queue_len > 0 :
            for item in list:
                queuePopJson = json.loads(item)
                print queuePopJson
                #todo write mysql
                self.writeToMysql(queuePopJson)
                self._logger.info(item)                
        else:
            self._logger.info("queue is null")

    def alarmQps(self):
        '''
        '''
        queueNameKey = 'redis_alarm_queue_name_qps';
        redis_alarm_queue_name = self._cf.get('bianalysis', queueNameKey)
        self.alarmTodo(redis_alarm_queue_name)

    def alarmQpsByM(self):
        '''
        每分钟统计上一小时分钟QPS情况
        '''
        qps_ip_lists = self._redis.smembers('qps:all:lists')
        if len(qps_ip_lists) > 0:
            sql = "INSERT INTO `qps_statistics_minute`(ip,serverid,qps,addtime,statistics_time, notes) VALUES"        
            for i in qps_ip_lists:
                i_k = self.getOldTimeStampBySecond(int(self._cf.get('bianalysis', 'total_old_time_start')), \
                                                   int(self._cf.get('bianalysis', 'total_old_time_end')))

                i_k_total = 0
                for j in i_k:
                    i_k_redis = str(i) + str(j)
                    if self._redis.get(i_k_redis) != None:
                        i_k_total += int(self._redis.get(i_k_redis))
                i_k_total = i_k_total / 60
                i_split = i.split(":")
                i_k_time_array = time.localtime(i_k[0])
                i_k_time_str = time.strftime("%Y-%m-%d %H:%M:00", i_k_time_array)
                sql += "('"+str(i_split[2])+"','"+str(i_split[1])+"','"+str(i_k_total)+"','"\
                       +str(self.getNowDatetime())+"','"+i_k_time_str+"', ''),"
            sql = sql[0:-1]
            try:
                cursor = self._mysql.cursor()
                cursor.execute(sql)
                cursor.close()
                self._mysql.commit()
            except MySQLdb.Error,e:
                self._logger.error(str(e.args[0]) + str(e.args[1]))
                        

    def alarmBase(self):
        '''
        原本需求处理
        '''
        queueNameKey = 'redis_alarm_queue_name_base';
        redis_alarm_queue_name = self._cf.get('bianalysis', queueNameKey)
        self.alarmTodo(redis_alarm_queue_name)

    def writeToMysql(self, queuePopJson):
        '''
        ...
        1 => 客户端IP告警处理
        2 => 后端IP告警处理
        3 => 用户ID告警处理
        4 => 客户端版本号告警处理
        5 => key:PeerIP+UserID+DeviceID 告警处理
        6 => 请求的url告警处理
        7 => 统计QPS情况
        8 => 统计hxff情况
        '''
        if queuePopJson.get('alarmType') == 7:
            #todo 后端机器分业务的QPS情况
            ip = queuePopJson.get('alarmName')
            serverid = queuePopJson.get('alarmServerId')
            qps = queuePopJson.get('alarmVal')
            addtime = self.getNowDatetime()
            statistics_time = queuePopJson.get('alarmDatetime')
            notes = json.dumps(queuePopJson)
            sql = "INSERT INTO `qps_statistics`(ip,serverid,qps,addtime,statistics_time, notes)\
            VALUES('%s', '%d', '%d','%s', '%s', '%s')"
            try:
                cursor = self._mysql.cursor()
                cursor.execute(sql % (ip, serverid, qps, addtime, statistics_time, notes))
                cursor.close()
                self._mysql.commit()
            except MySQLdb.Error,e:
                self._logger.error(str(e.args[0]) + str(e.args[1]))
        else:
            #todo 写入嫌疑业务的情况
            sql = "INSERT INTO `tm_storm_statistics`(alarmName,alarmType,alarmVal, alarmNotes, \
            alarmStatisticsDatetime, addtime, serverId) VALUES('%s','%d','%d','%s', '%s', '%s', '%d')"
            cursor = self._mysql.cursor()
            alarmName = queuePopJson.get('alarmName')
            alarmType = int(queuePopJson.get('alarmType'))
            alarmVal = int(queuePopJson.get('alarmVal'))
            alarmNotes = json.dumps(queuePopJson)
            alarmStatisticsDatetime = self.getNowDatetime()
            if queuePopJson.get('alarmDatetime'):
                alarmStatisticsDatetime = queuePopJson.get('alarmDatetime')
            serverId = 0
            if queuePopJson.get('alarmServerId'):
                serverId = int(queuePopJson.get('alarmServerId'))
            addtime = self.getNowDatetime()
            try:
                cursor.execute(sql % (alarmName, alarmType, alarmVal, alarmNotes, alarmStatisticsDatetime, addtime, serverId))
                cursor.close()
                self._mysql.commit()
            except MySQLdb.Error,e:
                self._logger.error(str(e.args[0]) + str(e.args[1]))
