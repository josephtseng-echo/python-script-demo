#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
'''
处理
队列数据
'''

'''
product 为生成环境配置
test 为测试环境配置
'''
_config_set = 'test'

from todo import Todo
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "参数有错，如：'python2.7 main.py test'测试环境 或 'python2.7 main.py product'生产环境"
        sys.exit(0)
    _config_set = str(sys.argv[1].lower())
    todo = Todo(_config_set)    
    print "todo start ", todo.getNowDatetime(), ""
    todo.alarm()
    print "todo end   ", todo.getNowDatetime(), "\n"
