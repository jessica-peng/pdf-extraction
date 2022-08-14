import glob
import json
import os
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


class Read_File:
    def __init__(self, path):
        self.path = path

    def read_pdf_file(self):
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