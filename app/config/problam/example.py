import sys
from datetime import datetime
from PyQt5.QtCore import pyqtSignal
import sqlite3
import sys
from app.plugins.MeterTask import MeterTask

def check_exec_plan(param, singal:pyqtSignal):
    path, point, item = param
    conn = sqlite3.connect(f'{path}/readmeter.db')
    cursor = conn.cursor()
    sql = f'select b.acq_set, a.task_id, a.exec_cycle, a.exec_cycle_unit from meter_task as a, meter_ex_project as b where a.task_id in (select task_id from task_status_mask where meter_id={point}) and a.task_id=b.plan_id ORDER by a.priority;'
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        meter = MeterTask()
        if meter.check_item_is_in_plan(row[0], item):
            task_id = row[1]
            exec_cycle = row[2]
            exec_cycle_unit = row[3]
            # singal.emit({"执行步骤":"检查已经存在的任务", "执行结果":"找到任务:"+str(task_id)+str(exec_cycle) + str(exec_cycle_unit), "时间":f"{datetime.now()}"})
            return {"state":True, "result": True, "uiinfo":{"执行步骤":"检查已经存在的任务", "执行结果":f"找到任务:任务号{task_id}, 执行周期{exec_cycle}, 执行周期单位{exec_cycle_unit}", "时间":f"{datetime.now()}"}}
    return {"state":True, "result":False, "uiinfo":{"执行步骤":"检查已经存在的任务", "执行结果":"未找到任务", "时间":f"{datetime.now()}"}}

# def check_data(param):


def add_function(a,b):
    print("add_function")
    return a+b
def function1():
    print("function1")
    return {"state":True, "result":(3,5), "uiinfo":{"执行步骤":"function1", "执行结果":"成功", "时间":f"{datetime.now()}"}}
def function2(c, singal:pyqtSignal):
    print("function2 param c:",c)
    a, b = c
    print(c)
    print(sys.path)
    x = 4 + add_function(a,b)
    singal.emit({"执行步骤":"function2发送信号", "执行结果":"成功", "失败原因":"无", "时间":f"{datetime.now()}"})
    return {"state":True, "result":x, "uiinfo":{"执行步骤":"function2", "执行结果":"成功",  "时间":f"{datetime.now()}"}}
     

def function3(c):
    print("function2 param c:",c)
    a, b = c
    print(c)
    print(sys.path)
    x = 4 + add_function(a,b)
    return {"state":True, "result":x, "uiinfo":{"执行步骤":"function3", "执行结果":"成功", "失败原因":"无", "时间":f"{datetime.now()}"}}