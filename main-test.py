from machine import Pin,SoftSPI,PWM,Timer,RTC
import time,json,ntptime,tm1637,urequests
nao_zhong_zhuang_tai = 1

'''
#另一种微信小程序配网
from mpycon import mpyconnect
con = mpyconnect()
con.connect()
'''

#直接根据wifi_config.json里面的essid和password的值连接网络
do_connect()

rtc = RTC()
ntptime.NTP_DELTA = 3155644800   #设置时区+8
ntptime.host = 'ntp1.aliyun.com'

#tm1637使用的引脚初始化
tm = tm1637.TM1637(clk=Pin(4), dio=Pin(5))

#小时和分钟之间的时钟冒号":",和左起第二个数码管绑定，| 0x80 显示':',否则不显示
Dot  = 0x80

#显示SEG8Code[0]-SEG8Code[15]分别表示显示0-F，最后一个SEG8Code[16]=0x00表示不显示
SEG8Code = [
    0x3F, # 0
    0x06, # 1
    0x5B, # 2
    0x4F, # 3
    0x66, # 4
    0x6D, # 5
    0x7D, # 6
    0x07, # 7
    0x7F, # 8
    0x6F, # 9
    0x77, # A  10
    0x7C, # b  11
    0x39, # C  12
    0x5E, # d  13
    0x79, # E  14
    0x71, # F  15
    0x00, # off 16
    0x5c,#o  17
    0x37,#n  18
    
    ]

# all LEDS on "88:88"
#tm.write([SEG8Code[7], SEG8Code[7] | Dot , SEG8Code[7] , SEG8Code[7] , SEG8Code[7] , SEG8Code[7] ])

#设置key1和key2分别为0脚和2脚，上拉输入，默认高电平1，按下为低电平0，松开为高电平1
key1 = Pin(0, Pin.IN, Pin.PULL_UP) 
key2 = Pin(2, Pin.IN, Pin.PULL_UP)     

#设置16脚为工作闪烁灯的引脚，默认输出脚，根据电平变化闪烁工作灯，夜间不闪烁
workled = Pin(16, Pin.OUT)
workled.value(0)

#key1和key2的按键去抖动
key1_debounce = 0
key2_debounce = 0

#key1和key2的按键模式
key1_mode = 0   #key1_mode:0：显示实时时间 1：显示年月日  2：显示闹钟  3：设置闹钟hour 4：设置闹钟min 5：计时器
key2_mode = 0   #在key1_mode==5的时候，key2_mode:0：清零 1：开始计时 2：停止计时
                #在key1_mode==0的时候，key2用于关闭闹钟
                #在key1_mode==3的时候，key2用于修改闹钟的小时值
                #在key1_mode==4的时候，key2用于修改闹钟的分钟值

buzzer = Pin(15, Pin.OUT) #buzzer是蜂鸣器引脚，输出模式 默认输出0，低电平，蜂鸣器不响
buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
time.sleep(0.01)
buzzer.value(0)






updatetimecount=0
#secondcount=0

timehasok = False
#timehasoknext = False
def myntpsettime():
    global timehasok 
    #label .retry
    try:
        ntptime.settime()
        timehasok =True
        #timehasoknext =True
        
    except:
        #updatetimecount =0
        timehasok =False
        #timehasoknext = False
    print("NTP同步是否成功:",timehasok)
    return timehasok
        
    



hour=0
minute=0
second=0
alarm_hour = 0
alarm_min = 0
#updatetime=1*60*60*24 #一天
#updatetime=1*60*60*8 #8小时
#updatetime=1*60*60*4 #4小时
updatetime=1*60*60 #一小时
#updatetime=1*60 #一分钟
#updatetime=1*30 #30秒
#updatetime=1*10 #10秒
import network
wifi = network.WLAN(network.STA_IF)
week_list=['星期一','星期二','星期三','星期四','星期五','星期六','星期日']

iftimesync=False
timer100mscount = 0
alarm_on = False

