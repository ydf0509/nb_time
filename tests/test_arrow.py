import time

import arrow

date_string = "2023-03-14 08:30:00"
parsed_date = arrow.get(date_string)
print(parsed_date)


print(arrow.get('2013-05-05 12:30:45 America/Chicago', ))
time.sleep(1000)