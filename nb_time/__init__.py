import copy
import functools
import typing
import re
import time
import datetime
import pytz
from pydantic import BaseModel


@functools.lru_cache()
def get_localzone_ignore_version():  # python3.9以上不一样.  tzlocal 版本在不同python版本上自动安装不同版本
    from tzlocal import get_localzone
    try:
        return get_localzone().zone
    except AttributeError as e:
        return get_localzone().key


class DateTimeValue(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    second: int = 0
    microsecond: int = 0


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

    TIMEZONE_UTC = 'UTC'
    TIMEZONE_EASTERN_7 = 'UTC+7'
    TIMEZONE_EASTERN_8 = 'UTC+8'  # UTC+08:00 这是东八区
    TIMEZONE_E8 = 'Etc/GMT-8'  # 这个也是东八区，这个Etc/GMT是标准的pytz的支持的格式。
    TIMEZONE_ASIA_SHANGHAI = 'Asia/Shanghai'  # 就是东八区.

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
        # print(f'get the system time zone is "{zone}"')
        return zone

    def __init__(self,
                 datetimex: typing.Union[None, int, float, datetime.datetime, str, 'NbTime', DateTimeValue] = None,
                 *,
                 datetime_formatter: str = None,
                 time_zone: typing.Union[str, datetime.tzinfo] = None):
        """
        :param datetimex: 接受时间戳  datatime类型 和 时间字符串 和类对象本身四种类型,如果为None，则默认当前时间now。
        :param time_zone  时区例如 Asia/Shanghai， UTC  UTC+8  GMT+8  Etc/GMT-8 等,也可以是 datetime.timezone(datetime.timedelta(hours=7))东7区,
                          默认是操作系统时区
        """
        init_params = copy.copy(locals())
        init_params.pop('self')
        init_params.pop('datetimex')
        self.init_params = init_params

        self.time_zone_str = time_zone or self.default_time_zone or self.get_localzone_name()
        self.datetime_formatter = datetime_formatter or self.default_formatter or self.FORMATTER_DATETIME
        '''
        将 time_zone 转成 pytz 可以识别的对应时区
        '''
        self.time_zone_obj = self.build_pytz_timezone(self.time_zone_str)
        self.datetime_obj = self.build_datetime_obj(datetimex)
        self.datetime = self.datetime_obj

    def _build_nb_time(self, datetimex) -> 'NbTime':
        return self.__class__(datetimex, **self.init_params)

    def build_datetime_obj(self, datetimex):
        if isinstance(datetimex, DateTimeValue):
            datetime_obj = datetime.datetime(**datetimex.model_dump(), tzinfo=self.time_zone_obj)
        elif isinstance(datetimex, str):
            # print(self.datetime_formatter)
            if '%z' in self.datetime_formatter and ('+' not in datetimex or '-' not in datetimex):
                datetimex = self.add_timezone_to_time_str(datetimex, self.time_zone_str)
            datetime_obj = datetime.datetime.strptime(datetimex, self.datetime_formatter)
            datetime_obj = datetime_obj.replace(tzinfo=self.time_zone_obj)
        elif isinstance(datetimex, (int, float)):
            if datetimex < 1:
                datetimex += 86400
            datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=self.time_zone_obj)  # 时间戳0在windows会出错。
        elif isinstance(datetimex, datetime.datetime):
            datetime_obj = datetimex
            datetime_obj = datetime_obj.astimezone(tz=self.time_zone_obj)
        elif isinstance(datetimex, NbTime):
            datetime_obj = datetimex.datetime_obj
            datetime_obj = datetime_obj.astimezone(tz=self.time_zone_obj)
        elif datetimex is None:
            datetime_obj = datetime.datetime.now(tz=self.time_zone_obj)
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
        datetimex += f' {int_timezone}'
        return datetimex

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
        if isinstance(time_zone, datetime.tzinfo):
            return time_zone
        if 'Etc/GMT' in time_zone:
            return pytz.timezone(time_zone)
        # print(time_zone)
        time_zone = cls._utc_to_etc(time_zone)
        # print(time_zone)
        pytz_timezone = pytz.timezone(time_zone)
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
        return self.datetime_obj.strftime(formatter or self.datetime_formatter)

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
        return f'<NbTime [{self.get_str()}]>'

    def __repr__(self) -> str:
        return f'<NbTime [{self.datetime_str}]>'

    def __call__(self) -> datetime.datetime:
        return self.datetime_obj

    def clone(self) -> "NbTime":
        return self._build_nb_time(self.datetime_obj, )

    def __copy__(self):
        return self.clone()

    def shift(self, seconds=0, minutes=0, hours=0, days=0, weeks=0, ) -> 'NbTime':
        seconds_delta = seconds + minutes * 60 + hours * 3600 + days * 86400 + weeks * 86400 * 7
        return self._build_nb_time(self.timestamp + seconds_delta, )

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
    default_time_zone = NbTime.TIMEZONE_ASIA_SHANGHAI
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE


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
    NbTime.set_default_formatter(NbTime.FORMATTER_MILLISECOND)
    NbTime.set_default_time_zone('UTC+8')

    # print(NbTime('2023-05-06 12:12:12'))
    print(NbTime())
    print(NbTime(datetime.datetime.now()))  # 和上面等效
    print(NbTime(1709192429))
    print(NbTime('2024-02-26 15:58:21', datetime_formatter=NbTime.FORMATTER_DATETIME_NO_ZONE,
                 time_zone=NbTime.TIMEZONE_EASTERN_7).datetime)
    print(NbTime(DateTimeValue(year=2022, month=5, day=9, hour=6), time_zone='UTC+7'))

    print(NbTime(datetime.datetime.now(tz=pytz.timezone('Etc/GMT+0')), time_zone='UTC+8'))
    print(NbTime().shift(hours=1).shift(days=3))
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

    print(NbTime().get_str('%Y%m%d'))
    print(NbTime().today_zero)
    print(NbTime().today_zero_timestamp)

    print(NbTime().replace(day=10, ).to_tz('UTC+6'))
    print(NbTime().shift(days=-7).timestamp_millisecond)

    print(NbTime(1709283094))

    print(NbTime(DateTimeValue(year=2023, month=7, day=5, hour=4, minute=3, second=2, microsecond=1))
          > NbTime(DateTimeValue(year=2023, month=6, day=6, hour=4, minute=3, second=2, microsecond=1)))

    print(PopularNbTime().ago_7_days.timestamp_millisecond)

    print(UtcNbTime())

    print(UtcNbTime().today_zero.timestamp_millisecond)

    print(ShanghaiNbTime())
