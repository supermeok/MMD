import wikipedia  # 需要 pip install wikipedia

def get_page_obs(page):
    # find all paragraphs
    paragraphs = page.split("\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # find all sentence
    sentences = []
    for p in paragraphs:
        sentences += p.split('. ')
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    return ' '.join(sentences[:5])


def search_step(entity):
    try:
        page_details = wikipedia.page(entity, auto_suggest=False)

        # 获取页面内容
        content = page_details.content

        # 过滤掉过短的行（比如标题、空行）
        # 原代码有 len(p.split(" ")) > 2 的判断
        page_re = ""
        for p in content.split("\n"):
            if len(p.split(" ")) > 2:
                page_re += p
                if not p.endswith("\n"):
                    page_re += "\n"

        obs = get_page_obs(page_re)

    except wikipedia.DisambiguationError as e:
        # 处理歧义页面 (对应原代码中的 result_divs 分支)
        # e.options 包含了类似的词条列表
        options = e.options[:5]
        obs = f"Could not find {entity}. Similar: {options}."

    except wikipedia.PageError:
        # 处理页面未找到
        obs = f"Could not find {entity}."

    except Exception as e:
        # 处理连接超时或其他网络错误
        obs = f"Could not find {entity}."

    return obs


def clean_data(output):
    output = output.split('.')[0].strip()
    output = output.replace('\\u00e9', 'e')
    output = output.replace('\u00e1', 'a')
    output = output.replace(' and ', ', ')
    output = output.replace('The ', '')
    output = output.replace('the ', '')
    output = output.replace('A ', '')
    output = output.replace(' two', '')
    output = output.replace('Two', '')
    output = output.replace('Two ', '')
    output = output.replace('Three ', '')
    output = output.replace(' a ', '')
    output = output.replace('An ', '')
    output = output.replace(' an ', '')
    output = output.replace('\"', '')
    output = output.split(', ')[0]
    char_num = len(output.split(' '))
    if char_num > 5:
        output = ''
    return output.lower()


def search_wiki_knowledge(output):
    if 'Thought 2' in output:
        output = output.split('Thought 2')[0].strip()

    if 'Finish:' in output:
        entity = output.split('Finish:')[1]
        entity = clean_data(entity)

        if entity == '':
            knowledge = ''
        else:
            knowledge = search_step(entity)
            if 'Could not find' in knowledge:
                knowledge = ''
    else:
        entity = ''
        knowledge = ''

    return entity, knowledge