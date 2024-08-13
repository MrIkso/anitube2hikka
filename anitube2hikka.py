import argparse
import sys

import requests
from bs4 import BeautifulSoup

user_agent = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile "
              "Safari/537.36")
hikka_api = "https://api.hikka.io/"
success_added_count: int = 0
falied_added_count: int = 0


def main(argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='anitube2hikka - конвертер закладок з Anitube.in.ua на сайт hikka.io')
    parser.add_argument('--username', type=str, help="Ім'я на anitube.in.ua")
    parser.add_argument('--token', type=str, help="Введіть ваш token з сайту hikka.io")

    opts = parser.parse_args(argv)
    start_convert(opts.username, opts.token)


def is_json_key_present(json, key):
    try:
        json[key]
    except KeyError:
        return False

    return True


def start_convert(user_name, token):
    lists_for_search = [
        'seen',
        'will',
        'watch',
        'poned',
        'aband'
    ]

    user_lists = {
        'seen': [],
        'will': [],
        'watch': [],
        'poned': [],
        'aband': [],
    }

    for watch_page in lists_for_search:
        data = get_user_lists(user_name, 1, watch_page)
        user_lists.get(watch_page).append(data)

    print(user_lists)

    for key in user_lists:
        search_and_add_to_list(key,user_lists[key], token)

    print(f"Успішно додано: {success_added_count}, не вдалося додати: {falied_added_count}")


def search_and_add_to_list(anime_name, anime_status, token):
    global success_added_count, falied_added_count

    print(f"Шукаємо: {anime_name}")
    # Параметри запиту (query parameters)
    query_params = {
        'size': '30'
    }
    headers = {
        "auth": f"{token}",
    }
    search_data = {
        "query": f"{anime_name}"
    }

    search_request = requests.post(f"{hikka_api}/anime", params=query_params, json=search_data)

    json_data = search_request.json()

    # print(json_data)

    if is_json_key_present(json_data, 'list'):
        json_list = json_data.get('list')
        if json_list:
            # беремо перший елемент з пошуку і беремо його slug
            hikka_slug = json_list[0]["slug"]
            print(f"Знайдено: {hikka_slug}")

            watch_data = {
                "note": "",
                "episodes": 0,
                "rewatches": 0,
                "score": 0,
                "status": f"{convert_anitube2hikka_status(anime_status)}"
            }

            requests.put(f"{hikka_api}/watch/{hikka_slug}", headers=headers, json=watch_data)
            success_added_count += 1
        else:
            print(f"Аніме за назвою: {anime_name} не було знайдено! Ви можете "
                  f"знайти його на сайті вручну, та додати самотушки")
            falied_added_count += 1
    else:
        print(f"Аніме за назвою: {anime_name} не було знайдено! Ви можете "
              f"знайти його на сайті вручну, та додати самотушки")
        falied_added_count += 1


def convert_anitube2hikka_status(status: str):
    if "watch" in status:
        return "watching"
    elif "will" in status:
        return "planned"
    elif "seen" in status:
        return "completed"
    elif "poned" in status:
        return "on_hold"
    elif "aband" in status:
        return "dropped"


def get_user_lists(user_name: str, page: int, watch_page: str) -> list:
    headers = {
        'user-agent': user_agent
    }
    anime_list = []
    while True:
        built_url = f"https://anitube.in.ua/mylists/{user_name}/{watch_page}/page/{page}"
        print(built_url)

        response = requests.get(url=built_url, headers=headers)

        soup = BeautifulSoup(response.content, 'html.parser')

        anime_pages = soup.findAll('div', class_='short-in')

        for anime in anime_pages:
            short_title = anime.find('a', class_='short-title')

            url_of_page = short_title.get('href')
            name_of_page = short_title.find('img').get("alt").strip()
            print(f"{url_of_page} -> {name_of_page}")
            anime_data = {
                'name': name_of_page,
                'link': url_of_page
            }

            anime_list.append(anime_data)

        navigation_span = soup.find('span', class_='navigation')
        if navigation_span is not None:
            page_numbers = []
            for link in navigation_span.findAll("a"):
                page_part = link.get('href').split('/')[-2]

                if page_part.isdigit():
                    page_numbers.append(int(page_part))

            max_page = max(page_numbers) if page_numbers else page

            if page >= max_page:
                break
            else:
                page += 1
        else:
            break

    return anime_list


if __name__ == '__main__':
    main(sys.argv[1:])
