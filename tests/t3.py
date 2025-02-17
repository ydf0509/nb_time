import nb_log
from nb_time import NbTime

miao = NbTime('23010108', datetime_formatter='%y%m%d%H')
print(miao.datetime_obj)

print(miao.shift(hours=1).datetime_obj)


# import datetime
# import pytz
#
# m = datetime.datetime.strptime('19020108', '%y%m%d%H')
# print(m,m.timestamp(),m.tzinfo,repr(m))
#
# n = m.replace(tzinfo=pytz.timezone('Asia/Shanghai'))   # Etc/GMT-8    Asia/Shanghai
# print(n,n.timestamp(),n.tzinfo,repr(n))
#
# print(n.timestamp() -m.timestamp())


# import datetime
# import pytz
#
# # 创建 naive datetime 对象 m
# m = datetime.datetime.strptime('23010108', '%y%m%d%H')
#
# # 将 naive datetime 对象 m 转换为带有时区信息的 datetime 对象 n
# shanghai_tz = pytz.timezone('Asia/Shanghai')
# m_localized = shanghai_tz.localize(m)
#
# # 获取 m_localized 的 timestamp
# m_timestamp = m_localized.timestamp()
#
# # 打印结果
# print(f"Localized DateTime: {m_localized}, Timestamp: {m_timestamp}, TZInfo: {m_localized.tzinfo}")
#
# # 直接使用 localized datetime 对象进行操作
# n = m_localized
# n_timestamp = n.timestamp()
#
# # 打印结果
# print(f"DateTime with fold 0: {n}, Timestamp: {n_timestamp}, TZInfo: {n.tzinfo}")
#
# # 计算时间戳差值
# print(f"Difference in timestamps: {n_timestamp - m_timestamp}")
