

# 1 NbTime 介绍

```
NbTime 是oop面向对象开发的爽快的日期时间操作类
NbTime 支持无限链式操作来处理时间,
(因为是oop所以易用程度远远的暴击面向过程python工程师写的time_utils.py里面
写几百个独立的操作时间的面向过程函数)

NbTime 入参支持 None 字符串 时间戳 datetime对象 NbTime对象自身
NbTime 非常轻松支持时区转化
Nbtime 内置属性 datetime对象,兼容性好

NbTime操作时间,远远暴击使用datetime和三方arrow包,
远远暴击用户在 utils.time_utils.py文件中写几百个孤立的面向过程操作时间的函数.
```

## 1.1 安装 

pip install nb_time

# 2 NbTime 时间值传参用法

## 2.1 NbTime 不传参,就是当前时间
```
>>> from nb_time import NbTime
>>> NbTime()                   
<NbTime [2024-02-29 17:51:14 +0800]>
```

## 2.2 NbTime 传参datetime对象

```
>>> NbTime(datetime.datetime.now())
<NbTime [2024-02-29 17:56:43 +0800]>
```

## 2.3 NbTime 传参时间戳
```
>>> NbTime(1709192429)
<NbTime [2024-02-29 15:40:29 +0800]>
```

## 2.4 NbTime 传参字符串,可以对字符串设置时区,例如把东七区的时间字符串转化成东8区的格式.
```
>>> NbTime('2024-02-26 15:58:21',datetime_formatter=NbTime.FORMATTER_DATETIME,time_zone=NbTime.TIMEZONE_EASTERN_7).to_tz('UTC+8')
<NbTime [2024-02-26 16:58:21 +0800]>
```

## 2.5 NbTime 传参 DateTimeValue类型对象
```
>>> from nb_time import DateTimeValue
>>> NbTime(DateTimeValue(year=2022,month=5,day=9,hour=6),time_zone='UTC+7')
<NbTime [2022-05-09 06:00:00 +0700]>

```

## 2.6 NbTime传参 NbTime对象

NbTime入参本身支持无限嵌套NbTime对象
```
NbTime(NbTime(NbTime(NbTime())))
<NbTime [2024-02-29 18:39:09]>


为什么 NbTime支持入参是自身类型,例如你可以方便的转时区和转字符串格式化
例如0时区的2024-02-29 07:40:34,你要转化成8时区的带毫秒带时区的时间字符串,
>>> from nb_time import NbTime                                                                                                    
>>> NbTime(NbTime('2024-02-29 07:40:34', time_zone='UTC+0', datetime_formatter=NbTime.FORMATTER_DATETIME_NO_ZONE),
...                time_zone='UTC+8', datetime_formatter=NbTime.FORMATTER_MILLISECOND).datetime_str
'2024-02-29 15:40:34.000000 +0800'
```

# 3 NbTime 链式计算时间

NbTime().shift方法返回的对象仍然是Nbtime类型。
因为Nbtime对象本身具有很多好用的属性和方法，所以使用NbTime作为时间转化的中转对象，比使用datetime作为中转对象方便使用很多。


求3天1小时10分钟后的时间,入参支持正数和负数
```
>>> NbTime().shift(hours=1,minutes=10).shift(days=3)
<NbTime [2024-03-03 19:02:49 +0800]>
```

求当前时间1天之前的时间戳
```commandline
>>> NbTime().shift(days=-1).timestamp
1709290123.409756

```







# 3 NbTime 时区设置

## 3.1 NbTime 实例化时候设置时区

实例化时候分别设置东7区和0时区
```
>>> NbTime(time_zone='UTC+7')
<NbTime [2024-02-29 17:05:08 +0700]>
>>> NbTime(time_zone='UTC+0') 
<NbTime [2024-02-29 10:05:08 +0000]>
```

## 3.2 全局设置时区
用户不传递时区时候,默认就是操作系统时区,如果用户想统一设置时区

例如用户统一设置东8区,以后实例化就不用每次亲自传递东八区.
```
NbTime.set_default_time_zone('UTC+8')
```

# 4 设置时间字符串格式化

## 4.1 NBTime实例化时候设置时间字符串格式
用户不想要毫秒时间字符串
```
>>> NbTime(datetime_formatter=NbTime.FORMATTER_DATETIME)    
<NbTime [2024-02-29 18:10:57 +0800]>
```

用户不想要字符串带时区
```
>>> NbTime(datetime_formatter=NbTime.FORMATTER_DATETIME_NO_ZONE) 
<NbTime [2024-02-29 18:12:18]>
```

##  4.2 NBTime全局设置字符串格式

NbTime.set_default_formatter 可以全局设置时间格式字符串,就不需要每次都传递格式
```
>>> NbTime.set_default_formatter(NbTime.FORMATTER_DATETIME_NO_ZONE)
>>> NbTime()
<NbTime [2024-02-29 18:14:38]>
```

# 5 NbTime 对象内置的成员属性

见下面的交互,NbTime类型对象有非常便捷的各种成员变量,

```
datetime  类型datetime.datetime类型的时间对象,这个很方便和内置类型关联起来
time_zone_obj 时区
datetime_str 日期时间字符串
time_str 时间字符串
date_str 日期字符串
timestamp  时间戳秒
timestamp_millisecond 时间戳毫秒
today_zero_timestamp 当天凌晨的时间戳
```

```
>>> nbt=NbTime()
>>> nbt.datetime
datetime.datetime(2024, 2, 29, 18, 16, 23, 541415, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)

>>> nbt.time_zone_obj
<DstTzInfo 'Asia/Shanghai' LMT+8:06:00 STD>

>>> nbt.datetime_str
'2024-02-29 18:16:23'

>>> nbt.time_str
'18:16:23'

>>> nbt.date_str
'2024-02-29'

>>> nbt.timestamp
1709201783.541415

>>> nbt.timestamp_millisecond
1709201783541.415

>>> nbt.today_zero_timestamp
1709136000

```

# 6 NbTime的方法

## 6.1 get_str 方法转化成任意字符串格式
```
例如获取今天的年月日,中间不要带 - 
>>> NbTime().get_str('%Y%m%d')
20240301
```

## 6.2 shift 是计算生成新的NbTime对象,支持无限连续链式操作
```
求3天1小时10分钟后的时间,入参支持正数和负数
>>> NbTime().shift(hours=1,minutes=10).shift(days=3)
<NbTime [2024-03-03 19:02:49 +0800]>
```

## 6.3 to_tz 是生成新的时区的NbTime对象,把NbTime对象转化成另一个时区.
```
一个东7区的时间:
>>> NbTime('2024-02-26 15:58:21',datetime_formatter=NbTime.FORMATTER_DATETIME,time_zone=NbTime.TIMEZONE_EASTERN_7)
<NbTime [2024-02-26 15:58:21 +0700]>

那这个东7区的时间转化成东8区的时间:
>>> NbTime('2024-02-26 15:58:21',datetime_formatter=NbTime.FORMATTER_DATETIME,time_zone=NbTime.TIMEZONE_EASTERN_7).to_tz('UTC+8')
<NbTime [2024-02-26 16:58:21 +0800]>
```


# 7 NbTime总结

```
总结就是 NbTime 的入参接受所有类型,NbTime支持链式调用,Nbtime方便支持时区,Nbtime方便操作时间转化,
所以NbTime操作时间,远远暴击使用datetime和三方arrow包,
远远暴击用户在 utils.time_utils.py文件中写几百个孤立的面向过程操作时间的函数.
```