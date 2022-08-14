import glob
import json
import os
import re
import shutil
import time
import pandas as pd


class PrefixSpan:
    def __init__(self, path, tokens, support, patternMin, patternMax):
        self.system_time = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
        self.path = path
        self.support = float(support)
        self.patternMin = int(patternMin)
        self.patternMax = int(patternMax)
        self.statistics_dir = self.path + '/statistics/'
        self.prepare = self.statistics_dir + self.system_time + '.csv'
        self.article_count = 0
        self.tokens = {}
        for token in json.loads(tokens):
            self.tokens[token['name']] = token['checked']

    def prepare_file(self):
        if not os.path.exists(self.statistics_dir):
            os.makedirs(self.statistics_dir)

        pdf2dict_dir = self.path + '/pdf2dict/'
        datas = []
        idx = 0
        searchPath = pdf2dict_dir + '*.json'
        for jsonFile in glob.glob(searchPath):
            idx += 1
            basename = os.path.basename(jsonFile)
            filename = os.path.splitext(basename)[0]
            print(filename)
            with open(jsonFile, mode='r', encoding='utf-8') as file:
                pageList = json.load(file)
                pageIdx = 0
                for page in pageList:
                    pageIdx += 1

                    rowIdx = 0
                    blockList = page['blocks']
                    for block in blockList:
                        text = ''
                        if block.get('lines') is None:
                            continue
                        lineList = block['lines']
                        for line in lineList:

                            spanList = line['spans']
                            for span in spanList:
                                if text == span['text']:
                                    continue

                                text = span['text']
                                x = span['origin'][0]
                                y = span['origin'][1]

                                checkline = " ".join(text.split())
                                checkline = checkline.replace(" ", "")
                                checkline = checkline.replace(" ", "")

                                # if self.opt.remove_empty_line:
                                if checkline.strip() == '':
                                    continue

                                if self.tokens.get('Number'):
                                    if re.match(r'^(-|)\d*$', checkline):
                                        continue
                                    if '0000000000000000' in checkline:
                                        continue
                                if self.tokens.get('Basic symbol'):
                                    # 、,。,〃,〈,〉,《,》,「,」,『,』
                                    if re.match(r'\S*([\u3001-\u3003]|[\u3008-\u3009]|[\u300A-\u300F])$', checkline):
                                        continue
                                    # ！,＃,＄,＆,（,）,＊,＋,，,－,．,／
                                    if re.match(r'\S*(\uFF01|[\uFF03-\uFF06]|[\uFF08-\uFF0F])$', checkline):
                                        continue
                                    # ﹙,﹚,﹛,﹜,﹝,﹞,(,),:,/
                                    if re.match(
                                            r'\S*(\uFE59|\uFE5A|\uFE5B|\uFE5C|\uFE5D|\uFE5E|\u0029|\u0028|\u003A|\u002F)$',
                                            checkline):
                                        continue
                                    # ：,；,？
                                    if re.match(r'\S*(\uFF1A|\uFF1B|\uFF1F)$', checkline):
                                        continue
                                    # –,—,‘,’,“,”
                                    if re.match(r'\S*([\u2013-\u2014]|[\u2018-\u2019]|[\u201C-\u201D])$', checkline):
                                        continue
                                    # 【,】,〔,〕,〝,〞
                                    if re.match(r'\S*([\u3010-\u3011]|[\u3014-\u3015]|[\u301D-\u301E])$', checkline):
                                        continue

                                str_length = 0
                                line_str = ''

                                split_str = re.split(r'\s+|   | 　', text)
                                print(split_str)

                                for element in split_str:
                                    if element != '':
                                        if self.tokens.get('Number'):
                                            if re.match(r'^\d{1,3}$', element):
                                                continue

                                        line_str = line_str + ' ' + element
                                        str_length += 1

                                if str_length > 0:
                                    rowIdx += 1
                                    new_string = line_str.strip()
                                    merge_str = new_string.replace(" ", "")

                                    # 去除空格：有部分案件格式不同，將字串長度 >15 的內容，去除字元間的空格
                                    if len(merge_str) > 15:
                                        new_string = merge_str
                                        str_length = 1

                                    data_format = {
                                        "filename": filename,
                                        "page": str(pageIdx),
                                        "row": str(rowIdx),
                                        "x": str(x),
                                        "y": str(y),
                                        "count": str(str_length),
                                        "string": new_string,
                                        "merge": merge_str
                                    }
                                    datas.append(data_format)
            file.close()
        self.article_count = idx

        # 合併字串：合併相同檔案、相同頁面且相同 y值的字串
        new_datas = []
        new_string = ''
        filename = ''
        page = ''
        x = ''
        y = ''
        compare_str = ''
        page_str = ''
        rowIdx = 0
        for data in datas:
            page_temp = data['filename'] + ';' + data['page']
            all_temp = data['filename'] + ';' + data['page'] + ';' + data['y']
            if compare_str != all_temp:
                if page_str != page_temp:
                    page_str = page_temp
                    if rowIdx != 0:
                        split_str = re.split(r'\s+|   | 　', new_string)
                        str_length = len(split_str)
                        merge_str = new_string.replace(" ", "")

                        # 去除空格：有部分案件格式不同，將字串長度 >15 的內容，去除字元間的空格
                        if len(merge_str) > 15:
                            new_string = merge_str
                            str_length = 1

                        data_format = {
                            "filename": filename,
                            "page": page,
                            "row": str(rowIdx),
                            "x": x,
                            "y": y,
                            "count": str(str_length),
                            "string": new_string,
                            "merge": merge_str
                        }
                        new_datas.append(data_format)

                        filename = data['filename']
                        page = str(data['page'])
                        x = str(data['x'])
                        y = str(data['y'])
                        new_string = data['string']

                    rowIdx = 0

                compare_str = all_temp
                if rowIdx != 0:
                    split_str = re.split(r'\s+|   | 　', new_string)
                    str_length = len(split_str)
                    merge_str = new_string.replace(" ", "")

                    # 去除空格：有部分案件格式不同，將字串長度 >15 的內容，去除字元間的空格
                    if len(merge_str) > 15:
                        new_string = merge_str
                        str_length = 1

                    data_format = {
                        "filename": filename,
                        "page": page,
                        "row": str(rowIdx),
                        "x": x,
                        "y": y,
                        "count": str(str_length),
                        "string": new_string,
                        "merge": merge_str
                    }
                    new_datas.append(data_format)
                rowIdx += 1

                filename = data['filename']
                page = str(data['page'])
                x = str(data['x'])
                y = str(data['y'])
                new_string = data['string']
            else:
                new_string = new_string + ' ' + data['string']

        split_str = re.split(r'\s+|   | 　', new_string)
        str_length = len(split_str)
        merge_str = new_string.replace(" ", "")
        # 去除空格：有部分案件格式不同，將字串長度 >15 的內容，去除字元間的空格
        if len(merge_str) > 15:
            new_string = merge_str
            str_length = 1

        data_format = {
            "filename": filename,
            "page": page,
            "row": str(rowIdx),
            "x": x,
            "y": y,
            "count": str(str_length),
            "string": new_string,
            "merge": merge_str
        }
        new_datas.append(data_format)

        # 匯出資料
        df = pd.json_normalize(new_datas)
        df.to_csv(self.prepare, index=False, encoding='utf-8-sig')
        new_datas.clear()
        datas.clear()

    def prefixSpan_analyze(self):
        from prefixspan import PrefixSpan

        threshold = self.support * self.article_count

        df = pd.read_csv(self.prepare)
        dbs = []
        for data in df['string']:
            db = []
            split_str = re.split(r'\s+', data)
            for element in split_str:
                db.append(element)
            dbs.append(db)

        # Pattern 過濾：利用取出的 Pattern 自動比對案件內容，濾除不存在的 Pattern
        merge_list = []
        for data in df['merge']:
            if data not in merge_list:
                merge_list.append(data)

        ps = PrefixSpan(dbs)

        # closed_result = ps.topk(threshold, closed=True)
        # closed_result = ps.frequent(2, closed=True)
        closed_result = ps.frequent(2, filter=lambda patt, matches: len(matches) > threshold)

        # print(ps.topk(threshold, closed=True))
        print(closed_result)

        frequent = threshold
        output = []
        for result in closed_result:
            if result[0] > frequent:
                if self.tokens.get('Limit pattern length'):
                    if (len(result[1]) == 1) & (
                            (len(result[1][0]) < self.patternMin) | (len(result[1][0]) > self.patternMax)):
                        continue

                is_valid = True
                merge_str = ''
                for item in result[1]:
                    merge_str = merge_str + item.replace("'", "")
                    if self.tokens.get('Basic symbol'):
                        # 、,。,〃,〈,〉,《,》,「,」,『,』
                        if re.match(r'\S*([\u3001-\u3003]|[\u3008-\u3009]|[\u300A-\u300F])$', item):
                            is_valid = False
                            break
                        # ！,＃,＄,＆,（,）,＊,＋,，,－,．,／
                        if re.match(r'\S*(\uFF01|[\uFF03-\uFF06]|[\uFF08-\uFF0F])$', item):
                            is_valid = False
                            break
                        # ﹙,﹚,﹛,﹜,﹝,﹞,(,),:,/
                        if re.match(r'\S*(\uFE59|\uFE5A|\uFE5B|\uFE5C|\uFE5D|\uFE5E|\u0029|\u0028|\u003A|\u002F)$',
                                    item):
                            is_valid = False
                            break
                        # ：,；,？
                        if re.match(r'\S*(\uFF1A|\uFF1B|\uFF1F)$', item):
                            is_valid = False
                            break
                        # –,—,‘,’,“,”
                        if re.match(r'\S*([\u2013-\u2014]|[\u2018-\u2019]|[\u201C-\u201D])$', item):
                            is_valid = False
                            break
                        # 【,】,〔,〕,〝,〞
                        if re.match(r'\S*([\u3010-\u3011]|[\u3014-\u3015]|[\u301D-\u301E])$', item):
                            is_valid = False
                            break

                if self.tokens.get('Limit pattern length'):
                    if (len(merge_str) < self.patternMin) | (len(merge_str) > self.patternMax):
                        continue

                if is_valid:
                    # Pattern 過濾：利用取出的 Pattern 自動比對案件內容，濾除不存在的 Pattern
                    for merge in merge_list:
                        if merge_str in merge:
                            data = {
                                "frequency": result[0],
                                "itemset": result[1],
                                "merge": merge_str
                            }
                            output.append(data)
                            break
                else:
                    continue

        pattern_list = []
        for o in output:
            data = str(o['merge'])
            invalid = False
            if self.tokens.get('Limit pattern length'):
                if len(data) < 2:
                    continue
            if self.tokens.get('Duplicate characters'):
                if data[0] == data[len(data) - 1]:
                    continue
            char_temp = []
            for char in data:
                if self.tokens.get('Number'):
                    if re.match(r'^\d$', char):
                        invalid = True
                        break
                if self.tokens.get('Basic symbol'):
                    if re.match(r'^\uFFFD$', char):
                        invalid = True
                        break
                if self.tokens.get('Duplicate characters'):
                    if char in char_temp:
                        invalid = True
                        break
                    else:
                        char_temp.append(char)

            if invalid:
                continue

            # 移除重複Pattern：移除重複取得的 Pattern
            if data not in pattern_list:
                pattern_list.append(data)

        pattern_list.sort(key=lambda s: len(s), reverse=True)
        print(pattern_list)

        output_list = []
        for pattern in pattern_list:
            index = [i for i, v in enumerate(output) if v['merge'] == pattern]
            freq = 0
            for idx in index:
                freq = freq + int(output[idx]['frequency'])
            output_format = {
                "frequency": str(freq),
                "merge": pattern
            }
            output_list.append(output_format)

        # 匯出資料
        output_path = os.path.splitext(self.prepare)[0] + "-pattern.csv"
        df = pd.json_normalize(output_list)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        output_list.clear()
        return pattern_list

    def executePrefixSpan(self):
        self.prepare_file()
        pattern_list = self.prefixSpan_analyze()
        return pattern_list
