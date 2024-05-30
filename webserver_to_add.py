from aiohttp import web
import aiohttp


async def handle(request):
    user_agent = request.headers.get('User-Agent')
    cook = request.cookies.get('user_id')
    response = web.Response(text="Hello")

    await send_tracking_request(cookies=cook, user_agent=user_agent, get_response=response)
    return response


async def send_tracking_request(cookies, user_agent, get_response):
    url = 'http://0.0.0.0:8080'

    headers = {
        'Cookies': f'{cookies}',
        'User-Agent': f'{user_agent}'
    }

    async with aiohttp.ClientSession(headers=headers, cookies={'user_id': f'{cookies}'}) as session:
        async with session.get(url) as response:

            new_cookies = response.cookies
            # Обработка ответа
            if response.status == 200:
                print('Успешно отправлено трекинг-событие')
            else:
                print(f'Не удалось отправить трекинг-событие {response.status} ')

    if cookies:
        pass
    else:
        cook = new_cookies
        get_response.set_cookie('user_id', cook)


app = web.Application()
app.router.add_get('/', handle)

if __name__ == '__main__':
    web.run_app(app)
