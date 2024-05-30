from aiohttp import web
from webserver import handle, get_stats, get_unique_stats

app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/stats', get_stats)
app.router.add_get('/unistats', get_unique_stats)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)