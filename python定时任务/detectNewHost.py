#!/usr/bin/python3.6
# -*- coding:utf-8 -*-
import datetime
#监测每天一早的up==1的所有元组，然后每5分钟请求一次,跟之前的做比较
import time
import urllib
import requests
import json

url = "http://152.136.179.134:9090/api/v1/query"

param_up = {
    "query": "up==1"
}

res_now = requests.get(url=url, params=param_up)


dict_now=res_now.json()


#print(dict_now)


list_res_now=dict_now['data']['result']


data_UpNow={}
#处理 list_res_now
if list_res_now:
    for i in range(len(list_res_now)):
        instance=list_res_now[i]['metric']['instance']
        job=list_res_now[i]['metric']['job']
        #print("instance ", instance, "job ", job)
        data_UpNow[instance] = job

with open('dataUp.json','r') as fileR:   #打开文本读取状态
    data_UpEarly = json.load(fileR)  #解析读到的文本内容 转为python数据 以一个变量接收
    fileR.close()  #关闭文件

#print(data_UpEarly)
#print(data_UpNow)

#比较两个dict 如果data_UpNow比data_UpEarly有多出的key就post
diffList = []
# 1.在 data_UpNow 中不在 data_UpEarly 中:新增
diff1 = data_UpNow.keys() - data_UpEarly.keys()
diffList = list(diff1)

if diffList :
    #非空
    # 先持久化到JSON文件
    with open('dataUp.json', 'w') as file:  # test.json文本，只能写入状态 如果没有就创建
        json.dump(data_UpNow, file)  # data_UpEarly转换为json数据格式并写入文件
        file.close()  # 关闭文件
    # 不为空,发送主机
    timenow = datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S')
    markdown = "## 主机上线(" + timenow + ")\n"
    markdown += "\n### 主机上线:"
    if diffList:
        for i in range(len(diffList)):
            markdown += "\n- *" + str(diffList[i]) + "* "
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
            "title": "主机上线",
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
    print("[INFO]Time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), "主机突然上线: ", diffList)
else:
    print("[INFO]Time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),"无新增主机，不发送消息")