#!/usr/bin/python3.6
# -*- coding:utf-8 -*-

import re
import requests
import json
import urllib
import urllib.request
import time
import datetime

# 发起查询
# 定制时间: start: 08:00:00  ;end: 18:00:00 ; step: 1h
#需要对这两个时间做 -8小时的处理
dtime_today = datetime.datetime.now()
dtime_yesterday = dtime_today - datetime.timedelta(days=1)
dtime_today=dtime_today - datetime.timedelta(hours=8)
dtime_today_str = dtime_today.strftime('%Y-%m-%dT%H:%M:%S')
dtime_today_str = dtime_today_str + ".781Z"
#print(dtime_today_str)

dtime_yesterday = dtime_yesterday - datetime.timedelta(hours=8)
dtime_yesterday_str = dtime_yesterday.strftime('%Y-%m-%dT%H:%M:%S')
dtime_yesterday_str = dtime_yesterday_str + ".781Z"

stepTime = "1h"
# 过去24小时

startTime = dtime_yesterday_str
endTime = dtime_today_str
#print(startTime)
#print(endTime)

url = "http://152.136.179.134:9090/api/v1/query"
url_range = "http://152.136.179.134:9090/api/v1/query_range"
params1 = {
    "query": "sum((1 - avg(irate(node_cpu_seconds_total{job=~'node-exporter',mode='idle'}[5m])) by(instance)) * 100 )/count(up{job='node-exporter'}==1)"
}
params_Mem = {
    "query": "(sum(node_memory_MemTotal_bytes{} - node_memory_MemAvailable_bytes{}) / sum(node_memory_MemTotal_bytes{}))*100"
}

params_MemRange = {
    "query": "(sum(node_memory_MemTotal_bytes{} - node_memory_MemAvailable_bytes{}) / sum(node_memory_MemTotal_bytes{}))*100",
    "start": startTime,
    "end": endTime,
    "step": stepTime
}
params_CPURange = {
    "query": "sum((1 - avg(irate(node_cpu_seconds_total{job=~'node-exporter',mode='idle'}[5m])) by(instance)) * 100 )/count(up{job='node-exporter'}==1)",
    "start": startTime,
    "end": endTime,
    "step": stepTime

}
params_IB = {
    "query": "avg( irate(node_infiniband_port_data_transmitted_bytes_total[5m])*8)+avg(irate(node_infiniband_port_data_received_bytes_total [5m])*8)"
}
params_IO = {
    "query": "sum(node_disk_writes_completed_total{job='node-exporter'}+node_disk_reads_completed_total{job='node-exporter'})"
}

res_CPU = requests.get(url=url, params=params1)

res_Mem = requests.get(url=url, params=params_Mem)

res_MemRange = requests.get(url=url_range, params=params_MemRange)

res_CPURange = requests.get(url=url_range, params=params_CPURange)

res_IB = requests.get(url=url, params=params_IB)

res_IO = requests.get(url=url, params=params_IO)
# 获取json
data_CPU = res_CPU.json()
data_Mem = res_Mem.json()
data_MemRange = res_MemRange.json()
data_CPURange = res_CPURange.json()
data_IB = res_IB.json()
data_IO = res_IO.json()


