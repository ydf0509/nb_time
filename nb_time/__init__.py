import copy
import functools
import logging
import sys
import threading
import types
import typing
import re
import time
import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser
import pytz
import arrow

# from pydantic import BaseModel

logger = logging.getLogger(__name__)


@functools.lru_cache()
def get_localzone_ignore_version():  # python3.9以上不一样.  tzlocal 版本在不同python版本上自动安装不同版本
    from tzlocal import get_localzone
    try:
        return get_localzone().zone
    except AttributeError as e:
        return get_localzone().key


# class DateTimeValue(BaseModel):
#     year: int
#     month: int
#     day: int
#     hour: int = 0
#     minute: int = 0
#     second: int = 0
#     microsecond: int = 0


class DateTimeValue:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond

    def dict(self):
        return {
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'hour': self.hour,
            'minute': self.minute,
            'second': self.second,
            'microsecond': self.microsecond
        }


class TimeInParamError(Exception):
    pass

class ArrowWrap(arrow.Arrow):
    def to_nb_time(self):
        return NbTime(self)

class NbTime:
    """ 时间转换，支持链式操作，纯面向对象的的。

    相比模块级下面定义几十个函数，然后将不同类型的时间变量传到不同的函数中return结果，然后把结果作为入参传入到另一个函数进行转换，
    纯面向对象支持链式转换的要方便很多。

    初始化能够接受的变量类型丰富，可以传入一切类型的时间变量。

    """
    FORMATTER_DATETIME = "%Y-%m-%d %H:%M:%S %z"  # 2023-07-03 16:20:21 +0800 ,这种字符串格式的时间清晰明了没有时区的歧义.
    FORMATTER_DATETIME_WITH_ZONE = "%Y-%m-%d %H:%M:%S %z"
    FORMATTER_DATETIME_NO_ZONE = "%Y-%m-%d %H:%M:%S"
    FORMATTER_MILLISECOND = "%Y-%m-%d %H:%M:%S.%f %z"
    FORMATTER_DATE = "%Y-%m-%d"
    FORMATTER_TIME = "%H:%M:%S"
    FORMATTER_ISO = "%Y-%m-%dT%H:%M:%S%z"  # iso8601,全球最标准的时间格式

    TIMEZONE_UTC = 'UTC'
    TIMEZONE_EASTERN_7 = 'UTC+7'
    TIMEZONE_EASTERN_8 = 'UTC+8'  # UTC+08:00 这是东八区
    TIMEZONE_E8 = 'Etc/GMT-8'  # 这个也是东八区，这个Etc/GMT是标准的pytz的支持的格式。
    TIMEZONE_ASIA_SHANGHAI = 'Asia/Shanghai'  # 就是东八区.
    TIMEZONE_TZ_EAST_8 = datetime.timezone(datetime.timedelta(hours=8),
                                           name='UTC+08:00')  # 这种性能比pytz 'Asia/Shanghai' 性能高很多。但pytz可以处理历史夏令时。
    TIMEZONE_TZ_UTC = datetime.timezone(datetime.timedelta(hours=0), name='UTC+07:00')

    default_formatter: str = None
    default_time_zone: str = None

    @classmethod
    def set_default_formatter(cls, datetime_formatter: str):
        cls.default_formatter = datetime_formatter

    @classmethod
    def set_default_time_zone(cls, time_zone: str):
        cls.default_time_zone = time_zone

    @staticmethod
    @functools.lru_cache()
    def get_localzone_name() -> str:
        zone = get_localzone_ignore_version()
        print(f'auto get the system time zone is "{zone}"')
        return zone

    time_zone_str__obj_map = {}

    def __init__(self,
                 datetimex: typing.Union[
                     None, int, float, datetime.datetime, str, 'NbTime', DateTimeValue, arrow.Arrow] = None,
                 *,
                 datetime_formatter: str = None,
                 time_zone: typing.Union[str, datetime.tzinfo, None] = None):
        """
        :param datetimex: 接受时间戳  datatime类型 和 时间字符串 和类对象本身四种类型,如果为None，则默认当前时间now。
        :param time_zone  时区例如 Asia/Shanghai， UTC  UTC+8  GMT+8  Etc/GMT-8 等,也可以是 datetime.timezone(datetime.timedelta(hours=7))东7区,
                          默认是操作系统时区
        """
        # init_params = copy.copy(locals())
        # init_params.pop('self')
        # init_params.pop('datetimex')
        init_params = {'datetime_formatter': datetime_formatter, 'time_zone': time_zone}
        self.init_params = init_params
        self.first_param = datetimex

        self.time_zone_str = self.get_time_zone_str(time_zone)
        self.datetime_formatter = datetime_formatter or self.default_formatter or self.FORMATTER_ISO
        '''
        将 time_zone 转成 pytz 可以识别的对应时区
        '''
        self.time_zone_obj = self.build_pytz_timezone(self.time_zone_str)
        self.datetime_obj = self.build_datetime_obj(datetimex)
        self.datetime = self.datetime_obj

    def _build_nb_time(self, datetimex) -> 'NbTime':
        return self.__class__(datetimex, **self.init_params)

    def get_time_zone_str(self, time_zone: typing.Union[str, datetime.tzinfo, None] = None):
        return time_zone or self.default_time_zone or self.get_localzone_name()

    def universal_parse_datetime_str(self, datetime_str):
        try:
            return dateutil.parser.parse(datetime_str)
        except Exception as e:
            date_string = datetime_str  # "2013-05-05 12:30:45 America/Chicago"
            date_parts = date_string.split()
            parsed_date = dateutil.parser.parse(' '.join(date_parts[:-1]))
            timezone = dateutil.tz.gettz(date_parts[-1])
            datetime_obj = parsed_date.replace(tzinfo=timezone)
            return self._build_nb_time(datetime_obj).datetime_obj

    def build_datetime_obj(self, datetimex):
        if datetimex is None:
            # print(self.time_zone_obj,type(self.time_zone_obj))
            datetime_obj = datetime.datetime.now(tz=self.time_zone_obj)
        elif isinstance(datetimex, str):
            # print(self.datetime_formatter)
            if '%z' in self.datetime_formatter and ('+' not in datetimex or '-' not in datetimex):
                datetimex = self.add_timezone_to_time_str(datetimex, self.time_zone_str)
            try:
                datetime_obj = datetime.datetime.strptime(datetimex, self.datetime_formatter)
            except Exception as e:
                # print(e,type(e))
                # print(f'尝试使用万能时间字符串解析 {datetimex}')
                logger.warning(f'warning! formatter: {self.datetime_formatter} cannot parse time str: {datetimex}  , {type(e)} , {e}  , will try use  Universal time string parsing')
                datetime_obj = self.universal_parse_datetime_str(datetimex)
            # print(repr(datetime_obj))
            if datetime_obj.tzinfo is None:
                if isinstance(self.time_zone_obj, pytz.BaseTzInfo):
                    datetime_obj = self.time_zone_obj.localize(datetime_obj, )
                else:
                    datetime_obj = datetime_obj.replace(tzinfo=self.time_zone_obj, )
            else:
                datetime_obj = datetime_obj.astimezone(self.time_zone_obj)
            # if isinstance(self.time_zone_obj,pytz.BaseTzInfo) and datetime_obj.tzinfo is None:
            #     datetime_obj = self.time_zone_obj.localize(datetime_obj, )
            # else:
            #     datetime_obj = datetime_obj.replace(tzinfo=self.time_zone_obj, )
            # print(repr(datetime_obj))
        elif isinstance(datetimex, (int, float)):
            if datetimex < 1:
                datetimex += 86400
            if datetimex >= 10 ** 12:
                # raise TimeInParamError(
                #     f'Invalid datetime param: {datetimex}. need seconds,not microseconds')  # 需要传入秒，而不是毫秒
                datetimex = datetimex / 1000.0
            datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=self.time_zone_obj)  # 时间戳0在windows会出错。
        elif isinstance(datetimex, datetime.datetime):
            datetime_obj = datetimex
            datetime_obj = datetime_obj.astimezone(tz=self.time_zone_obj)
        elif isinstance(datetimex, DateTimeValue):
            datetime_obj = datetime.datetime(**datetimex.dict(), tzinfo=self.time_zone_obj)
        elif isinstance(datetimex, NbTime):
            datetime_obj = datetimex.datetime_obj
            datetime_obj = datetime_obj.astimezone(tz=self.time_zone_obj)
        elif isinstance(datetimex, arrow.Arrow):
            datetime_obj = datetimex.datetime
            datetime_obj = datetime_obj.astimezone(tz=self.time_zone_obj)
        else:
            raise ValueError('input parameters is not right')
        return datetime_obj

    @classmethod
    def add_timezone_to_time_str(cls, datetimex: str, time_zone: str):
        offset = cls.get_timezone_offset(time_zone)
        offset_hour = int(offset.total_seconds() // 3600)
        abs_offset_hour = abs(offset_hour)
        int_timezone = ''
        if abs_offset_hour < 10:
            int_timezone = f'0{abs_offset_hour}00'
        else:
            int_timezone = f'{abs_offset_hour}00'
        if offset_hour < 0:
            int_timezone = f'-{int_timezone}'
        else:
            int_timezone = f'+{int_timezone}'
        if not cls._contains_two_or_more_letters(datetimex):
            datetimex += f' {int_timezone}'
        return datetimex

    @staticmethod
    def _contains_two_or_more_letters(text):
        pattern = r"[a-zA-Z]"
        letters = re.findall(pattern, text)
        return len(letters) >= 2

    @classmethod
    def get_timezone_offset(cls, time_zone: str) -> datetime.timedelta:
        tz = cls.build_pytz_timezone(time_zone)
        # 将时区转换为以Etc/GMT+形式表示的时区
        offset = tz.utcoffset(datetime.datetime.now())
        return offset

    @staticmethod
    def _utc_to_etc(timezone_str: str):
        """把UTC+8或UTC+08:00 转化成pytz可以识别的Etc/GMT-8的时区格式"""
        offset_match = re.match(r"UTC([+-]?)(\d{1,2}):?(\d{0,2})", timezone_str)
        if not offset_match:
            return timezone_str
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
        return new_timezone

    @classmethod
    def build_pytz_timezone(cls, time_zone: typing.Union[str, datetime.tzinfo]) -> datetime.tzinfo:
        """pytz 不支持 GTM+8  UTC+7 这种时区表示方式
        Etc/GMT-8 就是 GMT+8 代表东8区。
        """
        # print(time_zone,type(time_zone))
        time_zone0 = time_zone
        if time_zone0 in cls.time_zone_str__obj_map:
            # print('zhijie')
            return cls.time_zone_str__obj_map[time_zone0]

        if isinstance(time_zone, datetime.tzinfo):
            return time_zone

        # 常见时区字符串转化为内置的timezone类型，比pytz性能高很多。
        if time_zone in (cls.TIMEZONE_ASIA_SHANGHAI, cls.TIMEZONE_E8, cls.TIMEZONE_EASTERN_8):
            # print('aaaa')
            return cls.TIMEZONE_TZ_EAST_8
        if time_zone in (cls.TIMEZONE_UTC, 'UTC+0'):
            return cls.TIMEZONE_TZ_UTC

        if 'Etc/GMT' in time_zone:
            return pytz.timezone(time_zone)
        # print(time_zone,type(time_zone))
        time_zone = cls._utc_to_etc(time_zone)
        # print(time_zone)
        # pytz_timezone_xialinshi = pytz.timezone(time_zone)
        pytz_timezone = pytz.timezone(time_zone, )

        # print(pytz_timezone)
        # # UTC 负时区对应的 pytz 可以识别的时区
        # burden_timezone = 'Etc/GMT+'
        # # UTC 正时区对应的 pytz 可以识别的时区
        # just_timezone = 'Etc/GMT-'
        # # 截取 UTC 时区差值,eg:zone_code=UTC+5,count=5
        # count = time_zone[-1]
        # if '-' in time_zone:  # 就是这样没有反。
        #     pytz_timezone = pytz.timezone(burden_timezone + count)
        # elif '+' in time_zone:
        #     pytz_timezone = pytz.timezone(just_timezone + count)
        # else:
        #     pytz_timezone = pytz.timezone(time_zone)
        cls.time_zone_str__obj_map[time_zone0] = pytz_timezone
        return pytz_timezone

    @property
    def datetime_str(self) -> str:
        return self.get_str()

    @property
    def time_str(self) -> str:
        return self.datetime_obj.strftime(self.FORMATTER_TIME)

    @property
    def date_str(self) -> str:
        return self.datetime_obj.strftime(self.FORMATTER_DATE)

    def get_str(self, formatter=None):
        # print(self.datetime_formatter)
        return self.datetime_obj.strftime(formatter or self.datetime_formatter)

    def fast_get_str_formatter_datetime_no_zone(self):
        return f'{self.datetime_obj.year:04d}-{self.datetime_obj.month:02d}-{self.datetime_obj.day:02d} {self.datetime_obj.hour:02d}:{self.datetime_obj.minute:02d}:{self.datetime_obj.second:02d}'

    @property
    def timestamp(self) -> float:
        return self.datetime_obj.timestamp()

    @property
    def timestamp_millisecond(self) -> float:
        return self.datetime_obj.timestamp() * 1000

    def is_greater_than_now(self) -> bool:
        return self.timestamp > time.time()

    def __lt__(self, other: 'NbTime'):
        return self.timestamp < other.timestamp

    def __gt__(self, other: 'NbTime'):
        return self.timestamp > other.timestamp

    def __eq__(self, other: 'NbTime'):
        return self.timestamp == other.timestamp

    def __str__(self) -> str:
        return f'<NbTime [{self.datetime_str}] ({self.time_zone_str})>'

    def __repr__(self) -> str:
        return f'<NbTime [{self.datetime_str}] ({self.time_zone_str})>'

    def humanize(self)->str:
        return self.arrow.humanize()

    def to_arrow(self)->ArrowWrap:
        # return arrow.get(self.datetime_obj)
        return ArrowWrap(year=self.datetime_obj.year, month=self.datetime_obj.month, day=self.datetime_obj.day,
                         hour=self.datetime_obj.hour,minute=self.datetime_obj.minute,second=self.datetime_obj.second,
                         microsecond=self.datetime_obj.microsecond,
                         tzinfo=self.time_zone_str)

    @property
    def arrow(self) -> ArrowWrap:
        if getattr(self, '_arrow_obj', None) is None:
            self._arrow_obj = self.to_arrow()
        return self._arrow_obj

    def isoformat(self, timespec: typing.Literal['seconds', 'milliseconds', 'microseconds'] = 'seconds') -> str:
        """
        返回 ISO 8601 格式字符串
        :param timespec: 'seconds', 'milliseconds', 'microseconds'
        """
        return self.datetime_obj.isoformat(timespec=timespec)

    def __call__(self) -> datetime.datetime:
        return self.datetime_obj

    def clone(self) -> "NbTime":
        return self._build_nb_time(self.datetime_obj, )

    def __copy__(self):
        return self.clone()

    def shift(self, years=0, months=0, days=0, leapdays=0, weeks=0,
              hours=0, minutes=0, seconds=0, microseconds=0, ) -> 'NbTime':
        relativedeltax = relativedelta(years=years, months=months, days=days, leapdays=leapdays, weeks=weeks,
                                       hours=hours, minutes=minutes, seconds=seconds,
                                       microseconds=microseconds, )
        new_date = self.datetime_obj + relativedeltax
        # seconds_delta = seconds + minutes * 60 + hours * 3600 + days * 86400 + weeks * 86400 * 7
        return self._build_nb_time(new_date, )

    def replace(self, year=None,
                month=None,
                day=None,
                hour=None,
                minute=None,
                second=None,
                microsecond=None,
                ):
        kw = copy.copy(locals())
        kw.pop('self')
        kw_new = {}
        for k, v in kw.items():
            if v is not None:
                kw_new[k] = v
        datetime_new = self.datetime_obj.replace(**kw_new)
        return self._build_nb_time(datetime_new)

    def to_tz(self, time_zone: str) -> 'NbTime':
        init_params = copy.copy(self.init_params)
        init_params['time_zone'] = time_zone
        return self.__class__(self.timestamp, **init_params)

    def to_utc(self):
        return self.to_tz(self.TIMEZONE_UTC)

    def to_utc8(self):
        return self.to_tz(self.TIMEZONE_E8)

    @property
    def today_zero(self) -> 'NbTime':
        now = datetime.datetime.now(tz=self.time_zone_obj)
        today_zero_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self._build_nb_time(today_zero_datetime, )

    @property
    def today_zero_timestamp(self) -> float:
        # zero_ts = time.mktime(datetime.date.today().timetuple())
        # return zero_ts

        # # 获取当天零点时间
        # today_start = self.time_zone_obj.localize(datetime.datetime(now.year, now.month, now.day, 0, 0, 0))
        # # today_start =datetime.datetime(now.year, now.month, now.day, 0, 0, 0,tzinfo=self.time_zone_obj)
        # # 将当天零点时间转换为时间戳
        # timestamp = int(today_start.timestamp())

        return self.today_zero.timestamp

    @property
    def same_day_zero(self) -> 'NbTime':
        """
        获取时间对象对应的当天的该对象时区的0点的 NbTime对象
        :return:
        """

        same_day_zero_datetime = self.datetime_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        return self._build_nb_time(same_day_zero_datetime, )

    @staticmethod
    def seconds_to_hour_minute_second(seconds):
        """
        把秒转化成还需要的时间
        :param seconds:
        :return:
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)


class PopularNbTime(NbTime):
    @property
    def ago_1_days(self):
        return self.shift(days=-1)

    @property
    def ago_7_days(self):
        return self.shift(days=-7)

    @property
    def ago_30_days(self):
        return self.shift(days=-30)

    @property
    def ago_180_days(self):
        return self.shift(days=-180)

    @property
    def ago_360_days(self):
        return self.shift(days=-360)

    @property
    def ago_720_days(self):
        return self.shift(days=-720)


class UtcNbTime(NbTime):
    default_time_zone = NbTime.TIMEZONE_UTC


class ShanghaiNbTime(NbTime):
    # default_time_zone = NbTime.TIMEZONE_ASIA_SHANGHAI
    default_time_zone = NbTime.TIMEZONE_TZ_EAST_8
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE


class NowTimeStrCache:
    # 生成100万次当前时间字符串%Y-%m-%d %H:%M:%S仅需0.4秒.
    # 全局变量，用于存储缓存的时间字符串和对应的整秒时间戳
    _cached_time_str: typing.Optional[str] = None
    _cached_time_second: int = 0

    # 为了线程安全，使用锁。在极高并发下，锁的开销远小于每毫秒都进行时间格式化。
    _time_cache_lock = threading.Lock()

    @classmethod
    def fast_get_now_time_str(cls, timezone_str: str = None) -> str:
        """
        获取当前时间字符串，格式为 '%Y-%m-%d %H:%M:%S'。
        通过缓存机制，同一秒内的多次调用直接返回缓存结果，极大提升性能。
        适用于对时间精度要求不高（秒级即可）的高并发场景。
        :return: 格式化后的时间字符串，例如 '2024-06-12 15:30:45'
        """
        # timezone_str = timezone_str or FunboostCommonConfig.TIMEZONE

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
            now = datetime.datetime.now(tz=pytz.timezone(timezone_str))
            cls._cached_time_str = now.strftime('%Y-%m-%d %H:%M:%S', )
            cls._cached_time_second = current_second

        return cls._cached_time_str


if __name__ == '__main__':
    import nb_log

    """
    1557113661.0
    '2019-05-06 12:34:21'
    '2019/05/06 12:34:21'
    NbTime(1557113661.0)()
    """

    print(NbTime.get_localzone_name())

    print(NbTime(time_zone='UTC+8').today_zero_timestamp)
    print(NbTime(time_zone='UTC+7').datetime_obj)
    print(NbTime(time_zone='UTC+8').datetime_str)
    print(NbTime(time_zone='UTC+7').time_zone_obj)

    print(NbTime.get_timezone_offset('Asia/Shanghai'))
    # NbTime.set_default_formatter(NbTime.FORMATTER_MILLISECOND)
    NbTime.set_default_time_zone('UTC+8')

    # print(NbTime('2023-05-06 12:12:12'))
    print(NbTime())
    print(NbTime(datetime.datetime.now()))  # 和上面等效
    print(NbTime(1709192429))
    print(NbTime('2024-02-26 15:58:21', datetime_formatter=NbTime.FORMATTER_DATETIME_NO_ZONE,
                 time_zone=NbTime.TIMEZONE_EASTERN_7).datetime)
    print(NbTime(DateTimeValue(year=2022, month=5, day=9, hour=6), time_zone='UTC+7'))

    print(NbTime(datetime.datetime.now(tz=pytz.timezone('Etc/GMT+0')), time_zone='UTC+8'))
    print(NbTime().shift(months=1).shift(hours=-1))
    print(NbTime(datetime_formatter=NbTime.FORMATTER_MILLISECOND).to_tz(time_zone='UTC+8').to_tz(time_zone='UTC+0'))

    print(NbTime.get_timezone_offset(NbTime.get_localzone_name()).total_seconds())

    print(NbTime(time_zone='UTC+7').today_zero_timestamp)

    print(NbTime.seconds_to_hour_minute_second(450))

    print(NbTime(time_zone=NbTime.TIMEZONE_ASIA_SHANGHAI).datetime.tzinfo)

    print(NbTime(time_zone='UTC+8').time_zone_obj)
    print(NbTime(time_zone='UTC+07:00').time_zone_obj)

    print(NbTime(time_zone=datetime.timezone(datetime.timedelta(hours=7))))

    print(
        NbTime(NbTime('2024-02-29 07:40:34', time_zone='UTC+0', datetime_formatter=NbTime.FORMATTER_DATETIME_NO_ZONE),
               time_zone='UTC+8', datetime_formatter=NbTime.FORMATTER_MILLISECOND).datetime_str
    )

    print(NbTime('2024-02-29 07:40:34', time_zone='UTC+7'))
    print(NbTime(NbTime('2024-02-29 07:40:34', time_zone='UTC+7'), time_zone='UTC+8',
                 datetime_formatter=NbTime.FORMATTER_ISO).datetime_str)
    print(NbTime('2024-02-29 07:40:34', time_zone='UTC+7').to_tz('UTC+8').to_tz('utc').to_utc().datetime_str)

    print(NbTime().get_str('%Y%m%d'))
    print(NbTime().today_zero)
    print(NbTime().today_zero_timestamp)

    print(NbTime().replace(day=10, ).to_tz('UTC+6'))
    print(NbTime().shift(days=-7).timestamp_millisecond)

    print(NbTime(1709283094))

    print(NbTime(DateTimeValue(year=2023, month=7, day=5, hour=4, minute=3, second=2, microsecond=1))
          > NbTime(DateTimeValue(year=2023, month=6, day=6, hour=4, minute=3, second=2, microsecond=1)))

    print(NbTime(1727252278000))

    print(PopularNbTime().ago_7_days.timestamp_millisecond)

    print(UtcNbTime())

    print(UtcNbTime().today_zero.timestamp_millisecond)

    print(ShanghaiNbTime())

    print(NbTime('20230506T010203.886 +08:00'))
    print(NbTime('2023-05-06 01:02:03.886'))
    print(NbTime('2023-05-06T01:02:03.886 +08:00'))
    print(NbTime('20221206 1:2:3'))
    print(NbTime('Fri Jul 19 06:38:27 2024'))
    print(NbTime('2013-05-05 12:30:45 America/Chicago'))
    print(NbTime('2013-05-05 12:30:45 America/Chicago').isoformat())
    print(NbTime('Jun 12 2024 10:30AM'))

    import arrow

    # print(arrow.get("tomorrow at 3pm")) # 报错
    # print(NbTime("tomorrow at 3pm"))
    print(arrow.now().shift(hours=-3).shift(days=6).humanize())
    print(arrow.now().shift(hours=-3).shift(days=6))

    print(NbTime('2025-09-29 10:01:02').humanize())
    print(NbTime('2025-09-29 10:01:02').isoformat('microseconds'))

    print(NbTime(arrow.now(tz='utc+7')))

    print(NbTime().arrow.floor('hour'))
    print(NbTime().arrow.floor('day'))
    print(NbTime().arrow.ceil('day').to_nb_time().timestamp) # nb_time 和 arrow 之间 无限链式转化

    print()
    for i in range(1000000):
        # ShanghaiNbTime(time_zone='Asia/Shanghai').get_str()
        # ShanghaiNbTime(time_zone='UTC+8').get_str()
        # datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # NbTime(time_zone='Asia/Shanghai') # 3秒100万次
        arrow.now(tz='Asia/Shanghai') # 20秒100万次
        # datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
        # NbTime().fast_get_str_formatter_datetime_no_zone()
        # get_now_time_str_by_tz()

        # ts = 1717567890  # 示例时间戳
        # time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

        # datetime.datetime.now()#.strftime("%Y-%m-%d %H:%M:%S")
        # NowTimeStrCache.fast_get_now_time_str('Asia/Shanghai')
    print()
