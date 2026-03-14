import time

import requests
from bs4 import BeautifulSoup


def clean_str(value: str) -> str:
    return value.encode().decode("unicode-escape").encode("latin1").decode("utf-8")


def get_page_obs(page: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in page.split("\n") if paragraph.strip()]

    sentences: list[str] = []
    for paragraph in paragraphs:
        sentences.extend(paragraph.split(". "))

    cleaned_sentences = [sentence.strip() + "." for sentence in sentences if sentence.strip()]
    return " ".join(cleaned_sentences[:5])


def search_step(entity: str, max_retries: int = 2) -> str:
    entity_query = entity.replace(" ", "+")
    search_url = f"https://en.wikipedia.org/w/index.php?search={entity_query}"

    response_text = ""
    for _ in range(max_retries):
        try:
            session = requests.session()
            session.keep_alive = False
            response = session.get(search_url, timeout=(5, 5))
            response_text = response.text
            response.close()
            break
        except requests.RequestException:
            time.sleep(1)

    if not response_text:
        return ""

    soup = BeautifulSoup(response_text, features="html.parser")
    result_divs = soup.find_all("div", {"class": "mw-search-result-heading"})

    if result_divs:
        result_titles = [clean_str(div.get_text().strip()) for div in result_divs]
        return f"Could not find {entity}. Similar: {result_titles[:5]}."

    page = [p.get_text().strip() for p in soup.find_all("p") + soup.find_all("ul")]
    if any("may refer to:" in paragraph for paragraph in page):
        return search_step(f"[{entity}]")

    page_result = ""
    for paragraph in page:
        if len(paragraph.split(" ")) > 2:
            page_result += clean_str(paragraph)
            if not paragraph.endswith("\n"):
                page_result += "\n"
    return get_page_obs(page_result)


def clean_data(output: str) -> str:
    output = output.split(".")[0].strip()
    output = output.replace("\\u00e9", "e")
    output = output.replace("\u00e1", "a")
    output = output.replace(" and ", ", ")
    output = output.replace("The ", "")
    output = output.replace("the ", "")
    output = output.replace("A ", "")
    output = output.replace(" two", "")
    output = output.replace("Two", "")
    output = output.replace("Two ", "")
    output = output.replace("Three ", "")
    output = output.replace(" a ", "")
    output = output.replace("An ", "")
    output = output.replace(" an ", "")
    output = output.replace('"', "")
    output = output.split(", ")[0]
    if len(output.split(" ")) > 5:
        return ""
    return output.lower()


def search_wiki_knowledge(output: str) -> tuple[str, str]:
    if "Thought 2" in output:
        output = output.split("Thought 2", 1)[0].strip()

    if "Finish:" not in output:
        return "", ""

    entity = clean_data(output.split("Finish:", 1)[1])
    if not entity:
        return "", ""

    knowledge = search_step(entity)
    if not knowledge or "Could not find" in knowledge:
        knowledge = ""

    return entity, knowledge