# 处理范围查询数据，返回key为{"date","value"}的字典
# 如{'2020-07-24 11:00:00': 1.89, '2020-07-24 11:30:00': 3.29, '2020-07-24 12:00:00': 3.49, '2020-07-24 12:30:00': 3.51, '2020-07-24 13:00:00': 3.42}
def dataProcess(dataDict):
    # print("dataList: ",dataDict['data']['result'][0]['values'])
    if (dataDict['data']['result']):
        dataList = dataDict['data']['result'][0]['values']
        dataTotal = {}
        for i in range(len(dataList)):
            # 数据保留2位小数
            val = round(float(dataList[i][1]), 2)
            # 处理时间，把时间戳转为真实时间
            unix_ts = str(dataList[i][0])
            # 去掉末尾的.781,这个是请求参数的格式
            unix_ts = re.sub('.781', '', unix_ts)
            localtime = datetime.datetime.fromtimestamp(int(unix_ts))
            localtime = str(localtime)
            dataTotal[localtime] = val
            # print(localtime,": ",val)

    else:
        print("[INFO]Time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), "没有数据")
        return
    return dataTotal


dataMemTotal = dataProcess(data_MemRange)
# print(dataMemTotal)
# 最高/最低内存使用率
max_memory_percent = max(zip(dataMemTotal.values(), dataMemTotal.keys()))
min_memory_percent = min(zip(dataMemTotal.values(), dataMemTotal.keys()))

dataCPUTotal = dataProcess(data_CPURange)
# print(dataCPUTotal)
# 最高/最低集群CPU使用率
max_cpu_percent = max(zip(dataCPUTotal.values(), dataCPUTotal.keys()))
min_cpu_percent = min(zip(dataCPUTotal.values(), dataCPUTotal.keys()))

# 当前内存使用率
memory_percent = float(data_Mem['data']['result'][0]['value'][1])
memory_percent = round(memory_percent, 2)

# 当前集群CPU平均使用率
cpu_percent = data_CPU['data']['result'][0]['value'][1]
cpu_percent = float(cpu_percent)
cpu_percent = round(cpu_percent, 2)

# IB网络带宽
infiniband_bandwidth = float(data_IB['data']['result'][0]['value'][1])
infiniband_bandwidth = round(infiniband_bandwidth, 2)
# 判断单位
if (infiniband_bandwidth < 1048576):
    # KB
    infiniband_bandwidth = round(infiniband_bandwidth / 1024, 2)
    infiniband_data = str(infiniband_bandwidth) + " KB/S"
elif (infiniband_bandwidth > 1048576 and infiniband_bandwidth < 1073741824):
    # MB
    infiniband_bandwidth = round(infiniband_bandwidth / 1024 / 1024, 2)
    infiniband_data = str(infiniband_bandwidth) + " MB/S"

# IO吞吐量
io_throughput = float(data_IO['data']['result'][0]['value'][1])
io_throughput = io_throughput / 1024 / 1024
io_throughput = round(io_throughput, 2)
io_throughput_data = str(io_throughput) + " MB"

# 拼接字符串
timenow = datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S')
markdown = "=====云服务器测试(" + timenow + ")\n"
markdown += "## 今日汇总(" + timenow + ")\n"
markdown += "\n- 内存使用率: " + str(memory_percent) + " %"
markdown += "\n- 集群CPU使用率: " + str(cpu_percent) + " %"
markdown += "\n- 今日最高集群CPU使用率: " + str(max_cpu_percent[0]) + "% At-" + max_cpu_percent[1] + "."
markdown += "\n- 今日最低集群CPU使用率: " + str(min_cpu_percent[0]) + "% At-" + min_cpu_percent[1] + "."
markdown += "\n- 今日最高内存使用率: " + str(max_memory_percent[0]) + "% At-" + max_memory_percent[1] + "."
markdown += "\n- 今日最低内存使用率: " + str(min_memory_percent[0]) + "% At-" + min_memory_percent[1] + "."
markdown += "\n- IB网络带宽: " + infiniband_data + "."
markdown += "\n- IO吞吐量: " + io_throughput_data + "."

# POST发送到群里
urlPost = "https://oapi.dingtalk.com/robot/send?access_token=627c34ca398613ff446e643ff2c6581a4039dfdd8de94886d34da568f824b174"

header = {
    "Content-Type": "application/json",
    "Charset": "UTF-8"
}

dataPost = {
    "msgtype": "markdown",
    "markdown": {
        "title": "今日汇总",
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

# 最后输出，作为日志记录
print("[INFO]Time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), " CPU :", cpu_percent, "% MEM :",
      memory_percent, "% Max Mem: ", max_memory_percent, "% Min Mem: ", min_memory_percent
      , "% Max CPU: ", max_cpu_percent, "% Min CPU: ", min_cpu_percent, "% IB: ", infiniband_data, " IO: ",
      io_throughput_data)
