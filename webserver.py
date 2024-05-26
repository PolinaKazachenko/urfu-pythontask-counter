import sqlite3
from aiohttp import web
import requests
import uuid

conn = sqlite3.connect('visits.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY,
        ip TEXT NOT NULL,
        country TEXT,
        browser TEXT,
        user_id NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')


async def handle(request):
    ip = request.remote
    get_id = requests.get(url=f'http://ip-api.com/json/{ip}').json()
    print(get_id)
    user_agent = request.headers.get('User-Agent')
    browser = check_browsers(user_agent)
    country = get_id['country']
    html_data = get_html_data_handle()
    response_data = web.Response(text=html_data, headers={'Content-Type': 'text/html'})
    user_id_cookie = request.cookies.get('user_id')
    user_id = get_set_cookie(user_id_cookie, response_data)
    insert_data_base(ip, country, browser, user_id)
    return response_data


async def get_stats(request):
    sql_queries = {
        'day': "SELECT COUNT(*) FROM visits WHERE DATE(timestamp) = DATE('now')",
        'month': "SELECT COUNT(*) FROM visits WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')",
        'year': "SELECT COUNT(*) FROM visits WHERE strftime('%Y', timestamp) = strftime('%Y', 'now')",
        'total': "SELECT COUNT(*) FROM visits"

    }
    countries = {}
    with conn:
        c.execute("SELECT country, COUNT(*) as count FROM visits WHERE country IS NOT NULL GROUP BY country")
        rows = c.fetchall()
    for row in rows:
        country = row[0]
        count = row[1]
        countries[country] = count
    browsers = {}
    with conn:
        c.execute("SELECT browser, COUNT(*) as count FROM visits GROUP BY browser")
        rows = c.fetchall()
    for row in rows:
        browser = row[0]
        count = row[1]
        browsers[browser] = count
    values = get_stats_values(sql_queries)
    link = 'http://0.0.0.0:8080/'
    link_text = 'Вернуться назад'
    text_data = f"Number of visits this day: {values.get('day')}\n" \
                f"Number of visits this month: {values.get('month')}\n" \
                f"Number of visits this year: {values.get('year')}\n" \
                f"Number of visits this total: {values.get('total')}\n\n"
    for country, count in countries.items():
        text_data += f"Number of visits from {country}: {count}\n"
    for browser, count in browsers.items():
        text_data += f"Number of visits with browser - {browser}: {count}\n"
    html_data = (f'<html></head><body style="background-color: #161616;color: #DCDCDC;"><pre style="word-wrap: '
                 f'break-word; white-space: pre-wrap;">{text_data}</pre><a style = "color: #DCDCDC;" href="{link}">{
                 link_text}</a></body></html>')
    return web.Response(text=html_data, headers={'Content-Type': 'text/html'})


async def get_unique_stats(request):
    sql_queries = {
        'unique_day': "SELECT COUNT(DISTINCT user_id) FROM visits WHERE DATE(timestamp) = DATE('now')",
        'unique_month': "SELECT COUNT(DISTINCT user_id) FROM visits WHERE strftime('%Y-%m', timestamp) = strftime("
                        "'%Y-%m', 'now')",
        'unique_year': "SELECT COUNT(DISTINCT user_id) FROM visits WHERE strftime('%Y', timestamp) = strftime('%Y', "
                       "'now')",
        'unique_total': "SELECT COUNT(DISTINCT user_id) FROM visits"
    }
    values = get_stats_values(sql_queries)
    html_data = get_html_data_unique_stats(values)
    return web.Response(text=html_data, headers={'Content-Type': 'text/html'})


def get_stats_values(sql_queries):
    values = {'day': None, 'month': None, 'year': None, 'total': None}
    with conn:
        for query_name, query in sql_queries.items():
            c.execute(query)
            count = c.fetchone()[0]
            values[query_name] = count
    return values


def generate_unique_id():
    return str(uuid.uuid4())


def insert_data_base(ip, country, browser, user_id):
    with conn:
        c.execute("INSERT INTO visits (ip, country,  browser, user_id) VALUES (?, ?, ?, ?)",
                  (ip, country, browser, user_id))


def get_html_data_handle():
    link_stats = 'http://0.0.0.0:8080/stats'
    link_text_stats = 'Get stats\n'
    link_unique_stats = 'http://0.0.0.0:8080/unistats'
    link_text_unique_stats = 'Get unique stats'
    text_data = "Hello,\n" \
                "If you want to see counter - use /stats\n" \
                "If you want to see unique counter" \
                " - use /unistats\n"
    html_data = f'<html></head><body style="background-color: #161616;color: #DCDCDC;">' \
                f'<pre style="word-wrap: break-word; white-space: pre-wrap;">{text_data}</pre>' \
                f'<a style = "color: #DCDCDC;"href="{link_stats}">{link_text_stats}</a><br>' \
                f'<a style = "color: #DCDCDC;" href="{link_unique_stats}">{link_text_unique_stats}</a></body></html> '
    return html_data


def get_html_data_unique_stats(values):
    link = 'http://0.0.0.0:8080/'
    link_text = 'Вернуться назад'
    text_data = f"Number of visits this day: {values.get('unique_day')}\n" \
                f"Number of visits this month: {values.get('unique_month')}\n" \
                f"Number of visits this year: {values.get('unique_year')}\n" \
                f"Number of visits this total: {values.get('unique_total')}\n"
    html_data = f'<html></head><body style="background-color: #161616;color: #DCDCDC;"><pre style="word-wrap: ' \
                f'break-word; white-space: pre-wrap;">{text_data}</pre><a style = "color: #DCDCDC;" href="{link}">{link_text}</a></body></html> '
    return html_data


def check_browsers(user_agent):
    if 'OPR' in user_agent:
        browser = 'Opera'
    elif 'YaBrowser' in user_agent:
        browser = 'Yandex'
    elif 'Edg' in user_agent:
        browser = 'Microsoft Edge'
    elif 'Chrome' in user_agent:
        browser = 'Google Chrome'
    elif 'Safari' in user_agent:
        browser = 'Apple Safari'
    else:
        browser = 'Unknown browsers'
    return browser


def get_set_cookie(user_id_cookie, response_data):
    if user_id_cookie == "None":
        user_id_cookie = None
    if user_id_cookie:
        user_id = user_id_cookie
    else:
        user_id = generate_unique_id()
        response_data.set_cookie('user_id', user_id)
    return user_id
