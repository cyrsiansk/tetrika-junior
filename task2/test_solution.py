import pytest
import os
from solution import collect_file, ABCTypeParseArgs

ALPHABET = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"


@pytest.mark.asyncio
@pytest.mark.parametrize("url_type,title_text", [
    ("https://ru.wikipedia.org/w/index.php?title=Категория:Животные_по_алфавиту&from={}",
     "Страницы в категории «Животные по алфавиту»"),
    ("https://ru.wikipedia.org/w/index.php?title=Категория:Фигуристы_по_алфавиту&from={}",
     "Страницы в категории «Фигуристы по алфавиту»"),
    ("https://ru.wikipedia.org/w/index.php?title=Категория:Растения_по_алфавиту&from={}",
     "Страницы в категории «Растения по алфавиту»"),
])
async def test_collect_file_creates_output_file(url_type, title_text, tmp_path):
    parse_args = ABCTypeParseArgs(
        title=title_text,
        next_page_text="Следующая страница"
    )
    output_file = tmp_path / "test_result.csv"

    try:
        path = await collect_file(
            url_type, ALPHABET, parse_args,
            max_concurrent=5, path=str(output_file)
        )
    except Exception as e:
        pytest.fail(f"Скрипт завершился с ошибкой: {e}")

    assert os.path.exists(path), "Файл не создан"
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert all("," in line for line in lines), "Некорректный формат строк"
        assert all(line.split(",")[0].strip() in ALPHABET for line in lines), "Есть строки вне алфавита"
        assert all(line.strip().split(",")[1].isdigit() for line in lines), "Вторая часть строки не число"


@pytest.mark.asyncio
async def test_invalid_url_fails(tmp_path):
    parse_args = ABCTypeParseArgs(
        title="Несуществующая категория",
        next_page_text="Следующая страница"
    )
    broken_url = "https://ru.wikipedia.org/w/index.php?title=Категория:Несущестующая_категория&from={}"

    with pytest.raises(Exception):
        await collect_file(broken_url, ALPHABET, parse_args, max_workers=3, path=tmp_path / "invalid.csv")
