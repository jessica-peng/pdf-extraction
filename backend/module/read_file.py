import glob
import json
import os
import re
import shutil
import fitz
import numpy as np


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def save_dict_file(pdf, filename):
    data = []
    counter = 1
    for page in pdf:
        content = page.get_text("dict")
        data.append(content)
        counter += 1

    with open(filename, mode='wt', encoding='utf-8') as fj:
        fj.write(json.dumps(data, cls=MyEncoder, indent=4, ensure_ascii=False))
        fj.close()


def save_txt_file(pdf, filename):
    txt_file = open(filename, mode='wt', encoding='utf-8')
    for page in pdf:
        text = page.get_text("text")
        txt_file.write(text)


class Read_File:
    def __init__(self, path):
        self.path = path

    def read_pdf_file_dict(self):
        print(os.getcwd())

        dict_dir = self.path + '/pdf2dict/'

        if os.path.exists(dict_dir):
            shutil.rmtree(dict_dir)
        os.makedirs(dict_dir)

        searchPath = self.path + '/*.pdf'
        for pdfFile in glob.glob(searchPath):
            filename = os.path.basename(pdfFile)
            filename = filename.split(".pdf")[0]
            dict_file = dict_dir + filename + '.json'

            if os.path.exists(pdfFile):
                print(pdfFile)

                with fitz.open(pdfFile) as pdf:
                    save_dict_file(pdf, dict_file)
            else:
                print('File is not exist!')

    def read_pdf_file_text(self, filename):
        print(os.getcwd())

        text_dir = self.path + '/pdf2text/'

        if not os.path.exists(text_dir):
            os.makedirs(text_dir)

        pdfFile = self.path + '/' + filename
        filename = filename.split(".pdf")[0]
        text_file = text_dir + filename + '.txt'

        if os.path.exists(pdfFile):
            print(pdfFile)

            with fitz.open(pdfFile) as pdf:
                save_txt_file(pdf, text_file)
        else:
            print('File is not exist!')

    def read_text_file(self, filename):
        filename = filename.split(".pdf")[0]
        text_file = self.path + '/pdf2text/' + filename + '.txt'
        f = open(text_file, 'r', encoding='utf-8')
        text = ''
        for line in f.readlines():
            text_line = re.sub(r'^(\s\s|)[0-9][0-9]+\n', '', line)
            text_line = re.sub(r'^[１-９]', '', text_line)
            text_line = re.sub(r'^[0-9]$', '', text_line)
            text_line = re.sub(r' ', '', text_line)
            text_line = re.sub(r'^　', '', text_line)
            text_line = re.sub(r'^\n', '', text_line)
            text = text + text_line

        line_list = text.split('\n')
        text = ''
        for line in line_list:
            if '\u3000' in line:
                word_list = line.split('\u3000')
                for word in word_list:
                    if len(word) <= 1:
                        text = text + word
                    else:
                        text = text + '\u3000' + word
                text = text + '\n'
            elif '\xa0' in line:
                word_list = line.split('\xa0')
                for word in word_list:
                    if len(word) <= 1:
                        text = text + word
                    else:
                        text = text + '\u3000' + word
                text = text + '\n'
            else:
                text = text + line + '\n'

        line_list = text.split('\n')
        text = ''
        for line in line_list:
            if line == '':
                continue
            text_line = re.sub(r'^　', '', line)
            text = text + text_line + '\n'

        text = text[:-1]
        print(text)
        f.close()
        return text
