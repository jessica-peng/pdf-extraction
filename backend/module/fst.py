import difflib
import json

from SciPyFST import fst, fstUtils
import graphviz
from bs4 import BeautifulSoup
from pandocfilters import stringify

from backend.database.entity import Entity

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

    def __init__(self, schemaId, fileId, dtd, source, mapping):
        self.schema = schemaId
        self.file = fileId
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

        if len(self.schemaInfo['moore_fst']) == 0:
            self.moore_fst = init_fst()
        else:
            self.moore_fst = self.schemaInfo['moore_fst']

        if len(self.schemaInfo['rules']) == 0:
            self.rules = {}
        else:
            self.rules = self.schemaInfo['rules']

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
        skip_line = []
        for line in lines:
            spams = line.findAll("spam")
            line_content = ""
            for spam in spams:
                line_content = line_content + spam.getText()

            attrs = line.attrs
            if attrs['id'] in skip_line:
                continue

            if attrs.get('pattern') is None:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            elif '/' in attrs['pattern']:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            else:
                sp = attrs['pattern']

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue

            transition = [this_state, mappingKey, sp]
            if transition not in self.mealy_fst['transitionFunction']:
                self.mealy_fst['transitionFunction'].append(transition)

            output = [this_state, mappingKey, "R"+mappingKey]
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
        skip_line = []
        for line in lines:
            spams = line.findAll("spam")
            line_content = ""
            for spam in spams:
                line_content = line_content + spam.getText()

            attrs = line.attrs
            if attrs['id'] in skip_line:
                continue

            if attrs.get('pattern') is None:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            elif '/' in attrs['pattern']:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            else:
                sp = attrs['pattern']

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue

            transition = [this_state, mappingKey, sp]
            if transition not in self.moore_fst['transitionFunction']:
                self.moore_fst['transitionFunction'].append(transition)

            output = [sp, "R" + mappingKey]
            if output not in self.moore_fst['outputFunction']:
                self.moore_fst['outputFunction'].append(output)
            this_state = sp

        transition = [this_state, 'ε', 'GE']
        if transition not in self.moore_fst['transitionFunction']:
            self.moore_fst['transitionFunction'].append(transition)
        print(self.moore_fst['transitionFunction'])
        print(self.moore_fst['outputFunction'])
        print("update Moore FST")

    def getFileInSignals(self):
        inSignals = []
        soup = BeautifulSoup(self.source, "html.parser")
        lines = soup.findAll("p")
        for line in lines:
            spams = line.findAll("spam")
            line_content = ""
            for spam in spams:
                line_content = line_content + spam.getText()

            attrs = line.attrs
            if attrs.get('pattern') is None:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            elif '/' in attrs['pattern']:
                if "　" in line_content:
                    sp = self.get_key(line_content.split("　")[1])
                else:
                    sp = self.get_key(line_content)
            else:
                sp = attrs['pattern']

            if sp == '':
                continue

            mappingKey = self.getMappingValue(sp)
            lineId = self.getLineId(sp)
            if attrs['id'] not in lineId:
                continue
            inSignals.append(mappingKey)

        print(inSignals)
        return inSignals

    def getLineContentAttr(self, lines):
        line_info = []
        for line in lines:
            spams = line.findAll("spam")
            line_content = ""
            for spam in spams:
                line_content = line_content + spam.getText()

            attrs = line.attrs
            info = {
                'line_content': line_content,
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
        if '.' in attr:
            mainKey = attr.split('.')[0]
            subKey = attr.split('.')[1]
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
        return entity.updateSchema(self.schemaInfo.get('schema_id'), "", "", "", "", dtd, "", "", "", "")

    def resetSignal(self, inSignals, outSignals):
        original_inSignals = list()
        new_outSignals = list()
        new_inSignals = list()
        temp = ""
        for input in inSignals:
            if temp != input:
                original_inSignals.append(input)
                temp = input

        for input in original_inSignals:
            inSignal = self.getMappingKey(input)
            if isinstance(self.new_dtd[inSignal], str):
                new_inSignals.append(input)
            else:
                list_length = len(self.new_dtd[inSignal])
                for i in range(0, list_length):
                    new_inSignals.append(input)

        for new_input in new_inSignals:
            new_outSignals.append('R' + new_input)

        return new_inSignals, new_outSignals

    def updateRules(self, inSignals, outSignals):
        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))
        inSignals, outSignals = self.resetSignal(inSignals, outSignals)
        for idx, out in enumerate(outSignals):
            if out not in self.rules.keys():
                self.rules[out] = []
            inSignal = inSignals[idx]
            nextSignal = ""
            if idx != len(outSignals) - 1:
                nextSignal = inSignals[idx + 1]
            inSignal = self.getMappingKey(inSignal)
            in_value = self.new_dtd[inSignal]
            pos_file = self.fileInfo['position']
            if '.' in inSignal:
                main = inSignal.split('.')[0]
                sub = inSignal.split('.')[1]
                pos = pos_file[main][sub]
            else:
                pos = pos_file[inSignal]

            lineIds = []
            if isinstance(pos, list):
                for p in pos:
                    position = json.loads(p)
                    for lineId in position['lineId']:
                        lineIds.append(lineId)
            else:
                position = json.loads(pos)
                lineIds = position['lineId']

            for line in lineIds:
                line_id = int(line.split('-')[1])
                lineInfo = line_info[line_id]

                pattern = ""
                attr = lineInfo['attr']
                if attr.get('pattern') is not None:
                    pattern = attr.get('pattern')

                content = lineInfo['line_content']
                if isinstance(in_value, list):
                    for value in in_value:
                        startIdx = content.find(value)
                        leftStr = content[0:startIdx-1]
                        if (startIdx == -1) & (pattern == ""):
                            if nextSignal == "":
                                right_LM = "end"
                            else:
                                right_LM = "(\u4E00 | \u4E8C | \u4E09 | \u56DB | \u4E94 | \u516D | \u4E03 | \u516B | \u4E5D | \u5341) or \n and [" + nextSignal + "] attribute value"

                            rule_structure = {
                                'R': {
                                    'line_id': lineIds,
                                    'line_pattern': pattern,
                                    'left_LM': "[" + inSignal + "] attribute value and \n or (\u4E00 | \u4E8C | \u4E09 | \u56DB | \u4E94 | \u516D | \u4E03 | \u516B | \u4E5D | \u5341)",
                                    'right_LM': right_LM
                                },
                                'count': 0
                            }
                        else:
                            rule_structure = {
                                'R': {
                                    'line_id': lineIds,
                                    'line_pattern': pattern,
                                    'left_LM': "[" + inSignal + "] attribute value",
                                    'right_LM': "\n"
                                },
                                'count': 0
                            }

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

                            if leftStr not in sp_list:
                                self.schemaInfo = self.updateSchemaDtd(inSignal, leftStr)
                                print(self.schemaInfo)

                        if len(self.rules[out]) == 0:
                            self.rules[out].append(rule_structure)
                        # else:
                        #     rule_list = self.rules[out]
                        #     add_new = False
                        #     for rule in rule_list:
                        #         rule_lineId = rule.get('R').get('line_id')
                        #         rule_pattern = rule.get('R').get('line_pattern')
                        #         rule_left_LM = rule.get('R').get('left_LM')
                        #         rule_right_LM = rule.get('R').get('right_LM')
                        #         if
                        break
                else:
                    startIdx = content.find(in_value)
                    if (startIdx == 0) & (content == in_value):
                        rule_structure = {
                            'R': {
                                'line_id': lineIds,
                                'line_pattern': pattern,
                                'left_LM': "",
                                'right_LM': "\n"
                            },
                            'count': 0
                        }
                    elif (startIdx == -1) & (pattern == ""):
                        if nextSignal == "":
                            right_LM = "end"
                        else:
                            right_LM = "\n and [" + nextSignal + "] attribute value"
                        rule_structure = {
                            'R': {
                                'line_id': lineIds,
                                'line_pattern': pattern,
                                'left_LM': "[" + inSignal + "] attribute value and \n ",
                                'right_LM': right_LM
                            },
                            'count': 0
                        }
                    elif (startIdx == -1) & (content.replace('\u3000', '') == in_value):
                        rule_structure = {
                            'R': {
                                'line_id': lineIds,
                                'line_pattern': pattern,
                                'left_LM': "",
                                'right_LM': "\n"
                            },
                            'count': 0
                        }
                    else:
                        leftStr = content[0:startIdx - 1]
                        if nextSignal == "":
                            right_LM = "end"
                        else:
                            right_LM = "[" + nextSignal + "] attribute value"
                        rule_structure = {
                            'R': {
                                'line_id': lineIds,
                                'line_pattern': pattern,
                                'left_LM': "[" + inSignal + "] attribute value and \n",
                                'right_LM': right_LM
                            },
                            'count': 0
                        }

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

                        if leftStr not in sp_list:
                            self.schemaInfo = self.updateSchemaDtd(inSignal, leftStr)
                            print(self.schemaInfo)

                    if len(self.rules[out]) == 0:
                        self.rules[out].append(rule_structure)
                    break
        print(self.rules)

    def learning(self):
        self.updateMealyFst()
        fstMealy = fst(initState=self.mealy_fst['initState'],
                       states=self.mealy_fst['states'],
                       transitionFunction=self.mealy_fst['transitionFunction'],
                       outputFunction=self.mealy_fst['outputFunction'],
                       finalStates=self.mealy_fst['finalStates'])
        # graph = graphviz.Source(fstUtils.toDot(fstMealy))
        # graph.view('fst_graph_mealy', cleanup=True)

        self.updateMooreFst()
        fstMoore = fst(initState=self.moore_fst['initState'],
                       states=self.moore_fst['states'],
                       transitionFunction=self.moore_fst['transitionFunction'],
                       outputFunction=self.moore_fst['outputFunction'],
                       finalStates=self.moore_fst['finalStates'])
        # graph = graphviz.Source(fstUtils.toDot(fstMoore))
        # graph.view('fst_graph_moore', cleanup=True)

        print("updated FST")

        inSignals = self.getFileInSignals()
        outSignals, outStates = fstMoore.playFST(inSignals)
        self.updateRules(inSignals, outSignals)

        print("Rule Extraction")
        return self.mealy_fst, self.moore_fst, self.rules

    def extraction(self):
        soup = BeautifulSoup(self.source, "html.parser")
        line_info = self.getLineContentAttr(soup.findAll("p"))

        print("Test")


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
