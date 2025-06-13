from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import contextvars
from concurrent.futures import ThreadPoolExecutor, as_completed


# Сделал функцию переиспользуемой - её можно сразу применять
# к другим страниц подобного типа (которые построены по алфвавитному шаблону википедии)
# Работает для тех страниц, которые поддерживают побуквенную ориентацию
# По поводу контекстного менеджера Kwargs - во время тестирования можно использовать
# прокси-сервер с авторотацией для ускорения работы, он применялся во время написания.


current_response_args = contextvars.ContextVar("current_response_args")


class Kwargs:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._token = None

    def __enter__(self):
        self._token = current_response_args.set(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        current_response_args.reset(self._token)


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


def get_response_text(url: str):
    kwargs = current_response_args.get(Kwargs())
    return requests.get(url, **kwargs.kwargs)


def get_abctype_linktext(url: str, parse_args: ABCTypeParseArgs) -> ABCTypePage:
    response = get_response_text(url)
    html = BeautifulSoup(response.text, "html.parser")

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
        (a["href"] for a in page.findAllNext("a")  # NOQA
         if a.text == parse_args.next_page_text),
        None,
    )

    if next_page_url:
        next_page_url = requests.compat.urljoin(url, next_page_url)  # NOQA

    return ABCTypePage(entries, next_page_url)


def get_abctype_all(url_type: str, char: str, parse_args: ABCTypeParseArgs) -> ABCTypePage:
    entries = []
    url = url_type.format(char)
    result = get_abctype_linktext(url, parse_args)
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
        if collected:
            break_next = True
        if not result.next_page_url:
            break
        result = get_abctype_linktext(result.next_page_url, parse_args)

        if break_next:
            break

    return ABCTypePage(entries, None)


def collect_entries(url_type: str, alphabet: str, parse_args: ABCTypeParseArgs,
                    max_workers: int = 10):
    result = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(contextvars.copy_context().run, get_abctype_all, url_type, char, parse_args)  # NOQA
            for char in alphabet
        ]
        result.extend(future.result() for future in as_completed(futures))
    return result


def get_counted_dict(page_data: List[ABCTypePage]) -> dict[str, int]:
    return {page.entries[0][0]: len(page.entries) for page in page_data}


def create_file(path: str, counted_dict: dict[str, int]) -> str:
    with open(path, "w", encoding="utf-8") as f:
        for char, count in sorted(counted_dict.items()):
            f.write(f"{char},{count}\n")
    return path


def collect_file(url_type: str, alphabet: str, parse_args: ABCTypeParseArgs,
                 max_workers: int = 10, path: str | Path = "result.csv"):
    result = collect_entries(url_type, alphabet, parse_args, max_workers)
    counted_dict = get_counted_dict(result)
    return create_file(path, counted_dict)


def main():
    url = "https://ru.wikipedia.org/w/index.php?title=Категория:Животные_по_алфавиту&from={}"
    title = "Страницы в категории «Животные по алфавиту»"
    alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
    parse_args = ABCTypeParseArgs(title=title, next_page_text="Следующая страница")
    collect_file(url, alphabet, parse_args, path="beasts.csv", max_workers=20)


if __name__ == "__main__":
    main()
