import json
import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS

from database.collection import Schema, Files
from database.entity import Entity
from module.fst import FST
from module.langchain_pdf_json import LCOP
from module.prefixSpan import PrefixSpan
from module.read_file import Read_File

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# app.config['CORS_HEADERS'] = 'Content-Type'

entity = Entity()

# @app.route('/')
# def root():
#     return render_template('index.html')


@app.route("/api", methods=['GET'])
def hello():
    return jsonify({'text': 'Hello World!'})
    # return entity.getDatabase()


@app.route('/api/schemaList', methods=['GET'])
def get_schemaList():
    # fetching from the database
    userId = request.args['userId']
    userInfo = entity.getUserInfoByUserId(userId)
    schemaList = []
    for schema in userInfo['schema']:
        schemaList.append(schema)

    print(schemaList)
    return jsonify(schemaList)


@app.route('/api/schema', methods=['GET'])
def get_schema():
    schemaId = request.args['schemaId']

    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    if schemaInfo is None:
        result = "No Schema Information!"
    else:
        result = schemaInfo
    return jsonify(result)


@app.route('/api/addSchema', methods=['POST'])
def add_schema():
    schema = Schema().getCollectionFormat()
    userId = request.form.get('userId')
    schemaName = request.form.get('schemaName')
    minSupport = request.form.get('minSupport')
    ignoreTokes = request.form.get('ignoreTokens')

    schema_uuid = uuid.uuid4().hex
    schema['schema_id'] = schema_uuid
    schema['schema_name'] = schemaName
    schema['minimum_support'] = float(minSupport)
    schema['ignore_token'] = json.loads(ignoreTokes)

    userInfo = entity.updateUserInfoForSchema(userId, schema_uuid, schemaName)
    schema['files_path'] = userInfo['folder'] + schema_uuid + '/'
    schemaInfo = entity.insertSchema(schema)
    print(schemaInfo)
    return jsonify(schemaInfo)


