import calendar as cal
import datetime as dt
import locale
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun
from dateutil.rrule import rrule, WEEKLY
from pyluach import dates, utils

locale.setlocale(locale.LC_ALL, "he_IL.UTF-8")

tz = ZoneInfo("Asia/Jerusalem")
city = LocationInfo("Tel Aviv", "Center", "Asia/Jerusalem", 32.109333, 34.855499)


@dataclass
class Event:
    id: str
    name: str
    dates: Iterator[dt.datetime]


def month_dates(year: int, month: int) -> list[list[dt.date]]:
    return cal.Calendar(firstweekday=cal.SUNDAY).monthdatescalendar(year, month)


def week_dates(week: list[dt.date]) -> list[tuple[dt.date, dates.HebrewDate]]:
    return map(lambda date: (date, dates.HebrewDate.from_pydate(date)), week)


def week_days() -> list[str]:
    return list(utils.WEEKDAYS.values())


def span_format(span: list[tuple[str, str]]) -> str:
    month1, year1 = span[0]
    if len(span) == 1:
        return f"{month1} {year1}"

    month2, year1 = span[1]
    if year1 == year1:
        return f"{sm(month1)} - {sm(month2)} {sy(year1)}"
    else:
        return f"{sm(month1)} {sy(year1)} - {month2} {year1}"


sm = lambda text: f"<span class='month'>{text}</span>"
sy = lambda text: f"<span class='year'>{text}</span>"

dg = lambda text: f"<div class='gregorian'>{text}</div>"
dh = lambda text: f"<div class='hebrew'>{text}</div>"


def cal_month(
    year: int,
    month: int,
    today: dt.date = dt.date.today(),
    events: list[Event] | None = None,
):
    event_dates = defaultdict(list)
    for event in events or []:
        for date in event.dates:
            event_dates[date.date()].append(event)

    span = {}

    html = []
    a = html.append
    e = html.extend
    i = html.insert

    a("<table>")

    a("<caption>")
    a(dg("%s %s" % (sm(cal.month_name[month]), sy(year))))
    a("</caption>")

    a("<colgroup>")
    e(f"<col class='day-{i}' />" for i in range(1, 8))
    a("</colgroup>")

    a("<thead>")
    a("<tr>")
    e(f"<th scope='col'>{day}</th>" for day in week_days())
    a("</tr>")
    a("</thead>")

    a("<tbody>")
    for month_week in month_dates(year, month):
        a("<tr>")
        for date, heb_date in week_dates(month_week):
            if date.month == month:
                span[(f"{heb_date:%*B}", f"{heb_date:%*y}")] = True
                today_attr = " data-today" if date == today else ""

                a(f"<td{today_attr}>")
                a(f"<div>{dg(date.day)}{dh(f'{heb_date:%*d}')}</div>")

                a("<div class='events'>")
                if holiday := heb_date.holiday(hebrew=True):
                    a(f"<div>{holiday}</div>")

                if date in event_dates:
                    for event in event_dates[date]:
                        a(f"<div data-id='{event.id}'>{event.name}</div>")
                a("</div>")

                if date.weekday() == 4:
                    sun_info = sun(city.observer, date=date, tzinfo=tz)
                    candle_lighting = sun_info["sunset"] - dt.timedelta(minutes=30)
                    a(
                        f"<div class='candle-lighting'>{candle_lighting.strftime('%H:%M')}</div>"
                    )

                elif date.weekday() == 5:
                    sun_info = sun(city.observer, date=date, tzinfo=tz)
                    havdalah = sun_info["sunset"] + dt.timedelta(minutes=40)
                    a(f"<div class='havdalah'>{havdalah.strftime('%H:%M')}</div>")

                a("</td>")
            else:
                a("<td></td>")
        a("</tr>")
    a("</tbody>")

    a("</table>")

    # after gregorian month name
    i(3, dh(span_format(list(span))))

    return "\n".join(html)


def render_html(body: str) -> str:
    with open("base.html") as fp:
        return fp.read().format(body=body)


today = dt.date.today()
events = [
    Event(
        "test",
        "דוגמה",
        rrule(freq=WEEKLY, count=5, dtstart=today, byhour=12, byweekday=[6, 0]),
    )
]

print(render_html(cal_month(today.year, today.month, today, events)))
