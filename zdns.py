#coding:utf-8
"""
杭州御信科技有限公司
Zdns 调度工具
"""
import os
import time
import threading
import socket
from flask import Flask,request
import json

class zdns:
    def __init__(self):

        self.processing_task_list = []
        self.waiting_task_list = []
        self.finish_task_list = []
        self.current_status = 0 # 0:未运行 1:运行中
        self.check_time_interval = 5 # 检测间隔时间
        self.dict_path = "dict.txt" #字典路径
        self.domain_dict_save_path = "static/dict"
        self.result_save_path = "static/result"
        self.zdns_path = '/usr/local/go/bin/src/github.com/zmap/zdns/zdns/zdns'
        if os.path.exists(self.domain_dict_save_path) == False:
            os.mkdir(self.domain_dict_save_path)

        if os.path.exists(self.result_save_path) == False:
            os.mkdir(self.result_save_path)

        threading.Thread(target=self.check_task_list).start() # 启动任务队列检测

    def save_logs(self,type,content):
        f = open(type+'.txt','a+')
        f.write(content+'\n')
        f.close()
    def shell_exec(self, commands):
        try:
            res = os.popen(commands)
            return res.read()
        except Exception as e:
            content = "Command:\n{}\nError:\n{}\n".format(commands,str(e))
            self.save_logs("error",content)
            return False
    def set_check_time_interval(self,time_int):
        try:
            if time_int > 0:
                self.check_time_interval = time_int
                return {
                    'status':True,
                    'msg':'设置成功'
                }
            else:
                return {
                    'status':False,
                    'msg':'检测时间间隔必须大于0'
                }
        except Exception as e:
            return {
                'status': False,
                'msg': 'set_check_time_interval_except:'+str(e)
            }
    def add_task(self,domain,threads,priority):
        priority = int(priority)
        threads = int(threads)
        try:
            socket.getaddrinfo(domain, None)
        except Exception as e:
            return {
                'status': False,
                'msg': 'add_task_except:' + str(e)
            }

        try:
            if priority < 0:
                return {
                    'status': False,
                    'msg': '优先级必须大于0'
                }
            self.waiting_task_list.append({
                'domain':domain,
                'threads':threads,
                'priority':priority,
                'add_time':self.get_time(),
                'add_time_int':time.time()
            })
            return {
                    'status': True,
                    'msg': '添加成功'
                }
        except Exception as e:
            return {
                'status': False,
                'msg': 'add_task_except:'+str(e)
            }
    def generate_dict(self,domain):
        domain_dict_path = "{}/{}.txt".format(self.domain_dict_save_path,domain)
        commands = "sed 's/$/.{}/' {} > {}".format(domain,self.dict_path,domain_dict_path)
        self.shell_exec(commands)
        return domain_dict_path

    def get_universal_ip(self,domain):
        try:
            result = socket.getaddrinfo(domain, None)
            return result[0][4][0]
        except Exception as e:
            return False

    def zdns_exec(self,domain,threads):
        self.current_status = 1
        universal_ip = self.get_universal_ip(domain)
        domain_dict_path = self.generate_dict(domain)
        result_path = "{}/{}.txt".format(self.result_save_path,domain)
        if universal_ip != False:
            commands = '{} A -input-file={} --threads={} | sed -e /{}/g | grep -E "NOERROR" > {}'.format(self.zdns_path,domain_dict_path,threads,universal_ip,result_path)
        else:
            commands = '{} A -input-file={} --threads={} | grep -E "NOERROR" > {}'.format(self.zdns_path,domain_dict_path,threads,result_path)
        self.shell_exec(commands)
        self.current_status = 0
    def submit_task(self,task):
        if self.current_status == 0:
            self.waiting_task_list.remove(task)
            self.processing_task_list.append(task)
            start_time = time.time()
            self.zdns_exec(task['domain'],task['threads'])
            used_time = round(time.time() - start_time,2)
            task['used_time'] = used_time
            self.processing_task_list.remove(task)
            self.finish_task_list.append(task)
        else:
            return False
    #任务队列检测
    def check_task_list(self):
        while True:
            try:
                if self.current_status == 0 and len(self.waiting_task_list) > 0:
                    max_priority = 0
                    current_task = {}
                    for task in self.waiting_task_list:
                        if task['priority'] >= max_priority:
                            current_task = task
                    self.save_logs("log","检测到新任务：{}\n".format(current_task['domain']))
                    self.submit_task(current_task)
            except Exception as e:
                self.save_logs("error","check_task_list_except:"+str(e))
            time.sleep(self.check_time_interval)

    def delete_task(self,domain):
        count = 0
        for task in self.waiting_task_list:
            if task['domain'] == domain:
                self.waiting_task_list.remove(task)
                count += 1
        return {
            'status':True,
            'msg':'删除{}个任务'.format(count)
        }
    def getLines(self,domain):
        try:
            file_path = self.result_save_path + "/" + domain + ".txt"
            result = self.shell_exec("wc -l " + file_path)
            return result.split(" ")[0]
        except Exception as e:
            self.save_logs("error", "getLines_except:" + str(e))
            return 0
    def get_all_tasks(self):
        all_task = []

        for task in self.waiting_task_list:
            task['status'] = "等待中"
            task['lines'] = 0
            task['used_time'] = 0
            task['type'] = 0
            all_task.append(task)

        for task in self.processing_task_list:
            task['status'] = "运行中"
            task['lines'] = self.getLines(task['domain'])
            task['used_time'] = round(time.time() - task['add_time_int'],2)
            task['type'] = 1
            all_task.append(task)

        for task in self.finish_task_list:
            task['status'] = "已完成"
            task['lines'] = self.getLines(task['domain'])
            task['type'] = 2
            all_task.append(task)

        return all_task
    def get_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
app = Flask(__name__)
z = zdns()

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/waiting_list')
def waiting_list():
    return json.dumps(z.waiting_task_list)

@app.route('/processing_list')
def processing_list():
    return json.dumps(z.processing_task_list)

@app.route('/finish_list')
def finish_list():
    return json.dumps(z.finish_task_list)

@app.route('/add_task')
def add_task():
    domain = request.args.get('domain')
    threads = request.args.get('threads')
    priority = request.args.get('priority')
    return json.dumps(z.add_task(domain,threads,priority))

@app.route('/delete_task')
def delete_task():
    domain = request.args.get('domain')
    return json.dumps(z.delete_task(domain))

@app.route('/get_all_tasks')
def get_all_tasks():
    return json.dumps(z.get_all_tasks())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0' ,port=5000)