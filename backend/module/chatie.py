import json
import os
import re

import numpy as np
import fitz
import openai

from backend.database.entity import Entity

entity = Entity()
df_prefix = {
    'appeal': '原告',
    'appealed': '被告',
    'net_other_receivables': '其他應收款淨額'
}

df_suffix = {
    'amount': '金額',
    '%': '%'
}

df_type = {
    'id': '編號',
    'title': '標題',
    'court_number': '法庭號',
    'foreword': '前言',
    'school': '學校',
    'faculty': '學系',
    'date': '日期',
    'court': '法庭',
    'year_quarter': '年季度',
    'unit': '單位'
}

s1_p = {
    'chinese': '''給定的句子為：\n"{}"\n\n給定實體類型列表：{}\n\n在這個句子中，可能包含了哪些實體類型？\n如果不存在則回答：無\n務必按照元組形式回復，並依給定的實體類型列表回答，如 (實體類型1, 實體類型2, ......)：''',
    'english': '''The given sentence is "{}"\n\nGiven a list of entity types: {}\n\nWhat entity types may be included in this sentence?\nIf not present, answer: none.\nRespond as a list, e.g. [entity type 1, entity type 2, ......]:'''
}

s2_p = {
    'chinese': '''根據給定的句子，請識別出類型是"{}"的僅一項實體。\n如果不存在則回答：無\n務必按照表格形式回復，表格有兩個欄位且欄位名稱為"實體類型"與"實體名稱"：''',
    'english': '''According to the given sentence, please identify the entity whose type is "{}".\nIf not present, answer: none.\nRespond in the form of a table with two columns and a header of (entity type, entity name):'''
}

s3_p = {
    'chinese': '''給定的句子為：\n"{}"根據給定的句子，請識別出類型是"{}"的實體。\n如果不存在則回答：無\n務必按照表格形式回復，表格有兩個欄位且欄位名稱為"實體類型"與"實體名稱"：''',
    'english': '''According to the given sentence, please identify the entity whose type is "{}".\nIf not present, answer: none.\nRespond in the form of a table with two columns and a header of (entity type, entity name):'''
}



class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def getNewSchemaDtd(dtd):
    new_dtd = dict()
    dtd = json.loads(dtd)
    mainKey = dtd.keys()
    for key1 in mainKey:
        if isinstance(dtd[key1], dict):
            subKey = dtd[key1].keys()
            for key2 in subKey:
                new_dtd[key1 + "." + key2] = dtd[key1][key2]
        else:
            new_dtd[key1] = dtd[key1]
    return new_dtd


def getType(schema_dtd):
    typelist = list()
    # typelist = list(schema_dtd.keys())
    for key, value in schema_dtd.items():
        preValue = ''
        sufValue = ''
        if '.' in key:
            if key.split('.')[0] in df_prefix.keys():
                preValue = df_prefix[key.split('.')[0]]
            if key.split('.')[1] in df_suffix.keys():
                sufValue = df_suffix[key.split('.')[1]]

        if isinstance(value, list):
            value = value[0]
        if '/' in value:
            value = value.split('/')
        if value == '':
            if key in df_type.keys():
                value = df_type[key]
            elif (preValue != '') and (sufValue != ''):
                value = ''
            else:
                continue
        if isinstance(value, list):
            if (preValue != '') and (sufValue != ''):
                typelist = typelist + [preValue + '-' + sufValue]
            else:
                if preValue != '':
                    typelist = typelist + [preValue + '-' + v for v in value]
                elif sufValue != '':
                    typelist = typelist + [v + '-' + sufValue for v in value]
                else:
                    typelist = typelist + value
        else:
            if (preValue != '') and (sufValue != ''):
                typelist.append(preValue + '-' + sufValue)
            else:
                if preValue != '':
                    typelist.append(preValue + '-' + value)
                elif sufValue != '':
                    typelist.append(value + '-' + sufValue)
                else:
                    typelist.append(value)
    for s in df_suffix.values():
        remove_str = s + '-' + s
        if remove_str in typelist:
            typelist = [value for value in typelist if value != remove_str]
    return typelist