count_hour = 0
count_min  = 0
count_sec  = 0
ifcount=False
def timecallback(t):
    global count_hour,count_min,count_sec,ifcount
    global hour
    global minute,second
    global week
    global year,month,day
    global Dot
    global updatetimecount,iftimesync
    global timer100mscount
    global key1_mode,key1_debounce,key2_mode,key2_debounce
    global alarm_hour,alarm_min,alarm_on
    global nao_zhong_zhuang_tai
    
    #key1_mode:0：显示实时时间 1：显示年月日  2：显示闹钟  3：设置闹钟hour 4：设置闹钟min 5：计时器
    if key1_mode == 0:
        #print(key1_mode)
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 1       
                key1_debounce = 0
                
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
                #print(key1_mode)
        if alarm_on == True :
            if key2.value() == 0:
                key2_debounce = key2_debounce +1
            if key2_debounce >1 :
                if key2.value() ==1:
                    alarm_on = False
                    key2_debounce = 0
                    buzzer.value(0)
    
    #key1_mode:1：显示年月日
    elif key1_mode == 1:
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 2       
                key1_debounce = 0
                #print(key1_mode)
                
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
    #key1_mode:2：显示闹钟           
    elif key1_mode == 2:
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 3       #设置闹钟hour
                key1_debounce = 0
                #print(key1_mode)
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
        if nao_zhong_zhuang_tai == 0:
            if key2.value() == 0:
                key2_debounce = key2_debounce +1
            if key2_debounce >1 :
                if key2.value() ==1:
                    buzzer.value(1)
                    time.sleep(0.01)
                    buzzer.value(0)
                    key2_debounce =0
                    nao_zhong_zhuang_tai = 1
                    #print(nao_zhong_zhuang_tai)
        else:
            if key2.value() == 0:
                key2_debounce = key2_debounce +1
            if key2_debounce >1 :
                if key2.value() ==1:
                    buzzer.value(1)
                    time.sleep(0.01)
                    buzzer.value(0)
                    key2_debounce =0
                    nao_zhong_zhuang_tai = 0
        print(nao_zhong_zhuang_tai)
        '''            
        if key2.value() == 1:
            buzzer.value(1)
            time.sleep(0.01)
            buzzer.value(0)
            nao_zhong_zhuang_tai = 2'''
                
                
                
        
    #key1_mode:3：设置闹钟hour             
    elif key1_mode == 3:
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 4       #设置闹钟min
                key1_debounce = 0
                #print(key1_mode)
                
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
        if key2.value() == 0:
            key2_debounce = key2_debounce +1
        if key2_debounce >1 :
            if key2.value() ==1:
                if alarm_hour < 24:
                    key2_debounce=0
                    alarm_hour = alarm_hour +1
                    if alarm_hour == 24 :
                        alarm_hour =0
                    
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                        
    #key1_mode:4：设置闹钟min 
    elif key1_mode == 4:
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 5       #计时
                key1_debounce = 0
                #print(key1_mode)
            
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
        if key2.value() == 0:
            key2_debounce = key2_debounce +1
        if key2_debounce >1 :
            if key2.value() ==1:
                if alarm_min < 60:
                    key2_debounce=0
                    alarm_min = alarm_min +1
                    if alarm_min == 60 :
                        alarm_min =0
                
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                        
                        
    #key1_mode:5：计时器                    
    elif key1_mode == 5:
        if key1.value() == 0:
            key1_debounce = key1_debounce + 1
        if key1_debounce > 1 :
            if key1.value() == 1:
                key1_mode = 0       #显示模式
                key1_debounce = 0
                #print(key1_mode)
                
                buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                time.sleep(0.01)
                buzzer.value(0)
                
        if key2_mode == 0:   
            if key2.value() == 0:
                key2_debounce = key2_debounce + 1
            if key2_debounce > 1 :
                if key2.value() == 1:
                    key2_mode = 1       #计时模式
                    ifcount = 1
                    key2_debounce = 0
                    #print(key2_mode)
                
                    buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                    time.sleep(0.01)
                    buzzer.value(0)
                
        elif key2_mode == 1:   
            if key2.value() == 0:
                key2_debounce = key2_debounce + 1
            if key2_debounce > 1 :
                if key2.value() == 1:
                    key2_mode = 2       #停止计时
                    ifcount = 0
                    key2_debounce = 0
                    #print(key2_mode)
                
                    buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                    time.sleep(0.01)
                    buzzer.value(0)
                
        elif key2_mode == 2:   
            if key2.value() == 0:
                key2_debounce = key2_debounce + 1
            if key2_debounce > 1 :
                if key2.value() == 1:
                    key2_mode = 0       #停止计时
                    ifcounter = 0
                    count_hour = 0
                    count_min  = 0
                    count_sec  = 0
                    key2_debounce = 0
                    #print(key2_mode)
                
                    buzzer.value(1)  #buzzer脚输出值设置为1，高电平，蜂鸣器响
                    time.sleep(0.01)
                    buzzer.value(0)
                
        #print(ifcount,key2_mode)
        
    if timer100mscount < 9 :  #定时器累计0-9共10个100毫秒
        timer100mscount=timer100mscount+1
        #print(timer100mscount)                
    elif timer100mscount ==9:  #10个100ms等于1秒       
        timer100mscount=0
        
        #if key1_mode == 5:
        #计数器ifcount为真开始计数时，每秒加1
        if ifcount == 1:
            if count_sec < 59:
                count_sec = count_sec + 1
            else:
                count_sec = 0
                if count_min < 59 :
                    count_min = count_min + 1
                else:
                    count_min = 0
                    if count_hour < 23 :
                        count_hour = count_hour+1
                    else:
                        count_hour = 0
        
        #每秒获取一次RTC时间
        realdatetime = rtc.datetime()
        #print(realdatetime)    
        year   = realdatetime[0]
        month  = realdatetime[1]
        #print("%02d" % month)
        day    = realdatetime[2]
        week   = realdatetime[3]
        hour   = realdatetime[4]    
        minute = realdatetime[5]    
        second = realdatetime[6]    
        '''
        #格式化为两个字符，不足补0
        month2 = str("{0:0=2d}".format(month))
        day2   = str("{0:0=2d}".format(day))
        hour2  = str("{0:0=2d}".format(hour))
        minute2= str("{0:0=2d}".format(minute))
        second2= str("{0:0=2d}".format(second))    
        datestr= str(year)+'-'+str(month2)+'-'+str(day2)
        timestr= str(hour2)+':'+str(minute2)+':'+str(second2)
        datetimestr =datestr +' '+timestr+' '+str(week_list[week])    
        print(datetimestr)
        '''
        if (iftimesync!=True):
            iftimesync=myntpsettime() #如果首次ntp更新时间没成功，接着每秒一次更新时间
        else:   
            
            Dot = Dot ^ 0x80 #首次ntp更新时间成功后，时钟符号每秒闪烁 
            
            if updatetimecount < updatetime:
                updatetimecount = updatetimecount + 1      #updatetimecount为定时ntp更新时间的计数，根据上面的updatetime定义可以调整ntp更新时间的周期
    
        
    
    
