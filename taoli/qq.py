import time

import winsound

import Ashare
import datetime
import threading
from apps.option_data import *
from pywebio import *
import socket   
qq_xh_list = []
warmming = False
lock = threading.Semaphore(1)
def sound_cancel():
    global warmming
    while True:
        if warmming:
            input()
            warmming = False
            time.sleep(0.1)
def sound():
    threading.Thread(target=sound_cancel).start()
    global warmming
    while(True):
        if warmming:
            winsound.Beep(1000, 500)

def read_list():
    global qq_xh_list

    f = open("list.txt")
    lines = f.readlines()
    for i in range(0, len(lines)):
        l = lines[i].split(',')
        try:
            xh_code,xh_des,xh_num,xh_price,qq_code,qq_des,qq_num,qq_price,warm_num = l[0].strip(),l[1].strip(),float(l[2].strip()),float(l[3].strip()),l[4].strip(),l[5].strip(),float(l[6].strip()),float(l[7].strip()),float(l[8].strip())
            dic_t = {"qq_code":qq_code,"qq_num":qq_num,"xh_code":xh_code,"xh_num":xh_num,"warm_num":warm_num,'start':True,'warmed':False,'last_qq':-1,'last_xh':-1,'xh_des':xh_des,'qq_des':qq_des,'xh_price':xh_price,'qq_price':qq_price}
            print('读入，现货:',xh_code,'备注:',xh_des,'数量:',xh_num,'现货起始价格:',xh_price,'期权:',qq_code,'备注:',qq_des,'数量:',qq_num,'期权起始价格:',qq_price,'警告利润:',warm_num)
            qq_xh_list.append(dic_t)
        except BaseException as e:
            print(e)
            print("第",i,"行读取错误，数据：",l)
    f.close()

threading.Thread(target=sound).start()
def save():
    global qq_xh_list
    txt = ""
    for x in qq_xh_list:
        l = x['xh_code'] + "," + x['xh_des'] + "," + str(x['xh_num']) + "," + str(x['xh_price']) + "," + x['qq_code'] + "," + x['qq_des'] + "," + str(x['qq_num']) + "," + str(x['qq_price']) + "," + str(x['warm_num'])
        txt += l + '\n'
    try:
        f = open('list.txt',mode='w')
        f.write(txt)
        f.close()
    except:
        print('文件保存错误')
cli_list = []
def set_serve():
    try:
        s= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.bind((socket.gethostbyname(socket.gethostname()),7094))
        s.listen(1000)
        while True:
            try:
                
                conn,addr=s.accept()
                print('连接:',addr)
                global cli_list
                cli_list.append(conn)
            except:
                print('!连接用户失败')
    except:
        print('!设置服务器失败')
    
def refresh_data():
    read_list()
    err = 0
    global cli_list
    while True:
        for qx in qq_xh_list:
            try:
                time.sleep(0.1)
                close_xh = Ashare.get_price(qx['xh_code'], frequency='1m', count=1)
                close_qq = tick_option([qx['qq_code']])
                close_xh = close_xh.close.values[0]
                close_qq = float(close_qq.iloc[0, 2])
                if qx['xh_price'] == 0:
                    qx['xh_price'] = close_xh
                    save()
                if qx['qq_price'] == 0:
                    qx['qq_price'] = close_qq
                    save()
                if close_qq == 0:
                    continue
                if close_qq == qx['last_qq']  and close_xh ==qx['last_xh']:
                    err = 0
                    continue
                qx['last_qq'] = close_qq
                qx['last_xh'] = close_xh

                xh_start = qx['xh_price']
                qq_start = qx['qq_price']
                qq_num = qx['qq_num']
                xh_num = qx['xh_num']
                xh_pro = round((close_xh - xh_start) * xh_num,3)
                qq_pro = round((close_qq - qq_start) * -qq_num,3)
                sub = xh_pro + qq_pro
                txt = ''
                qx['xh_profit'],qx['qq_profit'],qx['total'] = xh_pro,qq_pro,sub
                txt += ' 现货代码:'+qx['xh_code']+' 说明:'+qx['xh_des']+' 买入数量:'+str(xh_num)+' 起始价格：'+str(xh_start)+' 最新价格:'+str(close_xh)+' 利润:'+str(xh_pro) + '\n'
                txt += ' 期权代码:'+qx['qq_code']+' 说明:'+qx['qq_des']+' 做空数量'+str(qq_num)+' 起始价格'+str(qq_start)+' 最新价格:'+str(close_qq)+' 利润:'+str(qq_pro) + '\n'
                txt += '总计:'+str(sub) + '\n'
                txt += '时间:'+datetime.datetime.now().strftime("%y-%m-%d %H:%M") + '\n'
                txt += '-----------------------------' + '\n'
                print(txt)
                for cli in cli_list:
                    try:
                        cli.sendall(bytes(txt.encode('utf-8')))
                    except BaseException as e:
                        print(e)
                err = 0

            except BaseException as e:
                err += 1
                if err >= 5:
                    warmming = True
                    print(e)
                    print('连续错误过多，请输入键盘停止报警')


threading.Thread(target=refresh_data).start()
threading.Thread(target=set_serve).start()

