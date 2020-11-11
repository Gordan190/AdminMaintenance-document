import datetime
import json

import requests

dtime_today = datetime.datetime.now()
dtime_today=dtime_today - datetime.timedelta(hours=8)
dtime_today_str=dtime_today.strftime('%Y-%m-%dT%H:%M:%S')
dtime_today_str= dtime_today_str + ".781Z"
print(dtime_today_str)

url = "http://152.136.179.134:9090/api/v1/query"

param_up_early={
    "query": "up==1",
    "time": dtime_today_str
}
res_early = requests.get(url=url, params=param_up_early)
dict_res_early=res_early.json()
list_res_early=dict_res_early['data']['result']
data_UpEarly={}

if list_res_early:
    for i in range(len(list_res_early)):
        instance=list_res_early[i]['metric']['instance']
        job=list_res_early[i]['metric']['job']
        #print("instance ",instance,"job ",job)
        data_UpEarly[instance]=job

with open('dataUp.json','w') as file: 
    json.dump(data_UpEarly, file)   
    file.close()  