#定时器，100ms调用timecallback
tim = Timer(-1)
tim.init(period=100,callback=timecallback)


line = 0x40 #共阳  #line为数码管中间显示横线



if __name__=='__main__':
    #tmp_secend=0
    workledvalue = 1   #为1的时候，左边的红色灯亮
    Dot  = 0x80        #Dot是小时和分钟之间的冒号，和左起第二个数码管绑定，或上0x80，冒号就亮，或上0x00就不亮 Dot = Dot ^ 0x80，实际就是一次为0x80，一次为0x00，依次交替
    tm.write([line, line | Dot , line , line , line , line])  #上电显示--:-- --
    
    #以下获取闹钟时间，闹钟时间掉电保存在内部存储空间中的json文件里，修改闹钟时间自动保存
    alarm_hour_num = 0
    alarm_min_num= 0
    try:
        with open('alarm_config.json','r') as f:
            config = json.loads(f.read())
    # 若初次运行,则将进入excpet,执行配置文件的创建        
    except:
        #alarm_hour_num = str(alarm_hour) # 
        #alarm_min_num = str(alarm_min) #
        alarm_hour_num = alarm_hour # 
        alarm_min_num = alarm_min # 
        config = dict(alarm_hour_num=alarm_hour_num, alarm_min_num=alarm_min_num) # 创建字典
        with open('alarm_config.json','w') as f:
            f.write(json.dumps(config)) # 将字典序列化为json字符串,存入wifi_config.json
    
    #alarm_hour = int(config['alarm_hour_num'])
    #alarm_min =int (config['alarm_min_num'])
    alarm_hour_get = (config['alarm_hour_num'])
    alarm_min_get = (config['alarm_min_num'])
    
    #将获取的闹钟时间赋值给alarm_hour和alarm_min,用于判定是否到达闹钟响铃时间，如果到达，则蜂鸣器鸣叫，可以使用key2关闭闹钟
    alarm_hour,alarm_min = alarm_hour_get,alarm_min_get
    
    while(1):
        if iftimesync == True:  #所有显示在首次ntp时间更新完成后显示，否则显示--:-- --
            
            #在修改了闹钟时间后，alarm_hour和alarm_min变化了，就不等于从内部存储空间获取到的闹钟值，此处更新闹钟时间，并保存到内部存储空间
            
            if alarm_hour_get != alarm_hour or alarm_min_get != alarm_min:
                alarm_hour_get,alarm_min_get = alarm_hour,alarm_min
                
                alarm_hour_num = alarm_hour_get # 
                alarm_min_num = alarm_min_get # 
                config = dict(alarm_hour_num=alarm_hour_num, alarm_min_num=alarm_min_num) # 创建字典
                with open('alarm_config.json','w') as f:
                    f.write(json.dumps(config)) 
                
            #如果当前时间和闹钟时间相同，则开启蜂鸣器，可以使用key2键关闭
            if nao_zhong_zhuang_tai == 1:
                if hour==alarm_hour and minute==alarm_min and (second >=0 and second <2):
                    alarm_on = True
                    buzzer.value(1)
                
            #key1_mode:0：显示实时时间
            if key1_mode == 0:
                tm.write([SEG8Code[hour//10], SEG8Code[hour%10] | Dot , SEG8Code[minute//10] , SEG8Code[minute%10] , SEG8Code[second//10] , SEG8Code[second%10]])
                #print(year%100)
                print('当前时间：',hour,':',minute,':',second)
                
            #key1_mode:1：显示年月日
            elif key1_mode == 1:
                tm.write([SEG8Code[month//10] , SEG8Code[month%10] , SEG8Code[day//10] , SEG8Code[day%10], SEG8Code[(year%100)//10], SEG8Code[(year%100)%10]])
                print('当前日期：',year,'-',month,'-',day)
                
            #key1_mode:2：显示闹钟 
            elif key1_mode == 2:
                if nao_zhong_zhuang_tai == 1:
                    tm.write([SEG8Code[alarm_hour//10], SEG8Code[alarm_hour%10] | 0x80 , SEG8Code[alarm_min//10] , SEG8Code[alarm_min%10] , SEG8Code[17] , SEG8Code[15]]) #尾灯显示mode2
                    #print(alarm_hour,alarm_min)
                else:
                    tm.write([SEG8Code[alarm_hour//10], SEG8Code[alarm_hour%10] | 0x80 , SEG8Code[alarm_min//10] , SEG8Code[alarm_min%10] , SEG8Code[17] , SEG8Code[18]]) #尾灯显示mode2
                    #print(alarm_hour,alarm_min)
                print('闹钟时间：',alarm_hour,':',alarm_min)
                
            #key1_mode:3：设置闹钟hour
            elif key1_mode == 3:
                tm.write([SEG8Code[alarm_hour//10], SEG8Code[alarm_hour%10] | 0x80, SEG8Code[16] , SEG8Code[16] , SEG8Code[16] , SEG8Code[16]]) #尾灯显示mode3
                #print(alarm_hour,alarm_min)
                print('设置闹钟小时：',alarm_hour)
                
                
            #key1_mode:4：设置闹钟min 
            elif key1_mode == 4:
                tm.write([SEG8Code[16], SEG8Code[16] | 0x80, SEG8Code[alarm_min//10] , SEG8Code[alarm_min%10] , SEG8Code[16] , SEG8Code[16]]) #尾灯显示mode4
                #print(alarm_hour,alarm_min)
                print('设置闹钟分钟：',alarm_min)
                
                
            #key1_mode:5：计时器
            elif key1_mode == 5:
                tm.write([SEG8Code[count_hour//10], SEG8Code[count_hour%10] | 0x80, SEG8Code[count_min//10] , SEG8Code[count_min%10] , SEG8Code[count_sec//10] , SEG8Code[count_sec%10]])    
                print('当前计数时间：',count_hour,':',count_min,':',count_sec)    
                    
            #print(key1_mode)
            
            #当到达ntp更新时间，从网络更新一次ntp时间
            if updatetimecount == updatetime:
                updatetimecount = 0
                myntpsettime()
        
        #当时间到21时和次日7点前，调整亮度最低为1，并且关闭左边工作灯的闪烁
        if hour >= 21 or hour <7:
            tm.brightness(0)
            workledvalue = 0
            workled.value(workledvalue)
        #其他时间段，调整亮度值为6，并且闪烁左边的工作灯
        else:
            tm.brightness(6)
            workledvalue = workledvalue ^ 1
            workled.value(workledvalue)
        
        #200ms刷新一次显示值，由于tm1637控制，肉眼看不出闪烁
        time.sleep(0.2)
        

