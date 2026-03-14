from utils.qwen_api_utis import QwenVLAPI,call_qwen_vl_api,call_qwen_text_api
from utils.weiki_search import search_wiki_knowledge

def clean_data(answer):
    """清理输出文本"""
    answer = answer.replace("\n", " ")
    answer = answer.replace("\t", " ")
    answer = answer.strip()
    return answer


def parse_debate_verdict(judge_output):
    """解析辩论法官的输出"""
    result = {
        'verdict': 'True',
        'category': 'original',
        'confidence': 0,
        'reasoning': ''
    }

    lines = judge_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith('verdict:'):
            verdict_str = line.split(':', 1)[1].strip().lower()
            result['verdict'] = 'Fake' if 'fake' in verdict_str else 'True'
        elif line.lower().startswith('category:'):
            category_str = line.split(':', 1)[1].strip().lower()
            if 'textual' in category_str:
                result['category'] = 'textual_veracity_distortion'
            elif 'visual' in category_str:
                result['category'] = 'visual_veracity_distortion'
            elif 'mismatch' in category_str:
                result['category'] = 'mismatch'
            else:
                result['category'] = 'original'
        elif line.lower().startswith('confidence:'):
            try:
                result['confidence'] = int(line.split(':', 1)[1].strip().replace('%', ''))
            except:
                result['confidence'] = 0
        elif line.lower().startswith('reasoning:'):
            result['reasoning'] = line.split(':', 1)[1].strip()
    return result

def text_analysis(prompt, image_data_url, api_client):
    question_fix_text_check = prompt
    text_check_action_1 = question_fix_text_check.split('Action 1:')[0].strip()
    text_check_action_1 += " Please answer in the form: 'Finish: [key entity noun].'"

    output = call_qwen_vl_api(text_check_action_1, image_data_url, api_client)

    print(output)


    key_entity, wiki_knowledge = search_wiki_knowledge(output)

    print(key_entity)
    print(wiki_knowledge)

    text_check_action_2 = question_fix_text_check.split('[Analysis]')[0].strip()
    text_check_action_2 = text_check_action_2.replace('[key entity noun]', key_entity)
    text_check_action_2 = text_check_action_2.replace('[External Knowledge]', wiki_knowledge)

    output = call_qwen_vl_api(text_check_action_2, image_data_url, api_client)

    print(output)

    if "Analysis:" in output:
        output = output.split('Analysis:')[1]
    analysis = clean_data(output)

    text_check_action_3 = question_fix_text_check.replace('[key entity noun]', key_entity)
    text_check_action_3 = text_check_action_3.replace('[External Knowledge]', wiki_knowledge)
    text_check_action_3 = text_check_action_3.replace('[Analysis]', analysis)

    text_result = call_qwen_vl_api(text_check_action_3, image_data_url, api_client)

    print(text_result)

    return text_result

def visual_investigate(prompt, image_data_url, api_client):
    question_fix_image_check = prompt
    visual_check_action_1 = question_fix_image_check.split('Observation:')[0].strip()

    output = call_qwen_vl_api(visual_check_action_1, image_data_url, api_client)

    if "Thought 2" in output:
        output = output.split('Thought 2')[0]
    img_descrip = clean_data(output)

    visual_check_action_2 = question_fix_image_check.replace('[Fact-conflicting Description]', img_descrip)

    visual_result = call_qwen_vl_api(visual_check_action_2, image_data_url, api_client)
    return visual_result

def consistency_check(prompt, image_data_url, api_client):
    question_fix_consistency_reason = prompt
    consistency_result = call_qwen_vl_api(question_fix_consistency_reason, image_data_url, api_client)
    return consistency_result

def comprehensive_judge(text_result, visual_result, consistency_result, prompt, api_client):
    template_comprehensive_judge = prompt
    judge_prompt = template_comprehensive_judge.replace('[text_result]', text_result)
    judge_prompt = judge_prompt.replace('[visual_result]', visual_result)
    judge_prompt = judge_prompt.replace('[consistency_result]', consistency_result)

    judge_result = call_qwen_text_api(judge_prompt, api_client)
    verdict = parse_debate_verdict(judge_result)
    return verdict

def process_prompt(template_path, news_caption):
    with open(template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template.replace('[News caption]', news_caption)

async def MAC_Judge(news_caption, image):
    api_client = QwenVLAPI(
        model_name="qwen3.5-plus",
        api_key="sk-63d404c4829e46b2a906bb214cf30cf8",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 读取图片并编码为 Data URL
    image_bytes = await image.read()
    content_type = image.content_type or "image/jpeg"
    image_data_url = QwenVLAPI.encode_image_bytes(image_bytes, content_type)

    # 加载提示模板
    question_fix_text_check = process_prompt("./prompt_template/textual_veracity_check.txt", news_caption)
    question_fix_image_check = process_prompt("./prompt_template/visual_veracity_check.txt", news_caption)
    question_fix_consistency_reason = process_prompt("./prompt_template/cross_modal_consistency.txt", news_caption)
    template_comprehensive_judge = process_prompt("./prompt_template/comprehensive_judge.txt", news_caption)

    text_result = text_analysis(question_fix_text_check, image_data_url, api_client)
    visual_result = visual_investigate(question_fix_image_check, image_data_url, api_client)
    consistency_result = consistency_check(question_fix_consistency_reason, image_data_url, api_client)

    print(text_result)
    print(visual_result)
    print(consistency_result)

    verdict_result = comprehensive_judge(
        text_result, visual_result, consistency_result,
        template_comprehensive_judge, api_client
    )


    return verdict_result