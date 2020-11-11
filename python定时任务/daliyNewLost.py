#!/usr/bin/python3.6
# -*- coding:utf-8 -*-
import re

import requests
import json

import urllib
import urllib.request
import time

import datetime

# 每日新增: 发起两次请求，得到两个响应res1,res2;res1是当天的,res2是前一天的,拿出两组数据做对比
# 如果res2中值为0,res1中值为1======新增===获取新增主机的ip
# 如果res2长度小于res1长度===有新增,
#                     ===res2中没有这个元素,res1中有===新增====获取主机的ip
# 把新增主机的ip放入到一个list里

# 每日失联
# 遍历res1中的数据=====对值为0的===获取其主机ip
# 把失联主机的ip放入到一个list里面

# 最后发送post请求给钉钉机器人
# 2次请求的时间要先获取当天时间

# 今日新增，设定每天18:00发信息，那就应该取昨天18:00-今天18:00的消息，那就是昨天10:00~今天10:00(UTC时间)
# 获取当前时间
dtime_today = datetime.datetime.now()
dtime_yesterday= dtime_today - datetime.timedelta(days=1)
dtime_beforeyes=dtime_today-datetime.timedelta(days=2)

dtime_today=dtime_today - datetime.timedelta(hours=8)
dtime_yesterday = dtime_yesterday - datetime.timedelta(hours=8)
dtime_today_str=dtime_today.strftime('%Y-%m-%dT%H:%M:%S')
dtime_today_str= dtime_today_str + ".781Z"
dtime_yesterday_str=dtime_yesterday.strftime('%Y-%m-%dT%H:%M:%S')
dtime_yesterday_str= dtime_yesterday_str + ".781Z"

#获取前一天时间
dtime_beforeyes=dtime_beforeyes - datetime.timedelta(hours=8)
dtime_beforeyes_str=dtime_beforeyes.strftime('%Y-%m-%dT%H:%M:%S')
dtime_beforeyes_str=dtime_beforeyes_str + ".781Z"


url = "http://152.136.179.134:9090/api/v1/query_range"
url2 = "http://152.136.179.134:9090/api/v1/query"
params1 = {"query": "up{job='node-exporter'}",
           "start": dtime_yesterday_str,
           "end": dtime_today_str,
           "step": "2h"
           }
params2 = {"query": "up{job='node-exporter'}",
           "start": dtime_beforeyes_str,
           "end": dtime_yesterday_str,
           "step": "2h"
           }
param_down = {
    "query": "up==0"
}
res1 = requests.get(url=url, params=params1)
res2 = requests.get(url=url, params=params2)

data_dict_res1 = res1.json()
data_dict_res2 = res2.json()

dataList_res1 = data_dict_res1['data']['result']
dataList_res2 = data_dict_res2['data']['result']
dataUp_res1 = {}
dataUp_res2 = {}

# 处理数据
for i in range(len(dataList_res1)):

    instance_res1 = dataList_res1[i]['metric']['instance']
    valueList_res1 = dataList_res1[i]['values']
    for j in range(len(valueList_res1)):
        unix_ts = str(valueList_res1[j][0])
        unix_ts = re.sub('.781', '', unix_ts)

        # dataUp_res1[instance_res1]=[unix_ts, valueList_res1[j][1]]
        dataUp_res1[instance_res1] = valueList_res1[j][1]

for i in range(len(dataList_res2)):

    instance_res2 = dataList_res2[i]['metric']['instance']
    valueList_res2 = dataList_res2[i]['values']
    for j in range(len(valueList_res2)):
        unix_ts = str(valueList_res2[j][0])
        unix_ts = re.sub('.781', '', unix_ts)

        dataUp_res2[instance_res2] = valueList_res2[j][1]

# 开始比较
# 先比较长度
diffList = []
#dataUp_res2是 更早的 dataUp_res1是晚一点的
if len(dataUp_res2) != len(dataUp_res1):

    # 找2个差异
    # 1.在res1中不在res2中:新增
    diff1 = dataUp_res1.keys() - dataUp_res2.keys()
    diffList = list(diff1)


else:
    # 2.res1和res2中key相等value不相等的==res2中value==0,res1中value==1
    diff2 = dataUp_res1.keys() & dataUp_res2.keys()
    diff_valab = [(k) for k in diff2 if (dataUp_res1[k] == '1') and (dataUp_res2[k] == '0')]
    diffList2 = list(diff_valab)
    diffList = diffList + diffList2

# 比较结束

# 获取今日失联主机list
downList = []
down_flag = 0


def get_key2(dct, value):
    return list(filter(lambda k: dct[k] == value, dct))


# 这里应该重新做即时查询
res_down = requests.get(url2, param_down)
dict_down = res_down.json()
data_downlist = dict_down['data']['result']
dict_downList = {}
for i in range(len(data_downlist)):
    instance = data_downlist[i]['metric']['instance']
    value = data_downlist[i]['value'][1]
    dict_downList[instance] = value

if dict_downList:
    # 不为空,这时从dict_downList获取值为0的所有键
    # 要先对data_downList做处理,{instance,value}的dict,不然就报错
    downList = get_key2(dict_downList, '0')
else:
    # 结果为空,再发起查询absent(up)
    param_absent = {
        "query": "absent(up)"
    }
    res_absent = requests.get(url2, param_absent)
    data_absent = res_absent.json()['data']['result'][0]['value'][1]
    if data_absent == "1":
        # 集群全部宕机
        down_flag = 1
    downList = []

# downList=get_key2(dataUp_res1,'0')


# post发送出去

if diffList:
    diffData = diffList
else:
    diffData = "无"

downData = ','.join(downList)

timenow = datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S')
markdown = "## 今日新增/失联(" + timenow + ")\n"

markdown += "\n### 今日新增:"
if diffList:
    for i in range(len(diffList)):
        markdown += "\n- *" + str(diffList[i]) + "* "
else:
    # 为空输出‘无'
    markdown += "\n- *" + "无*"

markdown += "\n### 今日失联(node-exporter):"
if down_flag == 1:
    markdown += "\n- *" + "集群全部宕机*"
elif downList:
    for i in range(len(downList)):
        markdown += "\n- *" + str(downList[i]) + "* "
else:
    # 为空输出‘无'
    markdown += "\n- *" + "无*"

urlPost = "https://oapi.dingtalk.com/robot/send?access_token=627c34ca398613ff446e643ff2c6581a4039dfdd8de94886d34da568f824b174"

header = {
    "Content-Type": "application/json",
    "Charset": "UTF-8"
}

dataPost = {
    "msgtype": "markdown",
    "markdown": {
        "title": "今日新增",
        "text": markdown
    },
    "at": {
        "isAtAll": False
    }
}

# 对请求的数据进行json封装
sendData = json.dumps(dataPost)
sendData = sendData.encode("utf-8")

# 发送请求
request = urllib.request.Request(url=urlPost, data=sendData, headers=header)
# 将请求发回的数据构建成为文件格式
opener = urllib.request.urlopen(request)

# 作为log
print("[INFO]Time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), "今日新增主机IP: ", diffList,
      " 今日失联主机: ", downList)
