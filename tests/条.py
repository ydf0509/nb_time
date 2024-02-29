import re

# 输入的时区表示
timezone_str = "UTC+07:00"
timezone_str = "UTC+7"

# 使用正则表达式提取时区偏移量
offset_match = re.match(r"UTC([+-]?)(\d{1,2}):?(\d{0,2})", timezone_str)

# 提取小时和分钟的偏移量
sign = offset_match.group(1)
hours = offset_match.group(2)
minutes = offset_match.group(3)

if sign == "+":
    sign = "-"
else:
    sign = "+"

# 构建新的时区表示
new_timezone = f"Etc/GMT{sign}{int(hours)}"

# 打印转换后的时区表示
print(new_timezone)



import pytz
print(pytz.timezone(new_timezone))