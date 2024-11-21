
from dateutil import parser
from datetime import datetime

time_string = "2023-03-14T12:00:00.1234567 +0800"
parsed_time = parser.parse(time_string)

print(parsed_time.tzinfo,parsed_time,type(parsed_time))

