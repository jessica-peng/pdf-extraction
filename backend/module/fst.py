import copy
import difflib
import json
import re

from SciPyFST import fst
from bs4 import BeautifulSoup
from .softmealy import SoftMealy
import sys

sys.path.append("..")
# from module.database.entity import Entity
from database.entity import Entity

entity = Entity()


def init_fst():
    fst_format = {
        "states": ['GB', 'GE'],
        "initState": 'GB',
        "inAlphabet": [],
        "outAlphabet": [],
        "transitionFunction": [['GB', 'skip', 'GB']],
        "outputFunction": [],
        "finalStates": ['GE']
    }
    return fst_format


class FST:
    def getNewSchemaDtd(self):
        new_dtd = dict()
        dtd = json.loads(self.schemaInfo.get('dtd'))
        mainKey = dtd.keys()
        for key1 in mainKey:
            if isinstance(dtd[key1], dict):
                subKey = dtd[key1].keys()
                for key2 in subKey:
                    new_dtd[key1 + "." + key2] = dtd[key1][key2]
            else:
                new_dtd[key1] = dtd[key1]

        return new_dtd

    def __init__(self, schemaId, fileId, dtd, source, mapping, filetype):
        self.schema = schemaId
        self.file = fileId
        self.filetype = filetype
        self.dtd = dtd
        self.mapping = mapping
        self.new_dtd = dict()
        self.source = source
        self.schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
        self.schema_dtd = self.getNewSchemaDtd()
        self.fileInfo = entity.getFileInfoBySchemaIdAndFileId(schemaId, fileId)
        if len(self.schemaInfo['mealy_fst']) == 0:
            self.mealy_fst = init_fst()
        else:
            self.mealy_fst = self.schemaInfo['mealy_fst']
            self.fstMealy = fst(initState=self.mealy_fst['initState'],
                                states=self.mealy_fst['states'],
                                transitionFunction=self.mealy_fst['transitionFunction'],
                                outputFunction=self.mealy_fst['outputFunction'],
                                finalStates=self.mealy_fst['finalStates'])

        if len(self.schemaInfo['moore_fst']) == 0:
            self.moore_fst = init_fst()
        else:
            self.moore_fst = self.schemaInfo['moore_fst']
            self.fstMoore = fst(initState=self.moore_fst['initState'],
                                states=self.moore_fst['states'],
                                transitionFunction=self.moore_fst['transitionFunction'],
                                outputFunction=self.moore_fst['outputFunction'],
                                finalStates=self.moore_fst['finalStates'])

        if len(self.schemaInfo['softmealy_fst']) == 0:
            self.softmealy_fst = init_fst()
        else:
            self.softmealy_fst = self.schemaInfo['softmealy_fst']
            self.fstSoftmealy = SoftMealy(initState=self.softmealy_fst['initState'],
                                          states=self.softmealy_fst['states'],
                                          inAlphabet=self.softmealy_fst['inAlphabet'],
                                          outAlphabet=self.softmealy_fst['outAlphabet'],
                                          transitionFunction=self.softmealy_fst['transitionFunction'],
                                          outputFunction=self.softmealy_fst['outputFunction'],
                                          finalStates=self.softmealy_fst['finalStates'])

        if len(self.schemaInfo['extraction_rules']) == 0:
            self.rules = {}
        else:
            self.rules = self.schemaInfo['extraction_rules']

    def get_key(self, line):
        target = ""
        isAddLine = False
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
                            if difflib.SequenceMatcher(None, i, line).ratio() == 1:
                                isAddLine = True
                            break
                if target != "":
                    break
            else:
                if line in value:
                    if (len(line) < 15) & (line not in self.schemaInfo['pattern_list']):
                        ratio = len(line) / len(value)
                    if difflib.SequenceMatcher(None, value, line).ratio() >= 0.4 * ratio:
                        target = key
                        if difflib.SequenceMatcher(None, value, line).ratio() == 1:
                            isAddLine = True
                        break

        return target, isAddLine

    def getMappingValue(self, sp):
        mapping = self.mapping[sp]
        return mapping

    def getMappingKey(self, inSignal):
        result = ""
        for key, value in self.mapping.items():
            if value == inSignal:
                result = key
        return result

    def getLineId(self, sp):
        if '.' in sp:
            mainKey = sp.split('.')[0]
            subKey = sp.split('.')[1]
            sp_info = self.fileInfo['position'][mainKey][subKey]
        else:
            sp_info = self.fileInfo['position'][sp]

        line_list = []
        if sp_info != '':
            if isinstance(sp_info, list):
                for info in sp_info:
                    info = json.loads(info)
                    for line in info['lineId']:
                        line_list.append(line)
            else:
                sp_info = json.loads(sp_info)
                line_list = sp_info['lineId']

        return line_list

    def updateMealyFst(self):
        # update states
        mainKey = self.dtd.keys()
        for key1 in mainKey:
            if isinstance(self.dtd[key1], dict):
                subKey = self.dtd[key1].keys()
                for key2 in subKey:
                    self.mealy_fst['states'].append(key1 + "." + key2)
                    self.new_dtd[key1 + "." + key2] = self.dtd[key1][key2]
            else:
                self.mealy_fst['states'].append(key1)
                self.new_dtd[key1] = self.dtd[key1]

        # update transition function
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        this_state = "GB"
        # skip_line = []
        for line in lines:
            spans = line.findAll("span")
            line_content = ""
            for span in spans:
                line_content = line_content + span.getText()

            attrs = line.attrs
            # if attrs['id'] in skip_line:
            #     continue

            if attrs.get('pattern') is None:
                if "　" in line_content:
                    sp, isAddLine = self.get_key(line_content.split("　")[1])
                else:
                    sp, isAddLine = self.get_key(line_content)
            elif '/' in attrs['pattern']:
                if "　" in line_content:
                    sp, isAddLine = self.get_key(line_content.split("　")[1])
                else:
                    sp, isAddLine = self.get_key(line_content)
            else:
                sp = attrs['pattern']
                isAddLine = True

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue

            transition = [this_state, "I" + mappingKey, sp]
            if transition not in self.mealy_fst['transitionFunction']:
                self.mealy_fst['transitionFunction'].append(transition)

            output = [this_state, mappingKey, "O" + mappingKey]
            if output not in self.mealy_fst['outputFunction']:
                self.mealy_fst['outputFunction'].append(output)
            this_state = sp

        transition = [this_state, 'ε', 'GE']
        if transition not in self.mealy_fst['transitionFunction']:
            self.mealy_fst['transitionFunction'].append(transition)
        print(self.mealy_fst['transitionFunction'])
        print(self.mealy_fst['outputFunction'])
        print("update Mealy FST")

    def updateMooreFst(self):
        # update states
        mainKey = self.dtd.keys()
        for key1 in mainKey:
            if isinstance(self.dtd[key1], dict):
                subKey = self.dtd[key1].keys()
                for key2 in subKey:
                    self.moore_fst['states'].append(key1 + "." + key2)
                    self.new_dtd[key1 + "." + key2] = self.dtd[key1][key2]
            else:
                self.moore_fst['states'].append(key1)
                self.new_dtd[key1] = self.dtd[key1]

        # update transition function
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        this_state = "GB"
        # skip_line = []
        for line in lines:
            spans = line.findAll("span")
            line_content = ""
            for span in spans:
                line_content = line_content + span.getText()

            attrs = line.attrs
            # if attrs['id'] in skip_line:
            #     continue

            if attrs.get('pattern') is None:
                if "　" in line_content:
                    sp, isAddLine = self.get_key(line_content.split("　")[1])
                else:
                    sp, isAddLine = self.get_key(line_content)
            elif '/' in attrs['pattern']:
                if "　" in line_content:
                    sp, isAddLine = self.get_key(line_content.split("　")[1])
                else:
                    sp, isAddLine = self.get_key(line_content)
            else:
                sp = attrs['pattern']
                isAddLine = True

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue

            transition = [this_state, "I" + mappingKey, sp]
            if transition not in self.moore_fst['transitionFunction']:
                self.moore_fst['transitionFunction'].append(transition)

            output = [sp, "O" + mappingKey]
            if output not in self.moore_fst['outputFunction']:
                self.moore_fst['outputFunction'].append(output)
            this_state = sp

        transition = [this_state, 'ε', 'GE']
        if transition not in self.moore_fst['transitionFunction']:
            self.moore_fst['transitionFunction'].append(transition)
        print(self.moore_fst['transitionFunction'])
        print(self.moore_fst['outputFunction'])
        print("update Moore FST")

    def updateSoftmealy(self):
        # update states
        mainKey = self.dtd.keys()
        for key1 in mainKey:
            if isinstance(self.dtd[key1], dict):
                subKey = self.dtd[key1].keys()
                for key2 in subKey:
                    self.softmealy_fst['states'].append(key1 + "." + key2)
                    self.softmealy_fst['states'].append('dummy/' + key1 + "." + key2)
                    self.new_dtd[key1 + "." + key2] = self.dtd[key1][key2]
            else:
                self.softmealy_fst['states'].append(key1)
                self.softmealy_fst['states'].append('dummy/' + key1)
                self.new_dtd[key1] = self.dtd[key1]

        # update transition function
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        this_state = "GB"
        # skip_line = []
        for line in lines:
            spans = line.findAll("span")
            line_content = ""
            for span in spans:
                line_content = line_content + span.getText()

            line_content = line_content.replace('\u3000', '').replace('\u0020', '').replace('\u00A0', '')
            attrs = line.attrs
            if attrs.get('pattern') is None:
                sp, isAddLine = self.get_key_new(line_content, attrs.get('id'))
            elif '/' in attrs['pattern']:
                sp, isAddLine = self.get_key_new(line_content, attrs.get('id'))
            else:
                sp = attrs['pattern']
                isAddLine = True

            # if attrs.get('pattern') is None:
            #     if "　" in line_content:
            #         sp, isAddLine = self.get_key(line_content.split("　")[1])
            #     else:
            #         sp, isAddLine = self.get_key(line_content)
            # elif '/' in attrs['pattern']:
            #     if "　" in line_content:
            #         sp, isAddLine = self.get_key(line_content.split("　")[1])
            #     else:
            #         sp, isAddLine = self.get_key(line_content)
            # else:
            #     sp = attrs['pattern']
            #     isAddLine = True

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue

            # transition = [this_state, "I" + mappingKey, sp]
            # preTransition = [sp, "O" + mappingKey, 'dummy/' + sp]
            if (not isAddLine) & (sp in this_state):
                continue

            transition = [this_state, "I" + mappingKey, sp]
            if transition not in self.softmealy_fst['transitionFunction']:
                self.softmealy_fst['transitionFunction'].append(transition)
            transition = [sp, "extract", sp]
            if transition not in self.softmealy_fst['transitionFunction']:
                self.softmealy_fst['transitionFunction'].append(transition)
            this_state = sp

            sp = 'dummy/' + sp
            transition = [this_state, "O" + mappingKey, sp]
            if transition not in self.softmealy_fst['transitionFunction']:
                self.softmealy_fst['transitionFunction'].append(transition)
            transition = [sp, "skip", sp]
            if transition not in self.softmealy_fst['transitionFunction']:
                self.softmealy_fst['transitionFunction'].append(transition)
            this_state = sp

        transition = [this_state, 'ε', 'GE']
        if transition not in self.softmealy_fst['transitionFunction']:
            self.softmealy_fst['transitionFunction'].append(transition)
        print(self.softmealy_fst['transitionFunction'])

        print("update Softmealy FST")

    def get_key_new(self, line, line_id):
        target = ""
        isAddLine = False
        score = -1
        for key, value in self.new_dtd.items():
            # if value == '':
            #     continue

            if line_id not in self.getLineId(key):
                continue

            target = key
            if isinstance(self.schema_dtd[key], list):
                sp = self.schema_dtd[key][0]
            else:
                sp = self.schema_dtd[key]

            ratio = 1
            if isinstance(value, list):
                for i in value:
                    if line in i:
                        isAddLine = True
                        if score < difflib.SequenceMatcher(None, i, line).ratio():
                            # if (len(line) < 40) & (line not in self.schemaInfo['pattern_list']):
                            if line not in self.schemaInfo['pattern_list']:
                                ratio = len(line) / len(i)
                            if difflib.SequenceMatcher(None, i, line).ratio() >= 0.4 * ratio:
                                score = difflib.SequenceMatcher(None, i, line).ratio()
                                # target = key
                                if difflib.SequenceMatcher(None, i, line).ratio() == 1:
                                    isAddLine = True
                                break
                    elif i in line:
                        if '/' in sp:
                            for s in sp.split('/'):
                                if s in line:
                                    sp = s
                                    break
                        if '/' in sp:
                            complete_value = i
                        else:
                            complete_value = sp + i
                        if score < difflib.SequenceMatcher(None, complete_value, line).ratio():
                            if difflib.SequenceMatcher(None, complete_value, line).ratio() >= 0.6 * ratio:
                                score = difflib.SequenceMatcher(None, complete_value, line).ratio()
                                # target = key
                                if difflib.SequenceMatcher(None, complete_value, line).ratio() == 1:
                                    isAddLine = True
                                break
                            # else:
                            #     if line.find(complete_value) == 0:
                            # target = key
                # if target != "":
                #     break
            else:
                if line in value:
                    if score < difflib.SequenceMatcher(None, value, line).ratio():
                        # if (len(line) < 40) & (line not in self.schemaInfo['pattern_list']):
                        if line not in self.schemaInfo['pattern_list']:
                            ratio = len(line) / len(value)
                        if difflib.SequenceMatcher(None, value, line).ratio() >= 0.4 * ratio:
                            score = difflib.SequenceMatcher(None, value, line).ratio()
                            # target = key
                            if difflib.SequenceMatcher(None, value, line).ratio() == 1:
                                isAddLine = True
                            # break
                elif value in line:
                    if '/' in sp:
                        for s in sp.split('/'):
                            if s in line:
                                sp = s
                                break
                    if '/' in sp:
                        complete_value = value
                    else:
                        complete_value = sp + value
                    if score < difflib.SequenceMatcher(None, complete_value, line).ratio():
                        if difflib.SequenceMatcher(None, complete_value, line).ratio() >= 0.6:
                            score = difflib.SequenceMatcher(None, complete_value, line).ratio()
                            # target = key
                            if difflib.SequenceMatcher(None, complete_value, line).ratio() == 1:
                                isAddLine = True
                            break
                        # else:
                        #     if line.find(complete_value) == 0:
                        # target = key

        return target, isAddLine

    def getFileSignals(self):
        signals = []
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        for line in lines:
            spans = line.findAll("span")
            line_content = ""
            for span in spans:
                line_content = line_content + span.getText()

            line_content = line_content.replace('\u3000', '').replace('\u0020', '').replace('\u00A0', '')
            attrs = line.attrs
            if attrs.get('pattern') is None:
                sp, isAddLine = self.get_key_new(line_content, attrs.get('id'))
            elif '/' in attrs['pattern']:
                sp, isAddLine = self.get_key_new(line_content, attrs.get('id'))
            else:
                sp = attrs['pattern']

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue
            signals.append(mappingKey)

        print(signals)
        return signals

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

    def getSchemaAttr(self, leftStr):
        attr = ""
        for key, value in self.schema_dtd.items():
            if value == '':
                continue
            if isinstance(value, list):
                for i in value:
                    if "/" in i:
                        sp_list = i.split("/")
                        if leftStr in sp_list:
                            attr = key
                            break
                    else:
                        if leftStr in i:
                            attr = key
                            break
                if attr != "":
                    break
            else:
                if "/" in value:
                    sp_list = value.split("/")
                    if leftStr in sp_list:
                        attr = key
                        break
                else:
                    if leftStr in value:
                        attr = key
                        break
        return attr

    def updateSchemaDtd(self, attr, leftStr):
        schema_dtd_json = json.loads(self.schemaInfo.get('dtd'))
        schema_pattern_list = self.schemaInfo.get('pattern_list')
        schema_pattern_list.append(leftStr)
        if '.' in attr:
            mainKey = attr.split('.')[0]
            subKey = attr.split('.')[1]
            if isinstance(schema_dtd_json[mainKey][subKey], list):
                if len(schema_dtd_json[mainKey][subKey][0]) > 0:
                    sp = schema_dtd_json[mainKey][subKey][0] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[mainKey][subKey][0] = sp
            else:
                if '/' in schema_dtd_json[mainKey][subKey]:
                    sp = schema_dtd_json[mainKey][subKey] + '/' + leftStr
                elif schema_dtd_json[mainKey][subKey] != "":
                    sp = schema_dtd_json[mainKey][subKey] + '/' + leftStr
                else:
                    sp = leftStr
                schema_dtd_json[mainKey][subKey] = sp
        else:
            if isinstance(schema_dtd_json[attr], list):
                if len(schema_dtd_json[attr][0]) > 0:
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

    def resetSignal(self, signals):
        original_inSignals = list()
        new_outSignals = list()
        new_inSignals = list()
        temp = ""
        for input in signals:
            # input = input[1:]
            if temp != input:
                original_inSignals.append(input)
                temp = input

        for input in original_inSignals:
            inSignal = self.getMappingKey(input)
            if isinstance(self.new_dtd[inSignal], str):
                new_inSignals.append("I" + input)
            else:
                list_length = len(self.new_dtd[inSignal])
                for i in range(0, list_length):
                    new_inSignals.append("I" + input)

        original_inSignals = list()
        for new_input in new_inSignals:
            input = new_input[1:]
            new_outSignals.append('O' + input)
            original_inSignals.append(input)

        return original_inSignals, new_inSignals, new_outSignals

    def resetRule(self, preSignal, inSignal, old, new):
        if preSignal != '':
            preSignal = self.getMappingValue(preSignal)
            preRule = self.rules.get(preSignal)
            if len(preRule) != 0:
                if old == '':
                    if preRule['right_LM'] == '':
                        preRule['right_LM'] = new
                    else:
                        if preRule['right_LM'] != new:
                            preRule['right_LM'] = preRule['right_LM'] + '||' + new
                else:
                    preRule['right_LM'] = preRule['right_LM'].replace(old, new)

        inSignal = self.getMappingValue(inSignal)
        inRule = self.rules.get(inSignal)
        if len(inRule) != 0:
            if old == '':
                if inRule['left_LM'] == '':
                    inRule['left_LM'] = new
                else:
                    inRule['left_LM'] = inRule['left_LM'] + '||' + new
            else:
                inRule['left_LM'] = inRule['left_LM'].replace(old, new)

    def has_punctuation(self, line):
        from zhon.hanzi import punctuation
        import string
        punctuations = re.findall(r"[%s]+" % punctuation, line)
        result = False
        if len(punctuations) > 0:
            result = True

        punctuations = re.findall(r"[%s]+" % string.punctuation, line)
        if len(punctuations) > 0:
            result = True

        return result

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            pass

        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            pass

        return False

    def hasNumber(self, stringVal):
        return any(elem.isdigit() for elem in stringVal)

    def updateRules_new(self):
        signals = self.getFileSignals()
        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))
        # signals, inSignals, outSignals = self.resetSignal(signals)
        value_idx = 0
        signal_idx = 0
        line_idx = 0
        while (line_idx < len(line_info)) and (signal_idx < len(signals)):
            line_content = line_info[line_idx].get('line_content').replace('\u3000', '').replace('\u0020', '').replace(
                '\u00A0', '')
            preLine = ""
            if line_idx != 0:
                preLine = line_info[line_idx - 1].get('line_content').replace('\u3000', '').replace('\u0020',
                                                                                                    '').replace(
                    '\u00A0', '')
            nextLine = ""
            if line_idx != len(line_info) - 1:
                nextLine = line_info[line_idx + 1].get('line_content').replace('\u3000', '').replace('\u0020',
                                                                                                     '').replace(
                    '\u00A0', '')
            if signals[signal_idx] not in self.rules.keys():
                self.rules[signals[signal_idx]] = {}

            pre_signal = ""
            if signal_idx != 0:
                pre_signal = signals[signal_idx - 1]
            next_signal = ""
            if signal_idx != len(signals) - 1:
                next_signal = signals[signal_idx + 1]

            current_signal = self.getMappingKey(signals[signal_idx])
            pre_signal = self.getMappingKey(pre_signal)
            next_signal = self.getMappingKey(next_signal)

            pattern = ""
            attr = line_info[line_idx]['attr']
            if attr.get('pattern') is not None:
                pattern = attr.get('pattern')
            if attr.get('id') not in self.getLineId(current_signal):
                line_idx = line_idx + 1
                continue

            in_sp = ""
            out_sp = ""
            current_value = ""
            pre_value = ""
            next_value = ""

            if pre_signal != "":
                if isinstance(self.new_dtd[pre_signal], list):
                    pre_value = ''.join(self.new_dtd[pre_signal])
                else:
                    pre_value = self.new_dtd[pre_signal]

            if current_signal != "":
                if isinstance(self.schema_dtd[current_signal], list):
                    in_sp = self.schema_dtd[current_signal][0]
                else:
                    in_sp = self.schema_dtd[current_signal]

                if isinstance(self.new_dtd[current_signal], list):
                    current_value = ''.join(self.new_dtd[current_signal])
                    if pattern != '':
                        for idx, value in enumerate(self.new_dtd[current_signal]):
                            if value in line_content:
                                value_idx = idx
                                break
                        current_value = self.new_dtd[current_signal][value_idx]
                else:
                    current_value = self.new_dtd[current_signal]

            if next_signal != "":
                if isinstance(self.schema_dtd[next_signal], list):
                    out_sp = self.schema_dtd[next_signal][0]
                else:
                    out_sp = self.schema_dtd[next_signal]

                if isinstance(self.new_dtd[next_signal], list):
                    next_value = ''.join(self.new_dtd[next_signal])
                else:
                    next_value = self.new_dtd[next_signal]

            # if ('/' in in_sp) and (line_content in in_sp.split('/')):
            #     line_idx = line_idx + 1
            #     continue
            # elif ('/' not in in_sp) and (line_content == in_sp):
            #     line_idx = line_idx + 1
            #     continue

            # if (line_content not in current_value) and (current_value not in line_content) or (line_content in in_sp.split('/')):
            #     line_idx = line_idx + 1
            #     continue

            left_LM = ""
            right_LM = ""
            if self.filetype == 'table':
                if line_content == current_value:
                    left_LM = " "
                    if (in_sp == preLine) and (preLine != ''):
                        left_LM = left_LM + "||" + in_sp + "||" + "\n"
                    elif (pre_value not in preLine) and (preLine not in pre_value) and (
                    not self.has_punctuation(preLine)):
                        left_LM = left_LM + "||" + preLine + "||" + "\n"

                    if (out_sp != '') and (out_sp in nextLine):
                        right_LM = out_sp
                    elif (next_value not in nextLine) and (nextLine not in next_value) and (
                    not self.has_punctuation(nextLine)):
                        right_LM = nextLine
                    else:
                        right_LM = "\n"
                elif line_content in current_value:
                    if pattern == "":
                        left_LM = " "
                        if (in_sp == preLine) and (preLine != ''):
                            left_LM = left_LM + "||" + in_sp + "||" + "\n"
                        elif (pre_value not in preLine) and (preLine not in pre_value):
                            left_LM = left_LM + "||" + preLine + "||" + "\n"

                        if (out_sp != '') and (out_sp in nextLine):
                            right_LM = out_sp
                        elif (next_value not in nextLine) and (nextLine not in next_value):
                            right_LM = nextLine

                        if re.match(
                                r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                line_content):
                            if right_LM == "":
                                right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                            else:
                                right_LM = right_LM + "||" + "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"

                        if re.match(r'^[0-9]\S*', line_content):
                            if right_LM == "":
                                right_LM = "(0|1|2|3|4|5|6|7|8|9)"
                            else:
                                right_LM = right_LM + "||" + "(0|1|2|3|4|5|6|7|8|9)"

                        # if (nextLine == '') and (right_LM == ''):
                        #     right_LM = '\n'
                    else:
                        print("warning!")
            elif self.filetype == 'FS':
                if line_content == current_value:
                    left_LM = " "
                    if ((in_sp == preLine) or (preLine in in_sp)) and (preLine != ''):
                        left_LM = left_LM + "||" + in_sp + "||" + "\n"
                    elif (preLine != '') and (preLine not in self.schemaInfo['pattern_list']) and \
                            (not self.is_number(preLine)) and (not self.hasNumber(preLine)) and (
                            (not self.has_punctuation(preLine)) or ('-' in preLine)):
                        self.schema_dtd = self.getNewSchemaDtd()
                        self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                        new_dtd = self.getNewSchemaDtd()
                        if isinstance(new_dtd[current_signal], list):
                            old_attr_sp = self.schema_dtd[current_signal][0]
                            new_attr_sp = new_dtd[current_signal][0]
                        else:
                            old_attr_sp = self.schema_dtd[current_signal]
                            new_attr_sp = new_dtd[current_signal]

                        in_sp = new_attr_sp
                        if len(self.rules) != 0:
                            self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                        self.schema_dtd = self.getNewSchemaDtd()
                        left_LM = left_LM + "||" + in_sp + "||" + "\n"
                        print(self.rules)
                    elif ((pre_value == '') or (pre_value not in preLine)) and (preLine not in pre_value) and (
                    not self.is_number(preLine)) and (not self.hasNumber(preLine)):
                        left_LM = left_LM + "||" + preLine + "||" + "\n"

                    if (out_sp != '') and (out_sp in nextLine):
                        right_LM = out_sp
                    elif (next_value not in nextLine) and (nextLine not in next_value) and (
                    not self.is_number(nextLine)) and (not self.hasNumber(nextLine)):
                        right_LM = nextLine
                    else:
                        right_LM = "\n"
                elif current_value in line_content:
                    sp = in_sp
                    if '/' in in_sp:
                        for s in in_sp.split('/'):
                            if s in line_content:
                                sp = s
                                break
                    complete_line = sp + current_value
                    if line_content == complete_line:
                        left_LM = in_sp
                    else:
                        toIdx = line_content.find(current_value)
                        if '/' in in_sp:
                            sp_list = in_sp.split('/')
                        else:
                            sp_list = in_sp

                        if toIdx > 0:
                            leftStr = line_content[:toIdx]
                            if leftStr not in sp_list:
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, leftStr)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                if len(self.rules) != 0:
                                    in_sp = new_attr_sp
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)

                        left_LM = in_sp
                    if line_content.find(current_value) + len(current_value) < len(line_content):
                        right_LM = " "
                    elif '/' in out_sp:
                        for s in out_sp.split('/'):
                            if difflib.SequenceMatcher(None, s, nextLine).ratio() >= 0.9:
                                right_LM = out_sp
                                break
                            elif (s in nextLine) and (nextLine.find(s) == 0):
                                right_LM = out_sp
                                break
                    if right_LM == '':
                        if (out_sp != '') and (out_sp in nextLine):
                            right_LM = out_sp
                        elif (next_value not in nextLine) and (nextLine not in next_value) and (
                        not self.is_number(nextLine)) and (not self.hasNumber(nextLine)):
                            right_LM = nextLine
                        elif (next_value == '') and (nextLine != ''):
                            right_LM = nextLine
                        else:
                            right_LM = "\n"
            else:
                if line_content == current_value:
                    left_LM = " "
                    if '/' in in_sp:
                        if self.filetype == 'form':
                            if (preLine not in in_sp.split('/')) and (preLine not in current_value) and (
                                    preLine not in self.schemaInfo['pattern_list']):
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                in_sp = new_attr_sp
                                if len(self.rules) != 0:
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)
                        else:
                            preLine = preLine.replace(':', '').replace('：', '')
                            if (preLine not in in_sp.split('/')) and (preLine not in current_value) and (
                            not self.has_punctuation(preLine)):
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                in_sp = new_attr_sp
                                if len(self.rules) != 0:
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)

                        if (preLine in in_sp.split('/')) or (preLine == in_sp):
                            left_LM = left_LM + "||" + in_sp + "||" + "\n"
                    elif ('/' not in in_sp) and (in_sp != ''):
                        if self.filetype == 'form':
                            if (preLine not in in_sp.split('/')) and (preLine not in current_value) and (
                                    preLine not in self.schemaInfo['pattern_list']):
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                in_sp = new_attr_sp
                                if len(self.rules) != 0:
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)
                        else:
                            preLine = preLine.replace(':', '').replace('：', '')
                            if (preLine != in_sp) and (preLine not in current_value) and (
                            not self.has_punctuation(preLine)):
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                in_sp = new_attr_sp
                                if len(self.rules) != 0:
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)

                        if (preLine in in_sp.split('/')) or (preLine == in_sp):
                            left_LM = left_LM + "||" + in_sp + "||" + "\n"
                    elif (pre_value not in preLine) and (preLine not in pre_value) and (
                    not self.has_punctuation(preLine)):
                        left_LM = left_LM + "||" + preLine + "||" + "\n"

                    if '/' in out_sp:
                        for s in out_sp.split('/'):
                            if difflib.SequenceMatcher(None, s, nextLine).ratio() >= 0.9:
                                right_LM = out_sp
                                break
                            elif (s in nextLine) and (nextLine.find(s) == 0):
                                right_LM = out_sp
                                break
                    if right_LM == '':
                        if (out_sp != '') and (out_sp in nextLine):
                            right_LM = out_sp
                        elif (next_value not in nextLine) and (nextLine not in next_value):
                            right_LM = nextLine
                        elif (next_value == '') and (nextLine != ''):
                            right_LM = nextLine
                        else:
                            right_LM = "\n"
                elif current_value in line_content:
                    sp = in_sp
                    if '/' in in_sp:
                        for s in in_sp.split('/'):
                            if s in line_content:
                                sp = s
                                break
                    complete_line = sp + current_value
                    if line_content == complete_line:
                        left_LM = in_sp
                    else:
                        toIdx = line_content.find(current_value)
                        if '/' in in_sp:
                            sp_list = in_sp.split('/')
                        else:
                            sp_list = in_sp

                        if toIdx > 0:
                            leftStr = line_content[:toIdx]
                            if leftStr not in sp_list:
                                self.schema_dtd = self.getNewSchemaDtd()
                                self.schemaInfo = self.updateSchemaDtd(current_signal, leftStr)
                                new_dtd = self.getNewSchemaDtd()
                                if isinstance(new_dtd[current_signal], list):
                                    old_attr_sp = self.schema_dtd[current_signal][0]
                                    new_attr_sp = new_dtd[current_signal][0]
                                else:
                                    old_attr_sp = self.schema_dtd[current_signal]
                                    new_attr_sp = new_dtd[current_signal]

                                if len(self.rules) != 0:
                                    in_sp = new_attr_sp
                                    self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                self.schema_dtd = self.getNewSchemaDtd()
                                print(self.rules)
                                pattern = current_signal
                        left_LM = in_sp
                    if line_content.find(current_value) + len(current_value) < len(line_content):
                        right_LM = " "
                    elif '/' in out_sp:
                        for s in out_sp.split('/'):
                            if difflib.SequenceMatcher(None, s, nextLine).ratio() >= 0.9:
                                right_LM = out_sp
                                break
                            elif (s in nextLine) and (nextLine.find(s) == 0):
                                right_LM = out_sp
                                break
                    if right_LM == '':
                        if (out_sp != '') and (out_sp in nextLine):
                            right_LM = out_sp
                        elif (next_value not in nextLine) and (nextLine not in next_value):
                            right_LM = nextLine
                        elif (next_value == '') and (nextLine != ''):
                            right_LM = nextLine
                        else:
                            right_LM = "\n"
                else:
                    if line_content in current_value:
                        if pattern == "":
                            left_LM = " "
                            if '/' in in_sp:
                                if self.filetype == 'form':
                                    if (preLine not in in_sp.split('/')) and (preLine not in current_value) and (
                                            preLine not in self.schemaInfo['pattern_list']):
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                        new_dtd = self.getNewSchemaDtd()
                                        if isinstance(new_dtd[current_signal], list):
                                            old_attr_sp = self.schema_dtd[current_signal][0]
                                            new_attr_sp = new_dtd[current_signal][0]
                                        else:
                                            old_attr_sp = self.schema_dtd[current_signal]
                                            new_attr_sp = new_dtd[current_signal]

                                        in_sp = new_attr_sp
                                        if len(self.rules) != 0:
                                            self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        print(self.rules)
                                else:
                                    preLine = preLine.replace(':', '').replace('：', '')
                                    if (preLine not in in_sp.split('/')) and \
                                            (preLine not in current_value.replace(':', '').replace('：', '')) and \
                                            (not self.has_punctuation(preLine)):
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                        new_dtd = self.getNewSchemaDtd()
                                        if isinstance(new_dtd[current_signal], list):
                                            old_attr_sp = self.schema_dtd[current_signal][0]
                                            new_attr_sp = new_dtd[current_signal][0]
                                        else:
                                            old_attr_sp = self.schema_dtd[current_signal]
                                            new_attr_sp = new_dtd[current_signal]

                                        if len(self.rules) != 0:
                                            in_sp = new_attr_sp
                                            self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        print(self.rules)

                                if (preLine in in_sp.split('/')) or (preLine == in_sp):
                                    left_LM = left_LM + "||" + in_sp + "||" + "\n"
                            elif ('/' not in in_sp) and (in_sp != ''):
                                if self.filetype == 'form':
                                    if (preLine not in in_sp.split('/')) and (preLine not in current_value) and (
                                            preLine not in self.schemaInfo['pattern_list']):
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                        new_dtd = self.getNewSchemaDtd()
                                        if isinstance(new_dtd[current_signal], list):
                                            old_attr_sp = self.schema_dtd[current_signal][0]
                                            new_attr_sp = new_dtd[current_signal][0]
                                        else:
                                            old_attr_sp = self.schema_dtd[current_signal]
                                            new_attr_sp = new_dtd[current_signal]

                                        in_sp = new_attr_sp
                                        if len(self.rules) != 0:
                                            self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        print(self.rules)
                                else:
                                    preLine = preLine.replace(':', '').replace('：', '')
                                    if (preLine != in_sp) and (in_sp not in preLine) and (
                                            preLine not in current_value) and (not self.has_punctuation(preLine)):
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        self.schemaInfo = self.updateSchemaDtd(current_signal, preLine)
                                        new_dtd = self.getNewSchemaDtd()
                                        if isinstance(new_dtd[current_signal], list):
                                            old_attr_sp = self.schema_dtd[current_signal][0]
                                            new_attr_sp = new_dtd[current_signal][0]
                                        else:
                                            old_attr_sp = self.schema_dtd[current_signal]
                                            new_attr_sp = new_dtd[current_signal]

                                        in_sp = new_attr_sp
                                        if len(self.rules) != 0:
                                            self.resetRule(pre_signal, current_signal, old_attr_sp, new_attr_sp)
                                        self.schema_dtd = self.getNewSchemaDtd()
                                        print(self.rules)

                                if preLine in in_sp.split('/'):
                                    left_LM = left_LM + "||" + in_sp + "||" + "\n"
                            elif in_sp == preLine:
                                left_LM = left_LM + "||" + in_sp + "||" + "\n"
                            elif (pre_value not in preLine) and (preLine not in pre_value) and (
                            not self.has_punctuation(preLine)):
                                left_LM = left_LM + "||" + preLine + "||" + "\n"

                            if '/' in out_sp:
                                for s in out_sp.split('/'):
                                    if difflib.SequenceMatcher(None, s, nextLine).ratio() >= 0.9:
                                        right_LM = out_sp
                                        break
                                    elif (s in nextLine) and (nextLine.find(s) == 0):
                                        right_LM = out_sp
                                        break
                            if right_LM == '':
                                if (out_sp != '') and (out_sp in nextLine):
                                    right_LM = out_sp
                                # elif (out_sp == '') and (out_sp in nextLine) and (current_signal != next_signal):
                                #     right_LM = nextLine[:4]
                                # elif re.match(
                                #         r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                #         line_content):
                                #     right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                                elif (next_value not in nextLine) and (nextLine not in next_value):
                                    right_LM = nextLine
                                elif (next_value == '') and (nextLine != ''):
                                    right_LM = nextLine

                            if re.match(
                                    r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                    line_content):
                                if right_LM == "":
                                    right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                                else:
                                    right_LM = right_LM + "||" + "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"

                            if re.match(r'^[0-9]\S*', line_content):
                                if right_LM == "":
                                    right_LM = "(0|1|2|3|4|5|6|7|8|9)"
                                else:
                                    right_LM = right_LM + "||" + "(0|1|2|3|4|5|6|7|8|9)"
                        else:
                            print("warning!")
                    elif (in_sp in line_content) and (line_content in in_sp + current_value):
                        left_LM = in_sp
                        if (out_sp != '') and (out_sp in nextLine):
                            right_LM = out_sp
                        elif (next_value not in nextLine) and (nextLine not in next_value):
                            right_LM = nextLine
                        elif (next_value == '') and (nextLine != ''):
                            right_LM = nextLine

            rule_structure = {
                "line_pattern": pattern,
                "line_id": attr.get('id'),
                "left_LM": left_LM,
                "right_LM": right_LM
            }

            if len(self.rules[signals[signal_idx]]) == 0:
                self.rules[signals[signal_idx]] = rule_structure
            else:
                rule = copy.deepcopy(self.rules.get(signals[signal_idx]))
                left_LM = list()
                right_LM = list()
                if '||' in rule.get('left_LM'):
                    left_LM = rule.get('left_LM').split('||')
                else:
                    left_LM.append(rule.get('left_LM'))

                if '||' in rule.get('right_LM'):
                    right_LM = rule.get('right_LM').split('||')
                else:
                    right_LM.append(rule.get('right_LM'))

                rule_left = list()
                rule_right = list()
                if '||' in rule_structure['left_LM']:
                    rule_left = rule_structure['left_LM'].split('||')
                else:
                    rule_left.append(rule_structure['left_LM'])

                for left in rule_left:
                    if (left not in left_LM) and (left != ""):
                        if rule.get('left_LM') == "":
                            rule['left_LM'] = left
                        else:
                            rule['left_LM'] = rule.get('left_LM') + "||" + left

                if '||' in rule_structure['right_LM']:
                    rule_right = rule_structure['right_LM'].split('||')
                else:
                    rule_right.append(rule_structure['right_LM'])

                for right in rule_right:
                    if (right not in right_LM) and (right != ""):
                        if rule.get('right_LM') == "":
                            rule['right_LM'] = right
                        else:
                            rule['right_LM'] = rule.get('right_LM') + "||" + right
                if rule_structure['line_pattern'] != '':
                    rule['line_pattern'] = rule_structure['line_pattern']

                line_list = rule.get('line_id').split(',')
                line_id = rule_structure['line_id']
                if line_id not in line_list:
                    line_list.append(line_id)
                    rule['line_id'] = ','.join(line_list)

                self.rules[signals[signal_idx]] = rule

            # if signal_temp != current_signal:
            #     signal_temp = current_signal

            signal_idx = signal_idx + 1
            line_idx = line_idx + 1
        print(self.rules)

    def updateRules(self, signals):
        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))
        signals, inSignals, outSignals = self.resetSignal(signals)
        value_idx = -1
        out_temp = ''
        for idx, out in enumerate(outSignals):
            if out_temp != out:
                out_temp = out
                value_idx = 0
            else:
                value_idx = value_idx + 1
            signal = signals[idx]
            if signal not in self.rules.keys():
                self.rules[signal] = {}
            inSignal = signal
            preSignal = ""
            if idx != 0:
                preSignal = signals[idx - 1]
            nextSignal = ""
            if idx != len(outSignals) - 1:
                nextSignal = signals[idx + 1]
            inSignal = self.getMappingKey(inSignal)
            preSignal = self.getMappingKey(preSignal)
            nextSignal = self.getMappingKey(nextSignal)
            in_value = self.new_dtd[inSignal]
            pos_file = self.fileInfo['position']
            if '.' in inSignal:
                main = inSignal.split('.')[0]
                sub = inSignal.split('.')[1]
                pos = pos_file[main][sub]
            else:
                pos = pos_file[inSignal]

            if isinstance(pos, list):
                pos = pos[value_idx]

            position = json.loads(pos)
            lineIds = position['lineId']

            line_id = int(lineIds[0].split('-')[1])
            lineInfo = line_info[line_id]

            pattern = ""
            attr = lineInfo['attr']
            if attr.get('pattern') is not None:
                pattern = attr.get('pattern')

            content = lineInfo['line_content']
            if isinstance(in_value, list):
                in_value = in_value[value_idx]

            in_sp = ""
            out_sp = ""

            if inSignal != "":
                if isinstance(self.schema_dtd[inSignal], list):
                    in_sp = self.schema_dtd[inSignal][0]
                else:
                    in_sp = self.schema_dtd[inSignal]

            if nextSignal != "":
                if isinstance(self.schema_dtd[nextSignal], list):
                    out_sp = self.schema_dtd[nextSignal][0]
                else:
                    out_sp = self.schema_dtd[nextSignal]

            if pattern == "":
                if content == in_value:
                    if in_sp == "":
                        left_LM = " "
                        if nextSignal == "":
                            right_LM = "\n"
                        else:
                            if out_sp == "":
                                right_LM = "\n"
                            else:
                                right_LM = out_sp
                    else:
                        if preSignal == "":
                            left_LM = " "
                        elif preSignal == inSignal:
                            left_LM = " "
                        else:
                            left_LM = in_sp + "||\n"

                        if nextSignal == "":
                            right_LM = "\n"
                        elif nextSignal == inSignal:
                            if re.match(
                                    r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                    content):
                                right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                            else:
                                right_LM = "\n"
                        else:
                            if out_sp == "":
                                right_LM = "\n"
                            else:
                                right_LM = out_sp
                else:
                    startIdx = content.find(in_value)
                    if startIdx == -1:
                        startIdx = content.replace('\u3000', '').find(in_value)

                    if isinstance(self.schema_dtd[inSignal], list):
                        if '/' in self.schema_dtd[inSignal][0]:
                            sp_list = self.schema_dtd[inSignal][0].split('/')
                        else:
                            sp_list = self.schema_dtd[inSignal][0]
                    else:
                        if '/' in self.schema_dtd[inSignal]:
                            sp_list = self.schema_dtd[inSignal].split('/')
                        else:
                            sp_list = self.schema_dtd[inSignal]

                    if startIdx > 0:
                        leftStr = content[0:startIdx].replace('\u3000', '')
                        if leftStr not in sp_list:
                            self.schemaInfo = self.updateSchemaDtd(inSignal, leftStr)
                            new_dtd = self.getNewSchemaDtd()
                            if isinstance(new_dtd[inSignal], list):
                                old_attr_sp = self.schema_dtd[inSignal][0]
                                new_attr_sp = new_dtd[inSignal][0]
                            else:
                                old_attr_sp = self.schema_dtd[inSignal]
                                new_attr_sp = new_dtd[inSignal]

                            if len(self.schemaInfo['extraction_rules']) != 0:
                                in_sp = new_attr_sp
                                self.resetRule(preSignal, inSignal, old_attr_sp, new_attr_sp)
                            print(self.schemaInfo)

                    if in_sp == "":
                        left_LM = " "

                        if nextSignal == "":
                            right_LM = "\n"
                        else:
                            right_LM = out_sp
                    else:
                        if preSignal == "":
                            left_LM = " "
                        elif preSignal == inSignal:
                            if re.match(
                                    r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                    content):
                                left_LM = " "
                            else:
                                left_LM = in_sp + "||\n"
                        else:
                            left_LM = in_sp + "||\n"

                        if nextSignal == "":
                            right_LM = "\n"
                        elif nextSignal == inSignal:
                            if re.match(
                                    r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                    content):
                                right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                            else:
                                right_LM = "\n"
                        else:
                            if out_sp == "":
                                right_LM = "\n"
                            else:
                                right_LM = out_sp
            else:
                startIdx = content.replace('\u3000', '').find(in_value)
                if startIdx == 0:
                    left_LM = " "
                else:
                    if preSignal == "":
                        left_LM = " "
                    elif preSignal == inSignal:
                        if re.match(
                                r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                                content):
                            left_LM = " "
                        else:
                            left_LM = in_sp + "||\n"
                    else:
                        left_LM = in_sp + "||\n"

                if nextSignal == "":
                    right_LM = "\n"
                elif nextSignal == inSignal:
                    if re.match(
                            r'^(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)\S*',
                            content):
                        right_LM = "(\u4E00|\u4E8C|\u4E09|\u56DB|\u4E94|\u516D|\u4E03|\u516B|\u4E5D|\u5341|\u58F9|\u8CB3|\u53C3|\u8086|\u4F0D|\u9678|\u67D2|\u634C|\u7396|\u62FE)"
                    else:
                        right_LM = "\n"
                else:
                    if out_sp == "":
                        right_LM = "\n"
                    else:
                        right_LM = out_sp

            rule_structure = {
                "line_id": lineIds,
                "line_pattern": pattern,
                "left_LM": left_LM,
                "right_LM": right_LM
            }

            if len(self.rules[signal]) == 0:
                self.rules[signal] = rule_structure
            else:
                rule = copy.deepcopy(self.rules.get(signal))
                left_LM = list()
                right_LM = list()
                if '||' in rule.get('left_LM'):
                    left_LM = rule.get('left_LM').split('||')
                else:
                    left_LM.append(rule.get('left_LM'))

                if '||' in rule.get('right_LM'):
                    right_LM = rule.get('right_LM').split('||')
                else:
                    right_LM.append(rule.get('right_LM'))

                rule_left = list()
                rule_right = list()
                if '||' in rule_structure['left_LM']:
                    rule_left = rule_structure['left_LM'].split('||')
                else:
                    rule_left.append(rule_structure['left_LM'])

                for left in rule_left:
                    if left not in left_LM:
                        rule['left_LM'] = rule.get('left_LM') + "||" + left

                if '||' in rule_structure['right_LM']:
                    rule_right = rule_structure['right_LM'].split('||')
                else:
                    rule_right.append(rule_structure['right_LM'])

                for right in rule_right:
                    if right not in right_LM:
                        rule['right_LM'] = rule.get('right_LM') + "||" + right

                line_list = rule.get('line_id')
                for lineId in lineIds:
                    if lineId not in line_list:
                        line_list.append(lineId)

                self.rules[signal] = rule

        print(self.rules)

    def learning(self):
        # self.updateMealyFst()
        # fstMealy = fst(initState=self.mealy_fst['initState'],
        #                states=self.mealy_fst['states'],
        #                transitionFunction=self.mealy_fst['transitionFunction'],
        #                outputFunction=self.mealy_fst['outputFunction'],
        #                finalStates=self.mealy_fst['finalStates'])
        # graph = graphviz.Source(fstUtils.toDot(fstMealy))
        # graph.view('fst_graph_mealy', cleanup=True)

        # self.updateMooreFst()
        # fstMoore = fst(initState=self.moore_fst['initState'],
        #                states=self.moore_fst['states'],
        #                transitionFunction=self.moore_fst['transitionFunction'],
        #                outputFunction=self.moore_fst['outputFunction'],
        #                finalStates=self.moore_fst['finalStates'])
        # graph = graphviz.Source(fstUtils.toDot(fstMoore))
        # graph.view('fst_graph_moore', cleanup=True)

        self.updateSoftmealy()
        fstSoftmealy = SoftMealy(initState=self.softmealy_fst['initState'],
                                 states=self.softmealy_fst['states'],
                                 inAlphabet=self.softmealy_fst['inAlphabet'],
                                 outAlphabet=self.softmealy_fst['outAlphabet'],
                                 transitionFunction=self.softmealy_fst['transitionFunction'],
                                 outputFunction=self.softmealy_fst['outputFunction'],
                                 finalStates=self.softmealy_fst['finalStates'])
        fstSoftmealy.exportDigraph()
        print("updated FST")

        # signals = self.getFileSignals()
        # outSignals = [fstSoftmealy.step(symbol) for symbol in inSignals]
        # signals, inSignals, outSignals = self.resetSignal(inSignals)
        # outSignals, outStates = fstMoore.playFST(inSignals)
        # # self.sortOutRules(outSignals)
        # self.updateRules(signals)
        self.updateRules_new()

        print("Rule Extraction")
        return self.mealy_fst, self.moore_fst, self.softmealy_fst, self.rules

    def getRule(self, state):
        return self.rules.get(state)

    def init_dtd(self):
        structure = self.dtd
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

    def prepare_LM(self, state_LM):
        LM = list()
        if '||' in state_LM:
            tmp_LM = state_LM.split('||')
            for tmp in tmp_LM:
                if '/' in tmp:
                    ll = tmp.split('/')
                    for mm in ll:
                        LM.append(mm)
                else:
                    LM.append(tmp)
        elif '/' in state_LM:
            ll = state_LM.split('/')
            for mm in ll:
                LM.append(mm)
        else:
            LM.append(state_LM)

        return LM

    def goExtract(self, last_line, current_line, input_symbol, vs_size):
        ok = False
        pattern = ''
        left_LM = self.prepare_LM(input_symbol.get('left_LM'))
        current_line_attr = current_line.get('attr')
        current_line_content = current_line.get('line_content').replace('\u3000', '').replace('\u0020', '').replace(
            '\u00A0', '').replace('\xa0', '').replace('\x00', '')
        last_line_content = last_line.get('line_content').replace('\u3000', '').replace('\u0020', '').replace(
            '\u00A0', '').replace('\xa0', '').replace('\x00', '')

        if current_line_attr.get('pattern') is None:
            if (input_symbol.get('pattern') == "") & (len(left_LM) == 1) & (left_LM[0] == " "):
                ok = True
            elif (input_symbol.get('pattern') == "") & (last_line_content in left_LM):
                ok = True
            elif (input_symbol.get('pattern') == "") & (current_line_content in left_LM):
                ok = False
            elif (self.filetype == 'form') and (input_symbol.get('pattern') == ""):
                if ('/' in current_line_content) and (current_line_content in input_symbol.get('left_LM').split('||')):
                    ok = False
            elif input_symbol.get('pattern') != "":
                for lm in left_LM:
                    if lm in current_line_content:
                        pattern = lm
                        ok = True
                        break
                    # elif lm in last_line_content:
                    #     ok = True
                    #     break
            else:
                for lm in left_LM:
                    if (lm in last_line_content) or (lm in current_line_content):
                        pattern = lm
                        ok = True
                        break
                    # elif lm == ' ':
                    #     ok = True
                    #     break
                    else:
                        # if lm in current_line_content:
                        ratio = difflib.SequenceMatcher(None, current_line_content, lm).ratio()
                        if (ratio >= 0.5) & (lm in current_line_content):
                            pattern = lm
                            ok = True
                            break
        else:
            if current_line_attr.get('pattern') == input_symbol.get('pattern'):
                if (len(left_LM) == 1) & (left_LM[0] == " "):
                    ok = True
                else:
                    for lm in left_LM:
                        # if lm in current_line_content:
                        ratio = difflib.SequenceMatcher(None, current_line_content, lm).ratio()
                        if ((ratio >= 0.5) | (current_line_content.find(lm) == 0)) & (lm in current_line_content):
                            pattern = lm
                            ok = True
                            break
            print('has pattern attr')

        if (self.filetype == 'table') and (vs_size > 1):
            input_line_list = input_symbol.get('line_id').split(',')
            if current_line_attr.get('id') not in input_line_list:
                ok = False
        return ok, pattern

    def goTransition(self, current_line, next_line, input_symbol):
        ok = False
        right_LM = self.prepare_LM(input_symbol.get('right_LM'))
        current_line = current_line.get('line_content').replace('\u3000', '').replace('\u0020', '').replace('\u00A0',
                                                                                                            '').replace(
            '\xa0', '').replace('\x00', '') + '\n'
        next_line = next_line.get('line_content').replace('\u3000', '').replace('\u0020', '').replace('\u00A0',
                                                                                                      '').replace(
            '\xa0', '').replace('\x00', '') + '\n'
        for lm in right_LM:
            ratio = difflib.SequenceMatcher(None, current_line, lm).ratio()
            is_punctuation = re.search(r'(\uFF1A|\uFF1B|\uFF1F)', current_line[-2])
            if (ratio >= 0.8) and is_punctuation:
                ok = True
                break
            if (lm in current_line) and (not is_punctuation):
                idx = current_line.find(lm)
                if (idx == 0) or (lm == '\n'):  # or (idx + len(lm) == len(current_line)):
                    ok = True
                    break
            ratio = difflib.SequenceMatcher(None, next_line, lm).ratio()
            is_punctuation = re.search(r'(\uFF1A|\uFF1B|\uFF1F)', next_line[-2])
            if (ratio >= 0.8) and is_punctuation:
                ok = True
                break
            if (lm in next_line) and (not is_punctuation):
                idx = next_line.find(lm)
                if (idx == 0) or (lm == '\n'):  # or (lm + '\n' == next_line[-len(lm + '\n'):]):
                    ok = True
                    break
        if (self.filetype == 'form') and (next_line == input_symbol.get('right_LM')):
            ok = True

        return ok

    def getPosition(self, value, color_info):
        position = {
            "lineId": [],
            "start": -1,
            "end": -1,
            "color": {}
        }
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        for line in lines:
            line_content = line.text
            spans = line.findAll("span")
            attrs = line.attrs

            if line_content in value:
                # 這個屬性的value可能存在於文章的多行
                if difflib.SequenceMatcher(None, value, line_content).ratio() == 1:
                    position["lineId"].append(attrs.get('id'))
                    position["start"] = spans[0].attrs['data-value']
                    position["end"] = int(spans[len(spans) - 1].attrs['data-value']) + 1
                    position["color"] = color_info
                    break
                else:
                    ratio = 1
                    if ((len(line_content) / len(value)) < 0.5) & (line_content not in self.schemaInfo['pattern_list']):
                        ratio = len(line_content) / len(value)
                    if difflib.SequenceMatcher(None, value, line_content).ratio() >= 0.4 * ratio:
                        position["lineId"].append(attrs.get('id'))
                        position["color"] = color_info
                        if position["start"] == -1:
                            position["start"] = spans[0].attrs['data-value']
                        position["end"] = int(spans[len(spans) - 1].attrs['data-value']) + 1
            else:
                # 這個屬性的value存在該行的部分位置
                if '\u3000' in line_content:
                    if difflib.SequenceMatcher(None, value, line_content.replace('\u3000', '')).ratio() == 1:
                        position["lineId"].append(attrs.get('id'))
                        position["start"] = spans[0].attrs['data-value']
                        position["end"] = int(spans[len(spans) - 1].attrs['data-value']) + 1
                        position["color"] = color_info
                        break
                    elif difflib.SequenceMatcher(None, value, line_content.replace('\u3000', '')).ratio() >= 0.5:
                        startIdx = line_content.find(value)
                        position["lineId"].append(attrs.get('id'))
                        position["start"] = spans[startIdx].attrs['data-value']
                        position["end"] = int(spans[len(spans) - 1].attrs['data-value']) + 1
                        position["color"] = color_info
                        break
                    else:
                        line_content_split = line_content.split('\u3000')[1]
                        if difflib.SequenceMatcher(None, value, line_content_split).ratio() == 1:
                            startIdx = line_content.find(value)
                            position["lineId"].append(attrs.get('id'))
                            position["start"] = spans[startIdx].attrs['data-value']
                            position["end"] = int(spans[len(spans) - 1].attrs['data-value']) + 1
                            position["color"] = color_info
                            break

        print(json.dumps(position))
        return json.dumps(position)

    def extraction(self, attrList):
        fstSoftmealy = SoftMealy(initState=self.softmealy_fst['initState'],
                                 states=self.softmealy_fst['states'],
                                 inAlphabet=self.softmealy_fst['inAlphabet'],
                                 outAlphabet=self.softmealy_fst['outAlphabet'],
                                 transitionFunction=self.softmealy_fst['transitionFunction'],
                                 outputFunction=self.softmealy_fst['outputFunction'],
                                 finalStates=self.softmealy_fst['finalStates'])

        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))
        idx = 0
        keyword = ''
        u = fstSoftmealy.initState
        file_structure = self.init_dtd()
        file_position = copy.deepcopy(file_structure)
        print("Extract structure")
        position = {
            "lineId": [],
            "start": -1,
            "end": -1,
            "color": {}
        }
        while (u != 'GE') and (idx < len(line_info)):
            pre_u = u
            vs = fstSoftmealy.next_state(u)
            for i, v in enumerate(vs):
                current_state = v.get('next_state')
                u = current_state

                if u == 'last_updated':
                    print('!!!!!!!!!!!!!!')

                # check value of u is 'GE' or not
                if u == 'GE':
                    if i == len(vs) - 1:
                        break
                    continue
                if i == len(vs) - 1:
                    if '.' in current_state:
                        key1 = current_state.split('.')[0]
                        key2 = current_state.split('.')[1]
                        if isinstance(file_structure[key1][key2], list):
                            if len(file_structure[key1][key2]) > 0:
                                u = 'dummy/' + current_state
                                idx = idx + 1
                                continue
                        else:
                            if file_structure[key1][key2] != '':
                                u = 'dummy/' + current_state
                                idx = idx + 1
                                continue
                    else:
                        if isinstance(file_structure[current_state], list):
                            if len(file_structure[current_state]) > 0:
                                u = 'dummy/' + current_state
                                idx = idx + 1
                                continue
                        else:
                            if file_structure[current_state] != '':
                                u = 'dummy/' + current_state
                                idx = idx + 1
                                continue

                # if current_state == 'GE':
                #     if i == len(vs) - 1:
                #         u = 'GE'
                #         break
                #     continue

                rule_key = self.getMappingValue(current_state)
                state_rule = self.getRule(rule_key)
                input_signal = {
                    # 'line_id': state_rule['line_id'],
                    'pattern': state_rule['line_pattern'],
                    'left_LM': state_rule['left_LM']
                }

                output_signal = {
                    'right_LM': state_rule['right_LM']
                }

                attr_value = ''
                noExtract = False
                while idx < len(line_info):
                    if idx == 0:
                        last_line = line_info[idx]
                        current_line = line_info[idx]
                        next_line = line_info[idx + 1]
                    elif idx == len(line_info) - 1:
                        last_line = line_info[idx - 1]
                        current_line = line_info[idx]
                        next_line = line_info[idx]
                    else:
                        last_line = line_info[idx - 1]
                        current_line = line_info[idx]
                        next_line = line_info[idx + 1]

                    rlm = output_signal.get('right_LM').split(' ')
                    if '/' in output_signal.get('right_LM'):
                        rlm = output_signal.get('right_LM').split('/')
                    current_line_content = current_line.get('line_content').replace('\u3000', '') \
                        .replace('\u0020', '') \
                        .replace('\u00A0', '') \
                        .replace('\xa0', '') \
                        .replace('\x00', '')
                    # 識別出符合下一個準備提取屬性的觸發規則
                    if (keyword not in self.prepare_LM(input_signal.get('left_LM'))) and (
                            keyword not in input_signal.get('left_LM').split('||')):
                        go, pattern = self.goExtract(last_line, current_line, input_signal, len(vs))
                        if go:
                            noExtract = False
                            if input_signal.get('left_LM') == ' ':
                                startIdx = 0
                                attr_value = attr_value + current_line_content
                                # if '\u3000' in line_info[idx].get('line_content'):
                                #     attr_value = attr_value + line_info[idx].get('line_content').replace('\u3000', '')
                                # else:
                                #     attr_value = attr_value + line_info[idx].get('line_content')
                            # elif '\u3000' in line_info[idx].get('line_content'):
                            elif (input_signal.get('left_LM') != ' ') and (pattern != ''):
                                value = ''
                                startIdx = current_line_content.find(pattern)
                                if startIdx >= 0:
                                    endIdx = startIdx + len(pattern)
                                    value = current_line_content[endIdx:]
                                attr_value = attr_value + value

                                startIdx = current_line.get('line_content').find(attr_value)
                                if startIdx == -1:
                                    startIdx = current_line.get('line_content').find(pattern)
                                    startIdx = startIdx + len(pattern) + 1
                            else:
                                attr_value = attr_value + current_line_content
                                startIdx = 0

                            # 賦予呈現標示資訊
                            position["lineId"].append(line_info[idx].get('attr').get('id'))
                            span = line_info[idx].get('spans')
                            if position["start"] == -1:
                                position["start"] = span[startIdx].attrs['data-value']
                            position["end"] = int(span[len(span) - 1].attrs['data-value']) + 1

                            if (len(self.prepare_LM(input_signal.get('left_LM'))) > 1) and (
                                    ' ' in self.prepare_LM(input_signal.get('left_LM'))):
                                if (pattern != '') and (pattern in self.prepare_LM(input_signal.get('left_LM'))):
                                    keyword = pattern
                        else:
                            if current_line_content in self.prepare_LM(input_signal.get('left_LM')):
                                keyword = current_line_content
                                idx = idx + 1
                                continue
                            elif (self.filetype == 'form') and (
                                    current_line_content in input_signal.get('left_LM').split('||')):
                                keyword = current_line_content
                                idx = idx + 1
                                continue
                            else:
                                noExtract = True
                                if i == len(vs) - 1:
                                    idx = idx + 1
                                    if len(vs) > 1:
                                        noExtract = False
                                        u = pre_u
                                        break
                                    continue
                                break
                    elif (current_line_content in rlm) or (current_line_content == output_signal.get('right_LM')):
                        if i == len(vs) - 1:
                            u = 'dummy/' + current_state
                        keyword = ''
                        noExtract = False
                        break
                    else:
                        # if '\u3000' in line_info[idx].get('line_content'):
                        #     attr_value = attr_value + line_info[idx].get('line_content').split('\u3000')[1]
                        #     startIdx = line_info[idx].get('line_content').find(attr_value)
                        # else:
                        attr_value = attr_value + current_line_content
                        startIdx = 0

                        # 賦予呈現標示資訊
                        position["lineId"].append(line_info[idx].get('attr').get('id'))
                        span = line_info[idx].get('spans')
                        if position["start"] == -1:
                            position["start"] = span[startIdx].attrs['data-value']
                        position["end"] = int(span[len(span) - 1].attrs['data-value']) + 1

                    print('extract')

                    # 識別出符合提取屬性的轉移規則
                    if self.goTransition(current_line, next_line, output_signal):
                        noExtract = False
                        keyword = ''
                        if '.' in current_state:
                            key1 = current_state.split('.')[0]
                            key2 = current_state.split('.')[1]
                            position["color"] = next(item['color'] for item in attrList if item["level1"] == key1)
                            if isinstance(file_structure[key1][key2], list):
                                file_structure[key1][key2].append(attr_value)
                                file_position[key1][key2].append(json.dumps(position))
                            else:
                                file_structure[key1][key2] = attr_value
                                file_position[key1][key2] = json.dumps(position)

                        else:
                            position["color"] = next(
                                item['color'] for item in attrList if item["level1"] == current_state)
                            if isinstance(file_structure[current_state], list):
                                file_structure[current_state].append(attr_value)
                                file_position[current_state].append(json.dumps(position))
                            else:
                                file_structure[current_state] = attr_value
                                file_position[current_state] = json.dumps(position)

                        u = 'dummy/' + current_state
                        position = {
                            "lineId": [],
                            "start": -1,
                            "end": -1,
                            "color": {}
                        }
                        idx = idx + 1
                        break
                    else:
                        if '(' in output_signal.get('right_LM'):
                            right_LM = output_signal.get('right_LM').split('||')
                            right_LM = [s for s in right_LM if '(' in s]
                            nolist = list()
                            for r in right_LM:
                                right_LM = r.replace('(', '').replace(')', '')
                                nolist = nolist + right_LM.split('|')
                            if len(next_line.get('line_content')) >= 2:
                                if (next_line.get('line_content')[0] in nolist) and (
                                        (next_line.get('line_content')[1] == '、') or (
                                        next_line.get('line_content')[1] == '.')):
                                    noExtract = False
                                    if '.' in current_state:
                                        key1 = current_state.split('.')[0]
                                        key2 = current_state.split('.')[1]
                                        position["color"] = next(
                                            item['color'] for item in attrList if item["level1"] == key1)
                                        if isinstance(file_structure[key1][key2], list):
                                            file_structure[key1][key2].append(attr_value)
                                            file_position[key1][key2].append(json.dumps(position))
                                        else:
                                            file_structure[key1][key2] = attr_value
                                            file_position[key1][key2] = json.dumps(position)
                                    else:
                                        position["color"] = next(
                                            item['color'] for item in attrList if item["level1"] == current_state)
                                        if isinstance(file_structure[current_state], list):
                                            file_structure[current_state].append(attr_value)
                                            file_position[current_state].append(json.dumps(position))
                                        else:
                                            file_structure[current_state] = attr_value
                                            file_position[current_state] = json.dumps(position)

                                    u = 'dummy/' + current_state
                                    position = {
                                        "lineId": [],
                                        "start": -1,
                                        "end": -1,
                                        "color": {}
                                    }
                                    idx = idx + 1
                                    break
                                elif idx == len(line_info) - 1:
                                    noExtract = False
                                    if '.' in current_state:
                                        key1 = current_state.split('.')[0]
                                        key2 = current_state.split('.')[1]
                                        position["color"] = next(
                                            item['color'] for item in attrList if item["level1"] == key1)
                                        if isinstance(file_structure[key1][key2], list):
                                            file_structure[key1][key2].append(attr_value)
                                            file_position[key1][key2].append(json.dumps(position))
                                        else:
                                            file_structure[key1][key2] = attr_value
                                            file_position[key1][key2] = json.dumps(position)
                                    else:
                                        position["color"] = next(
                                            item['color'] for item in attrList if item["level1"] == current_state)
                                        if isinstance(file_structure[current_state], list):
                                            file_structure[current_state].append(attr_value)
                                            file_position[current_state].append(json.dumps(position))
                                        else:
                                            file_structure[current_state] = attr_value
                                            file_position[current_state] = json.dumps(position)

                    idx = idx + 1
                    # 跑完整個文章
                    if idx == len(line_info):
                        u = 'GE'

                if (i == len(vs) - 1) & noExtract:
                    u = 'GE'
                if u != current_state:
                    break

        # print("Sort out position")
        # keys1List = [key for key in file_structure]
        # for key1 in keys1List:
        #     color_info = next(item['color'] for item in attrList if item["level1"] == key1)
        #     type1 = type(file_structure[key1])
        #     if type1 == str:
        #         if file_structure[key1] != '':
        #             file_position[key1] = self.getPosition(file_structure[key1], color_info)
        #     elif type1 == dict:
        #         keys2List = [key for key in file_structure[key1]]
        #         for key2 in keys2List:
        #             type2 = type(file_structure[key1][key2])
        #             if type2 == str:
        #                 if file_structure[key1][key2] != '':
        #                     file_position[key1][key2] = self.getPosition(file_structure[key1][key2], color_info)
        #             elif type2 == list:
        #                 if len(file_structure[key1][key2]) > 0:
        #                     for value in file_structure[key1][key2]:
        #                         file_position[key1][key2].append(self.getPosition(value, color_info))
        #
        #     elif type1 == list:
        #         if len(file_structure[key1]) > 0:
        #             for value in file_structure[key1]:
        #                 file_position[key1].append(self.getPosition(value, color_info))

        return file_structure, file_position

# if __name__ == '__main__':
#     mealy = FST('2c7d75bb5c074aff8a5e1a24c628bf39', '63242c86c53041b8abd51eb374bfdeaa')
# fstMealy = fst(initState=mealy.fst['initState'],
#                states=mealy.fst['states'],
#                transitionFunction=mealy.fst['transitionFunction'],
#                outputFunction=[],
#                finalStates=mealy.fst['finalStates'])
#
# table = Markdown(fstUtils.toMdTable(fstMealy))
# display(table)
#
# display(graphviz.Source(fstUtils.toDot(fstMealy)))
# graph = graphviz.Source(fstUtils.toDot(fstMealy))
# graph.view('fst_graph', cleanup=True)
