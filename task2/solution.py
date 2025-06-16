import sys
import asyncio
import requests
import aiohttp
from bs4 import BeautifulSoup
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Iterable
import contextvars

# Сделал функцию переиспользуемой - её можно сразу применять
# к другим страницам подобного типа (которые построены по алфвавитному шаблону википедии)
# Работает для тех страниц, которые поддерживают побуквенную ориентацию
# По поводу контекстного менеджера Kwargs - во время тестирования можно использовать
# прокси-сервер с авторотацией для ускорения работы, он применялся во время написания.

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


current_session_args = contextvars.ContextVar("current_session_args")


class Kwargs:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._token = None

    def __enter__(self):
        self._token = current_session_args.set(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        current_session_args.reset(self._token)


@dataclass
class ABCTypePage:
    entries: List[str]
    next_page_url: Optional[str]


@dataclass
class ABCTypeParseArgs:
    title: str
    next_page_text: str
    title_class: str = "h2"
    list_class: str = "mw-category mw-category-columns"


async def get_response_text(session: aiohttp.ClientSession, url: str) -> str:
    kwargs = current_session_args.get(Kwargs())
    async with session.get(url, **kwargs.kwargs) as resp:
        return await resp.text()


async def get_abctype_linktext(session: aiohttp.ClientSession, url: str, parse_args: ABCTypeParseArgs) -> ABCTypePage:
    html_text = await get_response_text(session, url)
    html = BeautifulSoup(html_text, "html.parser")

    mw_pages = html.find_all("div", {"id": "mw-pages"})
    page = None
    for mw_page in mw_pages:
        title_element = mw_page.find_all(parse_args.title_class)
        for title_ in title_element:
            if title_.text == parse_args.title:
                page = mw_page
                break
        if page:
            break

    if not page:
        raise ValueError("Parse error")

    list_elements = page.findNext("div", {"class": parse_args.list_class})
    entries = [a["title"] for a in list_elements.find_all("a")]

    next_page_url = next(
        (a["href"] for a in page.findAllNext("a") if a.text == parse_args.next_page_text),
        None,
    )
    if next_page_url:
        next_page_url = requests.compat.urljoin(url, next_page_url)

    return ABCTypePage(entries, next_page_url)


async def get_abctype_all(session: aiohttp.ClientSession, url_type: str, char: str,
                          parse_args: ABCTypeParseArgs) -> ABCTypePage:
    entries = []
    url = url_type.format(char)
    result = await get_abctype_linktext(session, url, parse_args)
    collected = False
    break_next = False

    while True:
        for entry in result.entries:
            if entry.startswith(char):
                entries.append(entry)
                break_next = False
                collected = False
            else:
                collected = True
        if collected or not result.next_page_url:
            break
        result = await get_abctype_linktext(session, result.next_page_url, parse_args)
        if break_next:
            break

    return ABCTypePage(entries, None)


async def collect_entries(url_type: str, alphabet: str, parse_args: ABCTypeParseArgs, max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for char in alphabet:
            async def limited_fetch(ch=char):
                async with semaphore:
                    return await get_abctype_all(session, url_type, ch, parse_args)

            tasks.append(limited_fetch())

        return await asyncio.gather(*tasks)


def get_counted_dict(page_data: Iterable[ABCTypePage]) -> dict[str, int]:
    return {page.entries[0][0]: len(page.entries) for page in page_data if page.entries}


def create_file(path: str, counted_dict: dict[str, int]) -> str:
    with open(path, "w", encoding="utf-8") as f:
        for char, count in sorted(counted_dict.items()):
            f.write(f"{char},{count}\n")
    return path


async def collect_file(url_type: str, alphabet: str, parse_args: ABCTypeParseArgs,
                       max_concurrent: int = 10, path: str | Path = "result.csv"):
    result = await collect_entries(url_type, alphabet, parse_args, max_concurrent)
    counted_dict = get_counted_dict(result)
    return create_file(path, counted_dict)


def main():
    url = "https://ru.wikipedia.org/w/index.php?title=Категория:Животные_по_алфавиту&from={}"
    title = "Страницы в категории «Животные по алфавиту»"
    alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
    parse_args = ABCTypeParseArgs(title=title, next_page_text="Следующая страница")

    requests_kwargs = {}
    if len(sys.argv) > 1:
        proxy = sys.argv[1]
        requests_kwargs["proxy"] = proxy

    with Kwargs(**requests_kwargs):
        asyncio.run(collect_file(url, alphabet, parse_args, path="beasts.csv", max_concurrent=20))


if __name__ == "__main__":
    main()
