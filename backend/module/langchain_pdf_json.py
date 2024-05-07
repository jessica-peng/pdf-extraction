import copy
import difflib
import json
import numpy as np

from bs4 import BeautifulSoup
from langchain.callbacks import get_openai_callback
from langchain.output_parsers.structured import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

import sys

sys.path.append("..")
from database.entity import Entity

entity = Entity()


class LCOP:
    def getNewSchemaDtd(self, dtd):
        new_dtd = dict()
        dtd = json.loads(dtd)
        mainKey = dtd.keys()
        for key1 in mainKey:
            if isinstance(dtd[key1], dict):
                subKey = dtd[key1].keys()
                for key2 in subKey:
                    new_dtd[key1 + "-" + key2] = dtd[key1][key2]
            else:
                new_dtd[key1] = dtd[key1]
        return new_dtd

    def __init__(self, schemaId, dtd, source):
        self.schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
        self.schema_dtd = self.getNewSchemaDtd(self.schemaInfo.get('dtd'))
        self.dtd = dtd
        self.new_dtd = self.getNewSchemaDtd(json.dumps(dtd))
        self.source = source

        with open("API_KEY", "r", encoding="utf-8") as f:
            api_key = f.read()
        # llm = OpenAI(model_name="text-davinci-003", openai_api_key=key)
        self.llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)
        self.response_schemas = []
        for key, value in self.schema_dtd.items():
            if isinstance(value, list):
                value = value[0]
            self.response_schemas.append(ResponseSchema(name=key, description=value))

    def getLineContentAttr(self, lines):
        line_info = []
        for line in lines:
            spans = line.findAll("span")
            line_content = ""
            for span in spans:
                line_content = line_content + span.getText()

            attrs = line.attrs
            info = {
                'line_content': line_content,
                'spans': spans,
                'attr': attrs
            }
            line_info.append(info)

        return line_info

    def getNewInstance(self, file_instance):
        new_dtd = dict()
        dtd = file_instance
        mainKey = dtd.keys()
        for key1 in mainKey:
            if isinstance(dtd[key1], dict):
                subKey = dtd[key1].keys()
                for key2 in subKey:
                    new_dtd[key1 + "-" + key2] = dtd[key1][key2]
            else:
                new_dtd[key1] = dtd[key1]

        return new_dtd

    def get_match_line_info(self, lines, value, sp):
        line_id = []
        start_idx = -1
        end_idx = -1
        ratio = 1
        v = ''
        for line in lines:
            line_content = line['line_content']
            if v == value:
                break
            if line_content in value:
                score = difflib.SequenceMatcher(None, value, line_content).ratio()
                if (len(line_content) < 40) & (line_content not in self.schemaInfo['pattern_list']):
                    ratio = len(line_content) / len(value)
                if score >= 0.4 * ratio:
                    v = v + line_content
                    line_id.append(line.get('attr').get('id'))
                    startIdx = 0
                    span = line.get('spans')
                    if start_idx == -1:
                        start_idx = span[startIdx].attrs['data-value']
                    end_idx = int(span[len(span) - 1].attrs['data-value']) + 1
            elif value in line_content:
                if '/' in sp:
                    for s in sp.split('/'):
                        if s in line_content:
                            sp = s
                            break
                complete_value = sp + value
                if difflib.SequenceMatcher(None, complete_value, line_content).ratio() >= 0.7:
                    startIdx = line_content.find(value)
                    line_id.append(line.get('attr').get('id'))
                    span = line.get('spans')
                    if start_idx == -1:
                        start_idx = span[startIdx].attrs['data-value']
                    end_idx = int(span[len(span) - 1].attrs['data-value']) + 1
                    break

        return line_id, start_idx, end_idx

    def sort_out_result(self, result, attrList, lines):
        # print(f'result = {result}')
        # print(f'attrList = {attrList}')
        # print(f'lines = {lines}')

        file_instance = copy.deepcopy(self.dtd)
        file_position = copy.deepcopy(self.dtd)
        line_info = self.getLineContentAttr(lines)

        for key, value in result.items():
            if value is None:
                continue

            value = value.replace('\u3000', '').replace('\u0020', '').replace('\u00A0', '').replace('\xa0', '').replace(
                '\x00', '')

            if '-' in key:
                key1 = key.split('-')[0]
                key2 = key.split('-')[1]
                if isinstance(file_instance[key1][key2], list):
                    if value == '':
                        continue
                    if '\n' in value:
                        for v in value.split('\n'):
                            if v == '':
                                continue
                            file_instance[key1][key2].append(v)
                    # elif ',' in value:
                    #     for v in value.split(','):
                    #         file_instance[key1][key2].append(v)
                    # elif '，' in value:
                    #     for v in value.split('，'):
                    #         file_instance[key1][key2].append(v)
                    else:
                        file_instance[key1][key2].append(value)
                else:
                    file_instance[key1][key2] = value.replace('\n', '')
            else:
                if isinstance(file_instance[key], list):
                    if value == '':
                        continue
                    if '\n' in value:
                        for v in value.split('\n'):
                            if v == '':
                                continue
                            file_instance[key].append(v)
                    # elif ',' in value:
                    #     for v in value.split(','):
                    #         file_instance[key].append(v)
                    # elif '，' in value:
                    #     for v in value.split('，'):
                    #         file_instance[key].append(v)
                    else:
                        file_instance[key].append(value)
                else:
                    file_instance[key] = value.replace('\n', '')

        new_instance = self.getNewInstance(file_instance)
        for key, value in new_instance.items():
            key1 = key
            key2 = ''
            if '-' in key:
                key1 = key.split('-')[0]
                key2 = key.split('-')[1]
            color = next(item['color'] for item in attrList if item["level1"] == key1)

            if isinstance(self.schema_dtd[key], list):
                sp = self.schema_dtd[key][0]
            else:
                sp = self.schema_dtd[key]

            if isinstance(value, list):
                for i in value:
                    position = dict()
                    line_id, start_idx, end_idx = self.get_match_line_info(line_info, i, sp)

                    position['color'] = color
                    position['lineId'] = line_id
                    position['start'] = start_idx
                    position['end'] = end_idx
                    if '-' in key:
                        file_position[key1][key2].append(json.dumps(position))
                    else:
                        file_position[key1].append(json.dumps(position))
            else:
                position = dict()
                line_id, start_idx, end_idx = self.get_match_line_info(line_info, value, sp)
                position['color'] = color
                position['lineId'] = line_id
                position['start'] = start_idx
                position['end'] = end_idx
                if '-' in key:
                    file_position[key1][key2] = json.dumps(position)
                else:
                    file_position[key1] = json.dumps(position)

        return file_instance, file_position

    def extraction(self, attrList):
        # 讀取文件
        soup = BeautifulSoup(self.source, 'html.parser')
        lines = soup.findAll('p')
        pdf_text = ''
        for line in lines:
            spans = line.findAll('span')
            line_content = ''
            for span in spans:
                line_content = line_content + span.getText()
            pdf_text = pdf_text + '\n' + line_content.replace('　', '')
        print("pdf_text = " + pdf_text + ";token = " + str(len(pdf_text)))

        # template = """
        #         使用PDF文件的上下文來擷取對應的資訊，必須完整擷取schema結構所對應的資訊內容，不做文字編碼改變及不允許改變schema結構，並且依照項目統整資訊內容，不知道答案就輸出空值，請不要試圖編答案，
        #
        #         {format_instructions}
        #
        #         % USER INPUT:
        #         {user_input}
        #
        #         YOUR RESPONSE:
        #         """
        template = """
                        參照schema結構，擷取PDF文件中的相對應資訊，不做文字編碼改變及不允許改變schema結構，並且依照項目統整資訊內容，不知道答案就輸出空值，請不要試圖編答案，

                        {format_instructions}

                        % USER INPUT:
                        {user_input}

                        YOUR RESPONSE:
                        """

        print("template token = " + str(len(template)))

        new_schema = []
        if len(self.response_schemas) > 50:
            total_items = 0
            if len(self.response_schemas) % 10 > 0:
                total_items = (len(self.response_schemas) / 10) + 1
            else:
                total_items = (len(self.response_schemas) / 10)

            new_schema = np.array_split(self.response_schemas, int(total_items))

        print(new_schema)

        texts = list()
        attrs = list()
        goWithSplit = False
        if (len(pdf_text) > 1500) or goWithSplit:
            preIdx = -1
            preKey = ''
            for key, value in self.schema_dtd.items():
                attrs.append(key)
                if isinstance(value, list):
                    value = value[0]
                if value != '':
                    toIdx = -1
                    if '/' in value:
                        value = value.split('/')
                        for v in value:
                            toIdx = pdf_text.find('\n' + v)
                            if toIdx != -1:
                                break
                    else:
                        toIdx = pdf_text.find('\n' + value)

                    if key == list(self.schema_dtd.keys())[-1]:
                        info = {
                            'attrs': attrs,
                            'text': pdf_text[:]
                        }
                        texts.append(info)
                    else:
                        if toIdx != -1:
                            if len(pdf_text[:toIdx]) < 1000:
                                preIdx = toIdx
                                preKey = key
                                continue
                            if len(pdf_text[:toIdx]) > 1500:
                                preKeyIdx = attrs.index(preKey)
                                attr2 = attrs[:preKeyIdx]
                                info = {
                                    'attrs': attr2,
                                    'text': pdf_text[:preIdx]
                                }
                                texts.append(info)
                                pdf_text = pdf_text[preIdx:]
                                attrs = attrs[preKeyIdx:]
                                if isinstance(value, list):
                                    toIdx = -1
                                    for v in value:
                                        toIdx = pdf_text.find('\n' + v)
                                        if toIdx != -1:
                                            break
                                else:
                                    toIdx = pdf_text.find('\n' + value)
                                preIdx = toIdx
                                preKey = key

                            # info = {
                            #     'attrs': attrs,
                            #     'text': pdf_text[:toIdx]
                            # }
                            # texts.append(info)
                            # pdf_text = pdf_text[toIdx:]

            new_result = {}
            total_tokens = 0
            total_cost = 0
            for text in texts:
                print(text.get('text'))
                new_response_schemas = list()
                # 初始化解析器
                for rs in self.response_schemas:
                    if rs.name in text.get('attrs'):
                        new_response_schemas.append(rs)
                print(f"response_schemas = {str(new_response_schemas)} ; Len = {len(str(new_response_schemas))}")
                output_parser = StructuredOutputParser.from_response_schemas(new_response_schemas)
                format_instructions = output_parser.get_format_instructions()

                # 将我们的格式描述嵌入到 prompt 中去，告诉 llm 我们需要他输出什么样格式的内容
                prompt = PromptTemplate(
                    input_variables=['user_input'],
                    partial_variables={'format_instructions': format_instructions},
                    template=template
                )

                with get_openai_callback() as cb:
                    promptValue = prompt.format(user_input=text.get('text'))
                    llm_output = self.llm(promptValue)
                    print("llm_output = " + llm_output)

                    # 使用解析器进行解析生成的内容
                    result = output_parser.parse(llm_output)
                    total_tokens = total_tokens + cb.total_tokens
                    total_cost = total_cost + cb.total_cost
                new_result.update(result)

            # 整理提取結果為所設計的schema結構
            print("new_result = " + str(new_result))
            print(f"Output: {new_result}")
            print(f"Total Tokens: {total_tokens}")
            print(f"Total Cost (USD): ${total_cost}")

            # 整理提取結果為所設計的schema結構
            instance, position = self.sort_out_result(new_result, attrList, lines)
        elif len(new_schema) > 0:
            new_result = {}
            total_tokens = 0
            total_cost = 0
            for schema in new_schema:
                # 初始化解析器
                print(f"response_schemas = {str(list(schema))} ; Len = {len(str(schema))}")
                output_parser = StructuredOutputParser.from_response_schemas(list(schema))
                format_instructions = output_parser.get_format_instructions()

                # 将我们的格式描述嵌入到 prompt 中去，告诉 llm 我们需要他输出什么样格式的内容
                prompt = PromptTemplate(
                    input_variables=['user_input'],
                    partial_variables={'format_instructions': format_instructions},
                    template=template
                )

                with get_openai_callback() as cb:
                    promptValue = prompt.format(user_input=pdf_text)
                    llm_output = self.llm(promptValue)
                    print("llm_output = " + llm_output)

                    # 使用解析器进行解析生成的内容
                    llm_output.replace("\'", "\"")
                    result = output_parser.parse(llm_output)
                    print("result = " + str(result))

                    total_tokens = total_tokens + cb.total_tokens
                    total_cost = total_cost + cb.total_cost

                new_result.update(result)

            # 整理提取結果為所設計的schema結構
            print("new_result = " + str(new_result))
            print(f"Output: {new_result}")
            print(f"Total Tokens: {total_tokens}")
            print(f"Total Cost (USD): ${total_cost}")
            instance, position = self.sort_out_result(new_result, attrList, lines)
        else:
            # 初始化解析器
            print(f"response_schemas = {str(self.response_schemas)} ; Len = {len(str(self.response_schemas))}")
            output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
            format_instructions = output_parser.get_format_instructions()

            # 将我们的格式描述嵌入到 prompt 中去，告诉 llm 我们需要他输出什么样格式的内容
            prompt = PromptTemplate(
                input_variables=['user_input'],
                partial_variables={'format_instructions': format_instructions},
                template=template
            )

            with get_openai_callback() as cb:
                promptValue = prompt.format(user_input=pdf_text)
                llm_output = self.llm(promptValue)

                print("llm_output = " + llm_output + ";token = " + str(len(pdf_text)))

                # 使用解析器进行解析生成的内容
                result = output_parser.parse(llm_output)

                print("result = " + str(result))
                print(f"Output: {result}")
                print(f"Total Tokens: {cb.total_tokens}")
                print(f"Total Cost (USD): ${cb.total_cost}")
                # print(f"Prompt Tokens: {cb.prompt_tokens}")
                # print(f"Completion Tokens: {cb.completion_tokens}")
                # print(f"Successful Requests: {cb.successful_requests}")

            # 整理提取結果為所設計的schema結構
            instance, position = self.sort_out_result(result, attrList, lines)

        return instance, position

    def get_key(self, line):
        target = ""
        for key, value in self.new_dtd.items():
            if value == '':
                continue
            ratio = 1
            if isinstance(value, list):
                for i in value:
                    if line in i:
                        if (len(line) < 15) & (line not in self.schemaInfo['pattern_list']):
                            ratio = len(line) / len(i)
                        if difflib.SequenceMatcher(None, i, line).ratio() >= 0.4 * ratio:
                            target = key
                            break
                if target != "":
                    break
            else:
                if line in value:
                    if (len(line) < 15) & (line not in self.schemaInfo['pattern_list']):
                        ratio = len(line) / len(value)
                    if difflib.SequenceMatcher(None, value, line).ratio() >= 0.4 * ratio:
                        target = key
                        break
        return target

    def updateSchemaDtd(self, attr, leftStr):
        schema_dtd_json = json.loads(self.schemaInfo.get('dtd'))
        schema_pattern_list = self.schemaInfo.get('pattern_list')
        schema_pattern_list.append(leftStr)
        if '-' in attr:
            mainKey = attr.split('-')[0]
            subKey = attr.split('-')[1]
            if isinstance(schema_dtd_json[mainKey][subKey], list):
                if len(schema_dtd_json[mainKey][subKey]) > 0:
                    sp = schema_dtd_json[mainKey][subKey][0] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[mainKey][subKey][0] = sp
            else:
                if '/' in schema_dtd_json[mainKey][subKey]:
                    sp = schema_dtd_json[mainKey][subKey] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[mainKey][subKey] = sp
        else:
            if isinstance(schema_dtd_json[attr], list):
                if len(schema_dtd_json[attr]) > 0:
                    sp = schema_dtd_json[attr][0] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[attr][0] = sp
            else:
                if '/' in schema_dtd_json[attr]:
                    sp = schema_dtd_json[attr] + '/' + leftStr
                elif schema_dtd_json[attr] != "":
                    sp = schema_dtd_json[attr] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[attr] = sp

        # dtd = stringify(schema_dtd_json)
        dtd = json.dumps(schema_dtd_json, ensure_ascii=False, default=str)
        return entity.updateSchema(self.schemaInfo.get('schema_id'), "", "", schema_pattern_list, "", dtd, "", "", "",
                                   "", "", "")

    def get_new_dtd(self):
        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))

        for line in line_info:
            line_content = line.get('line_content')
            if "　" in line_content:
                sp = self.get_key(line_content.split("　")[1])
            else:
                sp = self.get_key(line_content)

            if sp == '':
                continue

            value = self.new_dtd[sp]
            if isinstance(value, list):
                value = value[0]
            startIdx = line_content.find(value)
            if startIdx == -1:
                startIdx = line_content.replace('\u3000', '').find(value)

            if isinstance(self.schema_dtd[sp], list):
                if '/' in self.schema_dtd[sp][0]:
                    sp_list = self.schema_dtd[sp][0].split('/')
                else:
                    sp_list = self.schema_dtd[sp][0]
            else:
                if '/' in self.schema_dtd[sp]:
                    sp_list = self.schema_dtd[sp].split('/')
                else:
                    sp_list = self.schema_dtd[sp]

            if startIdx > 0:
                leftStr = line_content[0:startIdx].replace('\u3000', '').replace('\u00A0', '')
                if leftStr not in sp_list:
                    self.schemaInfo = self.updateSchemaDtd(sp, leftStr)
        return self.schemaInfo