@app.route('/api/updateSchema', methods=['POST'])
def update_schema():
    schemaId = request.form.get('schemaId')
    ignoreTokes = request.form.get('ignoreTokens')
    minSupport = request.form.get('minSupport')

    schemaInfo = entity.updateSchema(schemaId, json.loads(ignoreTokes), minSupport, "", "", "", "", "", "", "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


# 判斷副檔名是否允許上傳
def is_allow_extensions(filename):
    return ('.' in filename) and (filename.split('.')[-1].lower() == 'pdf')


@app.route('/api/uploadFiles/<schemaId>/<folder>', methods=['POST'])
def upload_files(schemaId, folder):
    path = 'data/demo/' + schemaId + '/' + folder
    if not os.path.exists(path):
        os.makedirs(path)

    fileList = request.files
    for filename in fileList:
        f = fileList.get(filename)
        if is_allow_extensions(filename):
            f.save(os.path.join(path, filename))
    return jsonify('success')


@app.route('/api/schemaMining', methods=['POST'])
def schema_mining():
    path = request.form.get('files_path') + 'pattern'
    schemaId = request.form.get('schemaId')
    ignoreTokes = request.form.get('ignoreTokens')
    minSupport = request.form.get('minSupport')
    patternMin = request.form.get('patternMin')
    patternMax = request.form.get('patternMax')

    read_file = Read_File(path)
    mining = PrefixSpan(path, ignoreTokes, minSupport, patternMin, patternMax)
    read_file.read_pdf_file_dict()
    pattern_list = mining.executePrefixSpan()

    selectPattern = []
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    if schemaInfo is not None:
        selectPattern = schemaInfo['pattern_list']
        for pattern in selectPattern:
            if pattern in pattern_list:
                pattern_list.remove(pattern)

    result = {
        'selected': selectPattern,
        'pattern': pattern_list
    }

    return jsonify(result)


@app.route('/api/updatePatternOfSchema', methods=['POST'])
def update_pattern_of_schema():
    schemaId = request.form.get('schemaId')
    patternList = request.form.get('patternList')
    patternList = patternList.split(',')
    schemaInfo = entity.updateSchema(schemaId, "", "", patternList, "", "", "", "", "", "", "", "")
    print(schemaInfo)

    return jsonify(schemaInfo)


@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    schemaId = request.args['schemaId']

    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    if schemaInfo is None:
        result = []
    else:
        patternList = []
        for pattern in schemaInfo['pattern_list']:
            patternList.append(pattern)
        result = patternList
    return jsonify(result)


@app.route('/api/getAttributes', methods=['GET'])
def get_attributes():
    schemaId = request.args['schemaId']
    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    if schemaInfo is None:
        result = []
    else:
        attributeList = []
        for attribute in schemaInfo['attributes']:
            attributeList.append(attribute)
        result = attributeList
    return jsonify(result)


@app.route('/api/getDtd', methods=['GET'])
def get_dtd():
    schemaId = request.args['schemaId']
    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    result = schemaInfo['dtd']
    return jsonify(result)


@app.route('/api/updateAttributeOfSchema', methods=['POST'])
def update_attribute_of_schema():
    schemaId = request.form.get('schemaId')
    attribute = request.form.get('attribute')
    schemaInfo = entity.updateSchema(schemaId, "", "", "", attribute, "", "", "", "", "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


@app.route('/api/updateDtdOfSchema', methods=['POST'])
def update_dtd_of_schema():
    schemaId = request.form.get('schemaId')
    dtd = request.form.get('dtd')
    structure = json.loads(dtd)
    mapping = {}

    mainKey = structure.keys()
    for key1 in mainKey:
        if isinstance(structure[key1], dict):
            subKey = structure[key1].keys()
            for key2 in subKey:
                if "_" in key2:
                    K2 = key2.upper().split("_")[0][0] + key2.upper().split("_")[1][0]
                else:
                    K2 = key2
                mapping.update({key1 + "." + key2: key1 + "_" + K2})
        else:
            mapping.update({key1: key1})

    # entity.updateNewStructureToFile(schemaId)
    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", dtd, "", mapping, "", "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


@app.route('/api/updateFileListOfSchema', methods=['POST'])
def update_fileList_of_schema():
    schemaId = request.form.get('schemaId')
    filename = request.form.get('filename')

    fileInfo = {
        "id": uuid.uuid4().hex,
        "name": filename
    }

    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", "", fileInfo, "", "", "", "", "")
    path = schemaInfo['files_path'] + 'test'
    filetype = request.args['filetype']
    read_file = Read_File(path, filetype)
    read_file.read_pdf_file_text(filename)
    print('success')
    return jsonify(schemaInfo)


@app.route('/api/readTextFileOfPDF', methods=['GET'])
def read_text_file_of_PDF():
    path = request.args['files_path']
    filename = request.args['filename']
    filetype = request.args['filetype']
    read_file = Read_File(path, filetype)
    result = read_file.read_text_file(filename)
    return jsonify(result)


@app.route('/api/addFileInfo', methods=['POST'])
def add_file_info():
    files = Files().getCollectionFormat()
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    structure = json.loads(dtd)

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

    files['schema_id'] = schemaId
    files['file_id'] = fileId
    files['instance'] = structure
    files['position'] = structure
    filesInfo = entity.insertFiles(files)
    print(filesInfo)
    return jsonify(filesInfo)


@app.route('/api/getFileInfo', methods=['GET'])
def get_file_info():
    schema_id = request.args['schema_id']
    file_id = request.args['file_id']
    result = entity.getFileInfoBySchemaIdAndFileId(schema_id, file_id)
    print("file ID = " + file_id)
    return jsonify(result)


@app.route('/api/updateStructureById', methods=['POST'])
def update_structure_by_id():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    pc = request.form.get('pc')
    structure = json.loads(dtd)
    positionColor = json.loads(pc)
    result = entity.updateStructureById(schemaId, fileId, structure, positionColor)
    print("file ID = " + fileId)
    return jsonify(result)


@app.route('/api/learningRule', methods=['POST'])
def learning_rule():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    mapping = request.form.get('mapping')
    content = request.form.get('content')
    structure = json.loads(dtd)
    mapping = json.loads(mapping)
    filetype = request.form.get('filetype')
    if filetype == '表單':
        filetype = 'form'
    elif filetype == '表格':
        filetype = 'table'
    elif filetype == '財務報表':
        filetype = 'FS'
    else:
        filetype = ''
    fst = FST(schemaId, fileId, structure, content, mapping, filetype)
    mealyFst, mooreFst, softmealyFst, rules = fst.learning()
    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", "", "", "", mealyFst, mooreFst, softmealyFst, rules)
    return jsonify(schemaInfo)


@app.route('/api/fileExtraction', methods=['POST'])
def file_extraction():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    mapping = request.form.get('mapping')
    attrList = request.form.get('attrList')
    content = request.form.get('content')
    structure = json.loads(dtd)
    mapping = json.loads(mapping)
    attrList = json.loads(attrList)
    filetype = request.form.get('filetype')
    if filetype == '表單':
        filetype = 'form'
    elif filetype == '表格':
        filetype = 'table'
    elif filetype == '財務報表':
        filetype = 'FS'
    else:
        filetype = ''
    fst = FST(schemaId, fileId, structure, content, mapping, filetype)
    file_structure, file_position = fst.extraction(attrList)
    result = entity.updateStructureById(schemaId, fileId, file_structure, file_position)
    print("file ID = " + fileId)
    return jsonify(result)


@app.route('/api/fileExtractionByLangChain', methods=['POST'])
def file_extraction_by_langchain():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    attrList = request.form.get('attrList')
    content = request.form.get('content')
    method = request.form.get('method')
    structure = json.loads(dtd)
    attrList = json.loads(attrList)
    file_structure = {}
    file_position = {}
    if method == 'LCOP':
        lcop = LCOP(schemaId, structure, content)
        file_structure, file_position = lcop.extraction(attrList)
    result = entity.updateStructureById(schemaId, fileId, file_structure, file_position)
    print("file ID = " + fileId)
    return jsonify(result)


@app.route('/api/updatePatternsByLangchain', methods=['POST'])
def update_patterns_by_langchain():
    schemaId = request.form.get('schemaId')
    dtd = request.form.get('dtd')
    content = request.form.get('content')
    structure = json.loads(dtd)
    lcop = LCOP(schemaId, structure, content)
    result = lcop.get_new_dtd()
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
    CORS(app)
    # from gevent import pywsgi
    # server = pywsgi.WSGIServer(('0.0.0.0', 5002), app)
    # server.serve_forever()