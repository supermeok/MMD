import wikipedia
import socket

# ========== 你的原函数（保持不变） ==========
def get_page_obs(page):
    paragraphs = page.split("\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    sentences = []
    for p in paragraphs:
        sentences += p.split('. ')
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    return ' '.join(sentences[:5])


def search_step(entity):
    try:
        # 设置超时，防止无限卡住（10秒）
        socket.setdefaulttimeout(10)
        page_details = wikipedia.page(entity, auto_suggest=False)
        content = page_details.content

        page_re = ""
        for p in content.split("\n"):
            if len(p.split(" ")) > 2:
                page_re += p
                if not p.endswith("\n"):
                    page_re += "\n"

        obs = get_page_obs(page_re)

    except wikipedia.DisambiguationError as e:
        options = e.options[:5]
        obs = f"Could not find {entity}. Similar: {options}."

    except wikipedia.PageError:
        obs = f"Could not find {entity}."

    except Exception as e:
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


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("=== Wikipedia 搜索测试 ===\n")

    # 测试用例列表：每个元素为 (描述, 输入字符串)
    test_cases = [
        ("1. 正常实体（如 Python）", "Some text before. Finish: Python programming language."),
        ("2. 歧义实体（如 Apple）", "Finish: Apple"),
        ("3. 不存在的实体（如 Asdfghjklzxcvbnm）", "Finish: Asdfghjklzxcvbnm"),
        ("4. 无 Finish 标记", "This is just a sentence without finish."),
        ("5. 包含 Thought 2 标记", "Thought 1... Thought 2... Finish: Albert Einstein"),
        ("6. 实体为空", "Finish:  "),
    ]

    for desc, input_str in test_cases:
        print(f"\n{desc}")
        print(f"输入: {input_str!r}")
        try:
            entity, knowledge = search_wiki_knowledge(input_str)
            print(f"提取的实体: {entity!r}")
            if knowledge:
                # 打印前200个字符避免过长
                print(f"知识摘要 (前200字符): {knowledge[:200]}...")
            else:
                print("知识摘要: 无")
        except Exception as e:
            print(f"测试过程中出现异常: {e}")

    print("\n=== 测试完成 ===")
    print("如果某个测试卡住超过10秒，请检查网络连接或代理设置。")