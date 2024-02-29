
import datetime
import pytz

#
# tzinfo=datetime.timezone(datetime.timedelta(hours=8))
#
# print(dir(tzinfo),type(tzinfo))
#
# print(str(tzinfo))


print(datetime.timezone(datetime.timedelta(hours=7)))




# pytz.timezone('Etc/GMT-7')

pytz.timezone('UTC+07:00')