# if __name__ == '__main__':
#     schema_id = '9c0f7fc5ee544156ba895006e1197e6d'
#     pdfFile = '../data/demo/9c0f7fc5ee544156ba895006e1197e6d/test/01-11112102235-20.pdf'
#     filename = os.path.basename(pdfFile)
#     pdf_text = ''
#     if os.path.exists(pdfFile):
#         print(pdfFile)
#         with fitz.open(pdfFile) as pdf:
#             for page in pdf:
#                 pdf_text = pdf_text + page.get_text("text")
#     else:
#         print('File is not exist!')
#
#     new_pdf_text = re.sub(r'(\s\s|\s|)[0-9]([0-9]|)+\n', '', pdf_text)
#     new_pdf_text = re.sub(r'[０-９]', '', new_pdf_text)
#     new_pdf_text = re.sub(r'(\s|)[0-9]([0-9]|)$', '', new_pdf_text)
#     new_pdf_text = re.sub(r' ', '', new_pdf_text)
#     new_pdf_text = re.sub(r'(\u3000|\u00A0|\u0020)*', '', new_pdf_text)
#     # new_pdf_text = re.sub(r'\n', '', new_pdf_text)
#     # print(new_pdf_text)
#     pdf_text = new_pdf_text
#     print(pdf_text)
#
#     lcop = LCOP(schema_id, pdf_text, schema_id)
#     result = lcop.sort_out_result()

