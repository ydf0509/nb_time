import time
from zoneinfo import ZoneInfo

import nb_log

import datetime

t1 = time.time()
tz_name = 'Asia/Shanghai'
zi = ZoneInfo(tz_name)


def now_str_gmt8():
    t = time.gmtime(time.time() + 8 * 3600)
    return f"{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02} {t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}"

def gen_2_dig_number(n)->str:
    n_str = str(n)
    if len(n_str) == 1:
        return f'0{n_str}'
    else:
        return n_str

DIGIT_MAP = {i: f'{i:02d}' for i in range(100)}
def gen_2_dig_number_v4(n):
    return DIGIT_MAP[n]



import time
from threading import Lock
from typing import Optional


class NowTimeStrCache:
    # 全局变量，用于存储缓存的时间字符串和对应的整秒时间戳
    _cached_time_str: Optional[str] = None
    _cached_time_second: int = 0

    # 为了线程安全，使用锁。在极高并发下，锁的开销远小于每毫秒都进行时间格式化。
    _time_cache_lock = Lock()

    @classmethod
    def get_now_time_str(cls) -> str:
        """
        获取当前时间字符串，格式为 '%Y-%m-%d %H:%M:%S'。
        通过缓存机制，同一秒内的多次调用直接返回缓存结果，极大提升性能。
        适用于对时间精度要求不高（秒级即可）的高并发场景。
        :return: 格式化后的时间字符串，例如 '2024-06-12 15:30:45'
        """


        # 获取当前的整秒时间戳（去掉小数部分）
        current_second = int(time.time())

        # 如果缓存的时间戳与当前秒数一致，直接返回缓存的字符串。
        if current_second == cls._cached_time_second:
            return cls._cached_time_str

        # 如果不一致，说明进入新的一秒，需要重新计算并更新缓存。
        # 使用锁确保在多线程环境下，只有一个线程会执行更新操作。

        with cls._time_cache_lock:
            # 双重检查锁定 (Double-Checked Locking)，防止在等待锁的过程中，其他线程已经更新了缓存。
            if current_second == cls._cached_time_second:
                return cls._cached_time_str

            # 重新计算时间字符串。这里直接使用 time.strftime，因为它在秒级更新的场景下性能足够。
            # 我们不需要像 Funboost 那样为每一毫秒的调用都去做查表优化。
            now = time.localtime(current_second)
            cls._cached_time_str = time.strftime('%Y-%m-%d %H:%M:%S', now)
            cls._cached_time_second = current_second

        return cls._cached_time_str





for i in range(1000000):
    # datetime.datetime.now(tz=zi)  # .strftime("%Y-%m-%d %H:%M:%S")

    # dt = datetime.datetime.now(tz=zi)
    # [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second]
    # now_str = f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
    # now_str2 = f'{dt.year}-{dt.month}-{dt.day} {dt.hour}:{dt.minute}:{dt.second}'
    # now_str3 = f'''{dt.year}-{gen_2_dig_number(dt.month)}-{gen_2_dig_number(dt.day)} {gen_2_dig_number(dt.hour)}:{gen_2_dig_number(dt.minute)}:{gen_2_dig_number(dt.second)}'''

    # now_str4 = f'''{dt.year}-{gen_2_dig_number_v4(dt.month)}-{gen_2_dig_number_v4(dt.day)} {gen_2_dig_number_v4(dt.hour)}:{gen_2_dig_number_v4(dt.minute)}:{gen_2_dig_number_v4(dt.second)}'''
    # now_str_5 = str(dt.year) + '-' + gen_2_dig_number_v4(dt.month) + '-' + gen_2_dig_number_v4(dt.day) + ' ' + gen_2_dig_number_v4(dt.hour) + ':' + gen_2_dig_number_v4(dt.minute) + ':' + gen_2_dig_number_v4(dt.second)

    # dt_naive = dt.replace(tzinfo=None)  # ⚡️ 关键！剥离时区
    # now_str = f'{dt_naive.year:04d}-{dt_naive.month:02d}-{dt_naive.day:02d} {dt_naive.hour:02d}:{dt_naive.minute:02d}:{dt_naive.second:02d}'

    # now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # t = time.localtime()
    # f'{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02} {t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}'

    # now_str_gmt8()

    NowTimeStrCache.get_now_time_str()

print(time.time() - t1)