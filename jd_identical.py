# -*- coding:utf-8 -*-
"""
cron: 50 * * * *
new Env('禁用重复任务');
"""

import json
import logging
import os
import sys
import time
import traceback

import requests

logger = logging.getLogger(name=None)  # 创建一个日志对象
logging.Formatter("%(message)s")  # 日志内容格式化
logger.setLevel(logging.INFO)  # 设置日志等级
logger.addHandler(logging.StreamHandler())  # 添加控制台日志
# logger.addHandler(logging.FileHandler(filename="text.log", mode="w"))  # 添加文件日志


ipport = os.getenv("IPPORT")
if not ipport:
    logger.info(
        "如果报错请在环境变量中添加你的真实 IP:端口\n名称：IPPORT\t值：127.0.0.1:5700\n或在 config.sh 中添加 export IPPORT='127.0.0.1:5700'"
    )
    ipport = "localhost:5700"
else:
    ipport = ipport.lstrip("http://").rstrip("/")
<<<<<<< HEAD
sub_str = os.getenv("RES_SUB", "okyyds_yydspure_master")
=======
sub_str = os.getenv("RES_SUB", "okyyds_yyds_master")
>>>>>>> 14d284972ef567f9bdf1469c72cee448a3c008ed
sub_list = sub_str.split("&")
res_only = os.getenv("RES_ONLY", True)
headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
}


def load_send() -> None:
    logger.info("加载推送功能中...")
    global send
    send = None
    cur_path = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(cur_path)
    if os.path.exists(cur_path + "/notify.py"):
        try:
            from notify import send
        except Exception:
            send = None
            logger.info(f"❌加载通知服务失败!!!\n{traceback.format_exc()}")


def get_tasklist() -> list:
    tasklist = []
    t = round(time.time() * 1000)
    url = f"http://{ipport}/api/crons?searchValue=&t={t}"
    response = requests.get(url=url, headers=headers)
    datas = json.loads(response.content.decode("utf-8"))
    if datas.get("code") == 200:
        tasklist = datas.get("data")
    return tasklist


def filter_res_sub(tasklist: list) -> tuple:
    filter_list = []
    res_list = []
    for task in tasklist:
        for sub in sub_list:
            if task.get("command").find(sub) == -1:
                flag = False
            else:
                flag = True
                break
        if flag:
            res_list.append(task)
        else:
            filter_list.append(task)
    return filter_list, res_list


def get_index(lst: list, item: str) -> list:
    return [index for (index, value) in enumerate(lst) if value == item]


def get_duplicate_list(tasklist: list) -> tuple:
    logger.info("\n=== 第一轮初筛开始 ===")

    ids = []
    names = []
    cmds = []
    for task in tasklist:
        ids.append(task.get("_id"))
        names.append(task.get("name"))
        cmds.append(task.get("command"))

    name_list = []
    for i, name in enumerate(names):
        if name not in name_list:
            name_list.append(name)

    tem_tasks = []
    tem_ids = []
    dup_ids = []
    for name2 in name_list:
        name_index = get_index(names, name2)
        for i in range(len(name_index)):
            if i == 0:
                logger.info(f"【✅保留】{cmds[name_index[0]]}")
                tem_tasks.append(tasklist[name_index[0]])
                tem_ids.append(ids[name_index[0]])
            else:
                logger.info(f"【🚫禁用】{cmds[name_index[i]]}")
                dup_ids.append(ids[name_index[i]])
        logger.info("")

    logger.info("=== 第一轮初筛结束 ===")

    return tem_ids, tem_tasks, dup_ids


def reserve_task_only(
    tem_ids: list, tem_tasks: list, dup_ids: list, res_list: list
) -> list:
    if len(tem_ids) == 0:
        return tem_ids

    logger.info("\n=== 最终筛选开始 ===")
    task3 = None
    for task1 in tem_tasks:
        for task2 in res_list:
            if task1.get("name") == task2.get("name"):
                dup_ids.append(task1.get("_id"))
                logger.info(f"【✅保留】{task2.get('command')}")
                task3 = task1
        if task3:
            logger.info(f"【🚫禁用】{task3.get('command')}\n")
            task3 = None
    logger.info("=== 最终筛选结束 ===")
    return dup_ids


def disable_duplicate_tasks(ids: list) -> None:
    t = round(time.time() * 1000)
    url = f"http://{ipport}/api/crons/disable?t={t}"
    data = json.dumps(ids)
    headers["Content-Type"] = "application/json;charset=UTF-8"
    response = requests.put(url=url, headers=headers, data=data)
    datas = json.loads(response.content.decode("utf-8"))
    if datas.get("code") != 200:
        logger.info(f"❌出错!!!错误信息为：{datas}")
    else:
        logger.info("🎉成功禁用重复任务~")


def get_token() -> str or None:
    try:
        with open("/ql/config/auth.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        logger.info(f"❌无法获取 token!!!\n{traceback.format_exc()}")
        send("💔禁用重复任务失败", "无法获取 token!!!")
        exit(1)
    return data.get("token")


if __name__ == "__main__":
    logger.info("===> 禁用重复任务开始 <===")
    load_send()
    token = get_token()
    headers["Authorization"] = f"Bearer {token}"

    # 获取过滤后的任务列表
    sub_str = "\n".join(sub_list)
    logger.info(f"\n=== 你选择过滤的任务前缀为 ===\n{sub_str}")
    tasklist = get_tasklist()
    if len(tasklist) == 0:
        logger.info("❌无法获取 tasklist!!!")
        exit(1)
    filter_list, res_list = filter_res_sub(tasklist)

    tem_ids, tem_tasks, dup_ids = get_duplicate_list(filter_list)
    # 是否在重复任务中只保留设置的前缀
    if res_only:
        ids = reserve_task_only(tem_ids, tem_tasks, dup_ids, res_list)
    else:
        ids = dup_ids
        logger.info("你选择保留除了设置的前缀以外的其他任务")

    sum = f"所有任务数量为：{len(tasklist)}"
    filter = f"过滤的任务数量为：{len(res_list)}"
    disable = f"禁用的任务数量为：{len(ids)}"
    logging.info("\n=== 禁用数量统计 ===\n" + sum + "\n" + filter + "\n" + disable)

    if len(ids) == 0:
        logger.info("😁没有重复任务~")
    else:
        disable_duplicate_tasks(ids)
    if send:
        send("💖禁用重复任务成功", f"\n{sum}\n{filter}\n{disable}")