# ext_info = dict()
# ext_info['filename'] = filename
# result = [('20,680', '透過損益按公允價值衡量之金融資產－流動-金額'), ('0.91', '現金及約當現金-%'), ('12,075', '現金及約當現金-金額'), ('104年03月31日', '日期'), ('民國104年第1季', '年季度'), ('61,405', '備供出售金融資產－流動淨額-金額'), ('104年03月31日', '透過損益按公允價值衡量之金融資產－流動-%'), ('413,956', '透過損益按公允價值衡量之金融資產－非流動-金額'), ('61,405', '備供出售金融資產－流動淨額-%'), ('48,000', '透過損益按公允價值衡量之金融資產－非流動-%'), ('54,910', '備供出售金融資產－非流動淨額-金額'), ('0.10', '其他應付款項－關係人-%'), ('1,124', '其他應付款項－關係人-金額'), ('317,838', '不動產、廠房及設備-金額'), ('4.15', '備供出售金融資產－非流動淨額-%'), ('24.02', '不動產、廠房及設備-%'), ('11,721', '其他非流動資產-金額'), ('117,377', '其他非流動資產-%'), ('30,983', '投資性不動產淨額-金額'), ('2.81', '投資性不動產淨額-%'), ('31.28', '非流動資產合計-%'), ('413,956', '非流動資產合計-金額'), ('0', '本期所得稅負債-金額'), ('4.14', '遞延所得稅負債-%'), ('54,850', '遞延所得稅負債-金額'), ('0.18', '應收票據淨額-%'), ('14,537', '應收帳款淨額-金額'), ('0.52', '應收帳款淨額-%'), ('1.12', '應收帳款淨額-%'), ('0.02', '應收票據淨額-%'), ('2,314', '應收票據淨額-金額'), ('9,439', '應收票據淨額-金額'), ('6,903', '應收帳款淨額-金額'), ('0.00', '本期所得稅負債-%'), ('95,281', '其他流動負債-金額'), ('2.27', '應付短期票券-%'), ('30,000', '應付短期票券-金額'), ('121,548', '其他流動資產-金額'), ('9.19', '其他流動資產-%'), ('4.49', '其他流動負債-%'), ('7.46', '流動負債合計-%'), ('2,762', '資本公積合計-金額'), ('325,855', '流動負債合計-金額'), ('0.21', '資本公積合計-%'), ('4.52', '特別盈餘公積-%'), ('1.74', '法定盈餘公積-%'), ('22,585', '法定盈餘公積-金額'), ('58,681', '特別盈餘公積-金額'), ('63,242', '保留盈餘合計-金額'), ('0.43', '其他權益合計-%'), ('1,554', '其他權益合計-金額'), ('3.05', '保留盈餘合計-%'), ('1,124', '其他應付款-%'), ('7,297', '其他應付款-金額'), ('無', '非控制權益-%'), ('879,164', '普通股股本-金額'), ('無', '普通股股本-%'), ('178,169', '短期借款-金額'), ('12,694', '非控制權益-金額'), ('7,235', '應付票據-金額'), ('6,749', '應付帳款-金額'), ('13.46', '短期借款-%'), ('0.51', '應付帳款-%'), ('0.55', '應付票據-%'), ('28.77', '負債總額-%'), ('677,193', '存貨-金額'), ('879,164', '股本合計-金額'), ('66.44', '股本合計-%'), ('380,765', '負債總額-金額'), ('新台幣仟元', '單位'), ('5,414 (0.41)', '遞延所得稅資產-金額'), ('103 (3,852)', '其他應收款淨額-金額'), ('103 (0.03)', '其他應收款淨額-%'), ('103 (30.16)', '存貨-%'), ('0.41', '遞延所得稅資產-%'), ('11,779', '其他非流動負債-%'), ('54,910', '非流動負債合計-金額'), ('4.87', '非流動負債合計-%'), ('11,721', '其他非流動負債-金額')]
# ext_info['result'] = chatie.sort_out_result(result)
# with open('extraction.json', mode='a', encoding='utf-8') as fw:
#     fw.write(json.dumps(ext_info, cls=MyEncoder, indent=4, ensure_ascii=False) + '\n')
# print(ext_info['result'])