class CHATIE:
    def __init__(self, text, schemaId, filename):
        with open("../API_KEY", "r", encoding="utf-8") as f:
            self.api_key = f.read()
        self.filename = filename
        self.sentence = text  # 文件轉成字串
        self.schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
        self.typelists = getType(getNewSchemaDtd(self.schemaInfo.get('dtd')))  # schema 結構
        self.lang = 'chinese'

    def chat(self, message):
        # message = [{"role": "system", "content": "chatGPT Start"}]
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message
        )
        res = response['choices'][0]['message']['content']
        return res, response

    def chat_extraction(self, chatbot, sentence, typelists):
        print("---Extraction---")
        mess = [{"role": "system", "content": "Extraction!!!"}]
        out = []  # 輸出列表 [(e1,et1)]
        token_usage = 0
        print('---stage1---')
        try:
            # 建構 prompt
            stage1_tl = typelists
            s1p = s1_p[self.lang].format(sentence, str(stage1_tl))
            print(s1p)

            # 请求chatgpt
            mess.append({"role": "user", "content": s1p})
            text1, response = chatbot(mess)
            mess.append({"role": "assistant", "content": text1})
            print(text1)
            token_usage = response['usage']['total_tokens']

            res1 = re.findall(r'\(.*?\)', text1)
            print(res1)

            if res1 != []:
                rels = [temp[1:-1].split(',') for temp in res1]
                rels = list(set([re.sub('[\'"]', '', j).strip() for i in rels for j in i]))
                # print(rels)
            else:  # 说明正则没提取到，可能是单个类型的情况
                text1 = text1.strip().rstrip('.')
                rels = [text1]
            print(rels)
        except Exception as e:
            print(e)
            print('extract stage 1 none out or error')
            return ['error-stage1:' + str(e)], mess

        print('---stage2---')
        try:
            for r in rels:
                if r in typelists:
                    # 建構 prompt
                    s2p = s2_p[self.lang].format(r)
                    print(s2p)

                    # 请求chatgpt
                    mess.append({"role": "user", "content": s2p})
                    text2, response = chatbot(mess)
                    mess.append({"role": "assistant", "content": text2})
                    print(text2)

                    # 正则提取结果
                    res2 = re.findall(r'\|.*?\|.*?\|', text2)
                    print(res2)

                    if res2 == []:
                        res2 = re.findall(r'.*\|.*', text2)
                        print(res2)

                    # 进一步处理结果
                    count = 0
                    for so in res2:
                        count += 1
                        if count <= 2:  # 过滤表头
                            continue

                        so = so.strip('|').split('|')
                        so = [re.sub('[\'"]', '', i).strip() for i in so]
                        if len(so) == 2:
                            s, o = so
                            # if st in s and ot in o or '---' in s and '---' in o:
                            #    continue
                            out.append((o, r))
                token_usage = token_usage + response['usage']['total_tokens']
        except Exception as e:
            print(e)
            print('ner stage 2 none out or error')
            if len(out) == 0:
                out.append('error-stage2:' + str(e))
            return out, mess

        if len(out) == 0:
            out.append('none-none')
        else:
            out = list(set(out))

        print(mess)
        # out = [('陈思成', 'PER'), ('北京', 'LOC')]

        return out, mess, token_usage

    def chat_extraction_new(self, chatbot, typelists):
        print("---Extraction---")
        mess = [{"role": "system", "content": "Extraction!!!"}]
        out = []  # 輸出列表 [(e1,et1)]
        token_usage = 0
        try:
            for r in typelists:
                # 建構 prompt
                s3p = s3_p[self.lang].format(self.sentence, str(r))
                print(s3p)

                # 请求chatgpt
                mess.append({"role": "user", "content": s3p})
                text2, response = chatbot(mess)
                mess.append({"role": "assistant", "content": text2})
                print(text2)

                # 正则提取结果
                res2 = re.findall(r'\|.*?\|.*?\|', text2)
                print(res2)

                if res2 == []:
                    res2 = re.findall(r'.*\|.*', text2)
                    print(res2)

                # 进一步处理结果
                count = 0
                for so in res2:
                    count += 1
                    if count <= 2:  # 过滤表头
                        continue

                    so = so.strip('|').split('|')
                    so = [re.sub('[\'"]', '', i).strip() for i in so]
                    if len(so) == 2:
                        s, o = so
                        # if st in s and ot in o or '---' in s and '---' in o:
                        #    continue
                        out.append((o, r))
                token_usage = token_usage + response['usage']['total_tokens']
        except Exception as e:
            print(e)
            print('ner stage 2 none out or error')
            if len(out) == 0:
                out.append('error-stage2:' + str(e))
            return out, mess

        if len(out) == 0:
            out.append('none-none')
        else:
            out = list(set(out))

        print(mess)
        # out = [('陈思成', 'PER'), ('北京', 'LOC')]

        return out, mess, token_usage

    def init_dtd(self):
        structure = json.loads(self.schemaInfo.get('dtd'))
        keys1List = [key for key in structure]
        for key1 in keys1List:
            type1 = type(structure[key1])
            if type1 == str:
                structure[key1] = ''
            elif type1 == dict:
                keys2List = [key for key in structure[key1]]
                for key2 in keys2List:
                    type2 = type(structure[key1][key2])
                    if type2 == str:
                        structure[key1][key2] = ''
                    elif type2 == list:
                        structure[key1][key2] = []
            elif type1 == list:
                structure[key1] = []
        return structure

    def sort_out_result(self, output):
        result = {}
        dtd = getNewSchemaDtd(self.schemaInfo.get('dtd'))
        for out in output:
            if out[1] in self.typelists:
                entry = out[1]
                preStr = ''
                if '-' in entry:
                    preStr = entry.split('-')[0] + '-'
                    # entry = entry.replace('-', '/')
                if entry in df_type.values():
                    attr = [k for k, v in df_type.items() if entry == preStr + v]
                else:
                    attr = list()
                    for k, v in dtd.items():
                        if isinstance(v, list):
                            v = v[0]
                        if '/' in v:
                            value = preStr + v
                            if value == entry:
                                if k not in attr:
                                    attr.append(k)
                                break
                            v = v.split('/')
                            getit = False
                            for vi in v:
                                vi = preStr + vi
                                if entry == vi:
                                    if k not in attr:
                                        attr.append(k)
                                    getit = True
                                    break
                            if getit:
                                break
                        else:
                            # v = preStr + v
                            preValue = ''
                            sufValue = ''
                            key = v
                            if '.' in k:
                                if k.split('.')[1] in df_suffix.keys():
                                    sufValue = df_suffix[k.split('.')[1]]
                                key = key + '-' + sufValue
                            if entry == key:
                                if k not in attr:
                                    attr.append(k)
                                break
                    # attr = [k for k, v in dtd.items() if entry in v]

                if len(attr) > 0:
                    out_value = str(out[0])
                    if isinstance(dtd[attr[0]], list):
                        if attr[0] not in result.keys():
                            result[attr[0]] = list()
                        if '\\n' in out_value:
                            out_value = out_value.replace('\\n', '').replace(' ', '')
                        if '<br>' in out_value:
                            out_value = out_value.split('<br>')
                            if '' in out_value:
                                out_value.remove('')
                            out_value = [out + '。' for out in out_value]
                            result[attr[0]] = result[attr[0]] + out_value
                        elif '。' in out_value:
                            out_value = out_value.split('。')
                            if '' in out_value:
                                out_value.remove('')
                            out_value = [out + '。' for out in out_value]
                            result[attr[0]] = result[attr[0]] + out_value
                        else:
                            if out_value not in result[attr[0]]:
                                result[attr[0]].append(out_value)
                    else:
                        # if (out_value == '無') or (out_value == '无'):
                        #     continue
                        result[attr[0]] = out_value

        ext_result = self.init_dtd()
        for key, value in result.items():
            if '.' in key:
                key1 = key.split('.')[0]
                key2 = key.split('.')[1]
                ext_result[key1][key2] = value
            else:
                ext_result[key] = value

        return ext_result

    def chatie(self):
        print('input data type:{}'.format(type(self)))
        print('input data:{}'.format(self))

        output_data = {}
        ## chatgpt
        try:
            chatbot = self.chat
        except Exception as e:
            print('---chatbot---')
            print(e)
            output_data['result'] = ['error-chatbot']
            return output_data  # 没必要进行下去

        if len(self.sentence) > 4000:
            new_sentence = list()
            types = dict()
            typelists = list()
            preIdx = -1
            preKey = ''
            schema_dtd = getNewSchemaDtd(self.schemaInfo.get('dtd'))
            for key, value in schema_dtd.items():
                types[key] = value
                typelists.append(key)
                if isinstance(value, list):
                    value = value[0]
                if value != '':
                    toIdx = -1
                    if '/' in value:
                        value = value.split('/')
                        for v in value:
                            toIdx = self.sentence.find('\n' + v)
                            if toIdx != -1:
                                break
                    else:
                        toIdx = self.sentence.find('\n' + value)

                    if key == list(schema_dtd.keys())[-1]:
                        info = {
                            'attrs': getType(types),
                            'sentence': self.sentence[:]
                        }
                        new_sentence.append(info)
                    else:
                        if toIdx != -1:
                            if len(self.sentence[:toIdx]) < 800:
                                preIdx = toIdx
                                preKey = key
                                continue
                            if len(self.sentence[:toIdx]) > 800:
                                preKeyIdx = {key: index for index, key in enumerate(types)}.get(preKey)
                                attr2 = {key: value for index, (key, value) in enumerate(types.items()) if index < preKeyIdx}
                                # preKeyIdx = typelists.index(preKey)
                                # attr2 = typelists[:preKeyIdx]
                                info = {
                                    'attrs': getType(attr2),
                                    'sentence': self.sentence[:preIdx]
                                }
                                new_sentence.append(info)
                                self.sentence = self.sentence[preIdx:]
                                types = {key: value for index, (key, value) in enumerate(types.items()) if index > preKeyIdx}
                                toIdx = self.sentence.find('\n' + value)
                                if len(self.sentence[:toIdx]) < 800:
                                    continue

                            info = {
                                'attrs': getType(types),
                                'sentence': self.sentence[:toIdx]
                            }
                            new_sentence.append(info)
                            self.sentence = self.sentence[toIdx:]

            output_data['result'] = list()
            output_data['mess'] = list()
            output_data['total_tokens'] = 0
            for sentence in new_sentence:
                print(sentence.get('sentence'))
                result = list()
                mess = list()
                total_tokens = 0
                times = 0
                while len(result) == 0:
                    times = times + 1
                    result, mess, total_tokens = self.chat_extraction(chatbot, sentence.get('sentence'), list(sentence.get('attrs')))
                    if result[0] == 'none-none':
                        result = list()
                    # 當已重複執行5次後，將放棄此組實體類型，避免重複執行太多次，成本會過高
                    if times > 5:
                        break
                output_data['result'] = output_data['result'] + result
                output_data['mess'] = output_data['mess'] + mess
                output_data['total_tokens'] = output_data['total_tokens'] + total_tokens

        elif len(self.typelists) > 30:
            if len(self.typelists) % 5 > 0:
                total_items = int(len(self.typelists) / 5) + 1
            else:
                total_items = int(len(self.typelists) / 5)
            new_typelists = np.array_split(self.typelists, int(total_items))

            if len(new_typelists) > 0:
                output_data['result'] = list()
                output_data['mess'] = list()
                output_data['total_tokens'] = 0
                for types in new_typelists:
                    result = list()
                    mess = list()
                    total_tokens = 0
                    times = 0
                    while len(result) == 0:
                        times = times + 1
                        result, mess, total_tokens = self.chat_extraction(chatbot, self.sentence, list(types))
                        if result[0] == 'none-none':
                            result = list()
                        # 當已重複執行5次後，將放棄此組實體類型，避免重複執行太多次，成本會過高
                        if times > 5:
                            break
                    output_data['result'] = output_data['result'] + result
                    output_data['mess'] = output_data['mess'] + mess
                    output_data['total_tokens'] = output_data['total_tokens'] + total_tokens
        else:
            times = 0
            go = True
            while go:
                times = times + 1
                output_data['result'], output_data['mess'], output_data['total_tokens'] = self.chat_extraction(chatbot, self.sentence, self.typelists)
                if output_data['result'][0] != 'none-none':
                    go = False
                if times > 5:
                    break

        output_data['type'] = self.typelists
        output_data['total_cost'] = 0.002 * output_data['total_tokens'] / 1000
        print(f"Output: {output_data['result']}")
        print(f"Total Tokens: {output_data['total_tokens']}")
        print(f"Total Cost (USD): ${output_data['total_cost']}")
        # print(f"Prompt Tokens: {cb.prompt_tokens}")
        # print(f"Completion Tokens: {cb.completion_tokens}")
        # print(f"Successful Requests: {cb.successful_requests}")

        with open('access_record.json', mode='a', encoding='utf-8') as fw:
            fw.write(json.dumps(output_data, cls=MyEncoder, indent=4, ensure_ascii=False) + '\n')

        ext_info = dict()
        ext_info['filename'] = self.filename
        ext_info['result'] = self.sort_out_result(output_data['result'])
        ext_info['total_tokens'] = output_data['total_tokens']
        ext_info['total_cost'] = output_data['total_cost']
        with open('extraction.json', mode='a', encoding='utf-8') as fw:
            fw.write(json.dumps(ext_info, cls=MyEncoder, indent=4, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    schema_id = '4869dc7b98d645ef86519a63c745e99e'
    pdfFile = '../data/demo/4869dc7b98d645ef86519a63c745e99e/test/35-戀戀澎湖海水藍３日.pdf'
    filename = os.path.basename(pdfFile)
    pdf_text = ''
    if os.path.exists(pdfFile):
        print(pdfFile)
        with fitz.open(pdfFile) as pdf:
            for page in pdf:
                pdf_text = pdf_text + page.get_text("text")
    else:
        print('File is not exist!')

    # new_pdf_text = re.sub(r'(\s\s|\s|)[0-9]([0-9]|)+\n', '', pdf_text)
    new_pdf_text = re.sub(r'[０-９]', '', pdf_text)
    # new_pdf_text = re.sub(r'(\s|)[0-9]([0-9]|)$', '', new_pdf_text)
    new_pdf_text = re.sub(r' ', '', new_pdf_text)
    new_pdf_text = re.sub(r'(\u3000|\u00A0|\u0020)*', '', new_pdf_text)
    # new_pdf_text = re.sub(r'\n', '', new_pdf_text)
    # print(new_pdf_text)
    pdf_text = new_pdf_text
    print(pdf_text)

    chatie = CHATIE(pdf_text, schema_id, filename)
    chatie.chatie()

    # output = []
    # ext_info = dict()
    # ext_info['filename'] = filename
    # ext_info['result'] = chatie.sort_out_result(output)
    # with open('extraction.json', mode='a', encoding='utf-8') as fw:
    #     fw.write(json.dumps(ext_info, cls=MyEncoder, indent=4, ensure_ascii=False) + '\n')