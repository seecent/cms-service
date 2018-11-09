from __future__ import absolute_import
from datetime import datetime, timedelta

DTF = "%Y-%m-%d"
DF = "%Y-%m-%d %H:%M:%S"


class DateUtil:

    @staticmethod
    def get_week_of_month(date_time):
        """
        获取指定的某天是某个月中的第几周
        周一作为一周的开始

        Parameters:
          date_time - 日期时间

        Returns:
          第几周
        """
        end = int(date_time.strftime("%W"))
        year = date_time.year
        month = date_time.month
        begin = int(datetime(year, month, 1).strftime("%W"))
        return end - begin + 1

    @staticmethod
    def getStatDate(date_time):
        """
        获取日期年月日拼接成的整数。

        Parameters:
          date_time - 日期时间

        Returns:
          日期年月日拼接成的整数，例如：20180622。

        Raises:
          KeyError - raises an exception
        """
        year = date_time.year
        month = date_time.month
        day = date_time.day
        stat_date = year * 10000 + month * 100 + day
        return stat_date

    @staticmethod
    def formatDate(date_time, format=DTF):
        '''
        使用%Y-%m-%d格式化日期时间，返回日期。

        Parameters
          date_time - 日期时间

        Returns
          格式化后的日期字符串，例如：2018-06-22
        '''
        try:
            return datetime.strftime(date_time, format)
        except Exception:
            return ''

    @staticmethod
    def parseDateTime(text, format=DF):
        '''
        解析时间。

        Parameters
          text - 时间字符串
          format - 时间格式字符串

        Returns
          日期时间
        '''
        try:
            if text is not None and text.strip() != '':
                return datetime.strptime(text, format)
            else:
                return None
        except Exception:
            return None

    @staticmethod
    def getCostTimeMs(begin_time, end_time):
        '''
        获取消耗时间毫秒数

        Parameters
          begin_time - 开始时间，datetime
          end_time - 结束时间，datetime

        Returns
            消耗时间毫秒数，int
        '''
        cost_time = 0
        if begin_time is not None and end_time is not None:
            t = (end_time - begin_time).microseconds
            print(t)
            cost_time = int(round(t / 1000))
        return cost_time

    @staticmethod
    def getDayBetween(date_time):
        '''
        获取指定日期00:00:00到23:59:59时间范围

        Parameters
          date_time - 日期，可以是日期时间或者字符串类型，字符串格式：%Y-%m-%d，举例：2018-06-22。

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        date_text = None
        if type(date_time) == str:
            date_text = date_time
        else:
            date_text = datetime.strftime(date_time, DTF)
        begin_time = datetime.strptime(date_text + " 00:00:00", DF)
        end_time = datetime.strptime(date_text + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def getLastDaysBetween(days):
        '''
        最近days天时间范围。

        Parameters
          days - int，最近天数

        Returns
          开始时间和结束时间元祖(begin_time, end_time)。
        '''
        end_date = datetime.now()
        bengin_date = end_date - timedelta(days=days)
        begin_text = datetime.strftime(bengin_date, DTF)
        end_text = datetime.strftime(end_date, DTF)
        begin_time = datetime.strptime(begin_text + " 00:00:00", DF)
        end_time = datetime.strptime(end_text + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def getWeekBetween(date_time):
        '''
        获取指定日期00:00:00到23:59:59时间范围

        Parameters
          date_time - 日期，可以是日期时间或者字符串类型，字符串格式：%Y-%m-%d，举例：2018-06-22。

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = None
        if type(date_time) == str:
            now = datetime.strptime(date_time, DTF)
        else:
            now = date_time

        days = now.weekday()
        begin = now - timedelta(days=days)
        start_date = datetime.strftime(begin, DTF)
        end_date = datetime.strftime(now, DTF)
        begin_time = datetime.strptime(start_date + " 00:00:00", DF)
        end_time = datetime.strptime(end_date + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def getMonthBetween(date_time):
        '''
        获取指定日期00:00:00到23:59:59时间范围

        Parameters
          date_time - 日期，可以是日期时间或者字符串类型，字符串格式：%Y-%m-%d，举例：2018-06-22。

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = None
        if type(date_time) == str:
            now = datetime.strptime(date_time, DTF)
        else:
            now = date_time

        year = now.year
        month = now.month
        begin_text = str(year) + '-' + str(month) + '-1'
        end_text = datetime.strftime(now, DTF)
        begin_time = datetime.strptime(begin_text + " 00:00:00", DF)
        end_time = datetime.strptime(end_text + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def thisMonthRange():
        '''
        本月时间范围

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = datetime.now()
        year = now.year
        month = now.month
        begin_text = str(year) + '-' + str(month) + '-1'
        end_text = datetime.strftime(now, DTF)
        begin_time = datetime.strptime(begin_text + " 00:00:00", DF)
        end_time = datetime.strptime(end_text + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def thisMonthStatRange():
        '''
        本月统计时间范围

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        begin_time = year * 10000 + month * 100 + 1
        end_time = year * 10000 + month * 100 + day
        return (begin_time, end_time)

    @staticmethod
    def thisWeekRange():
        '''
        本周时间范围

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = datetime.now()
        days = now.weekday()
        begin = now - timedelta(days=days)
        start_date = datetime.strftime(begin, DTF)
        end_date = datetime.strftime(now, DTF)
        begin_time = datetime.strptime(start_date + " 00:00:00", DF)
        end_time = datetime.strptime(end_date + " 23:59:59", DF)
        return (begin_time, end_time)

    @staticmethod
    def thisWeekStatRange():
        '''
        本周统计时间范围

        Returns
          开始时间和结束时间元祖(begin_time, end_time)
        '''
        now = datetime.now()
        days = datetime.date.today().weekday()
        begin = now - timedelta(days=days)
        year = begin.year
        month = begin.month
        day = begin.day
        begin_time = year * 10000 + month * 100 + day
        end_time = now.year * 10000 + now.month * 100 + now.day
        return (begin_time, end_time)

    @staticmethod
    def last15DaysStatRange():
        '''
        最近15天统计时间范围。

        Returns
          开始时间和结束时间元祖(begin_time, end_time)。
        '''
        e = datetime.now()
        b = e - timedelta(days=15)
        begin_time = b.year * 10000 + b.month * 100 + b.day
        end_time = e.year * 10000 + e.month * 100 + e.day
        return (begin_time, end_time)

    @staticmethod
    def lastDaysStatRange(days):
        '''
        最近days天统计时间范围。

        Parameters
          days - int，最近天数

        Returns
          开始时间和结束时间元祖(begin_time, end_time)。
        '''
        e = datetime.now()
        b = e - timedelta(days=days)
        begin_time = b.year * 10000 + b.month * 100 + b.day
        end_time = e.year * 10000 + e.month * 100 + e.day
        return (begin_time, end_time)
