import json
import os
import uuid

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from backend.database.collection import Schema, Files
from backend.database.entity import Entity
from backend.module.fst import FST
from backend.module.prefixSpan import PrefixSpan
from backend.module.read_file import Read_File

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

entity = Entity()

# @app.route('/')
# def root():
#     return render_template('index.html')


@app.route("/")
def hello():
    return jsonify({'text': 'Hello World!'})


@app.route('/schemaList', methods=['GET'])
def get_schemaList():
    # fetching from the database
    userId = request.args['userId']
    userInfo = entity.getUserInfoByUserId(userId)
    schemaList = []
    for schema in userInfo['schema']:
        schemaList.append(schema)

    print(schemaList)
    return jsonify(schemaList)


@app.route('/schema', methods=['GET'])
def get_schema():
    schemaId = request.args['schemaId']

    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    if schemaInfo is None:
        result = "No Schema Information!"
    else:
        result = schemaInfo
    return jsonify(result)


@app.route('/addSchema', methods=['POST'])
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


@app.route('/updateSchema', methods=['POST'])
def update_schema():
    schemaId = request.form.get('schemaId')
    ignoreTokes = request.form.get('ignoreTokens')
    minSupport = request.form.get('minSupport')

    schemaInfo = entity.updateSchema(schemaId, json.loads(ignoreTokes), minSupport, "", "", "", "", "", "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


# 判斷副檔名是否允許上傳
def is_allow_extensions(filename):
    return ('.' in filename) and (filename.split('.')[-1].lower() == 'pdf')


@app.route('/uploadFiles', methods=['POST'])
def upload_files():
    folder = request.headers.get('upload_type')
    path = request.headers.get('files_path') + folder
    if not os.path.exists(path):
        os.makedirs(path)

    fileList = request.files
    for filename in fileList:
        f = fileList.get(filename)
        if is_allow_extensions(filename):
            f.save(os.path.join(path, filename))
    return jsonify('success')


@app.route('/schemaMining', methods=['POST'])
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


@app.route('/updatePatternOfSchema', methods=['POST'])
def update_pattern_of_schema():
    schemaId = request.form.get('schemaId')
    patternList = request.form.get('patternList')
    patternList = patternList.split(',')
    schemaInfo = entity.updateSchema(schemaId, "", "", patternList, "", "", "", "", "", "", "")
    print(schemaInfo)

    return jsonify(schemaInfo)


@app.route('/patterns', methods=['GET'])
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


@app.route('/getAttributes', methods=['GET'])
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


@app.route('/getDtd', methods=['GET'])
def get_dtd():
    schemaId = request.args['schemaId']
    # fetching from the database
    schemaInfo = entity.getSchemaInfoBySchemaId(schemaId)
    result = schemaInfo['dtd']
    return jsonify(result)


@app.route('/updateAttributeOfSchema', methods=['POST'])
def update_attribute_of_schema():
    schemaId = request.form.get('schemaId')
    attribute = request.form.get('attribute')
    schemaInfo = entity.updateSchema(schemaId, "", "", "", attribute, "", "", "", "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


@app.route('/updateDtdOfSchema', methods=['POST'])
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
    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", dtd, "", mapping, "", "", "")
    print(schemaInfo)
    return jsonify(schemaInfo)


@app.route('/updateFileListOfSchema', methods=['POST'])
def update_fileList_of_schema():
    schemaId = request.form.get('schemaId')
    filename = request.form.get('filename')

    fileInfo = {
        "id": uuid.uuid4().hex,
        "name": filename
    }

    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", "", fileInfo, "", "", "", "")
    path = schemaInfo['files_path'] + 'test'
    read_file = Read_File(path)
    read_file.read_pdf_file_text(filename)
    print('success')
    return jsonify(schemaInfo)


@app.route('/readTextFileOfPDF', methods=['GET'])
def read_text_file_of_PDF():
    path = request.args['files_path']
    filename = request.args['filename']
    read_file = Read_File(path)
    result = read_file.read_text_file(filename)
    return jsonify(result)


@app.route('/addFileInfo', methods=['POST'])
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
    files['structure'] = structure
    files['position'] = structure
    filesInfo = entity.insertFiles(files)
    print(filesInfo)
    return jsonify(filesInfo)


@app.route('/getFileInfo', methods=['GET'])
def get_file_info():
    schema_id = request.args['schema_id']
    file_id = request.args['file_id']
    result = entity.getFileInfoBySchemaIdAndFileId(schema_id, file_id)
    return jsonify(result)


@app.route('/updateStructureById', methods=['POST'])
def update_structure_by_id():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    pc = request.form.get('pc')
    structure = json.loads(dtd)
    positionColor = json.loads(pc)
    result = entity.updateStructureById(schemaId, fileId, structure, positionColor)
    return jsonify(result)


@app.route('/learningRule', methods=['POST'])
def learning_rule():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    mapping = request.form.get('mapping')
    content = request.form.get('content')
    structure = json.loads(dtd)
    mapping = json.loads(mapping)
    fst = FST(schemaId, fileId, structure, content, mapping)
    mealyFst, mooreFst, rules = fst.learning()
    schemaInfo = entity.updateSchema(schemaId, "", "", "", "", "", "", "", mealyFst, mooreFst, rules)
    return jsonify(schemaInfo)


@app.route('/fileExtraction', methods=['POST'])
def file_extraction():
    schemaId = request.form.get('schemaId')
    fileId = request.form.get('fileId')
    dtd = request.form.get('dtd')
    mapping = request.form.get('mapping')
    content = request.form.get('content')
    structure = json.loads(dtd)
    mapping = json.loads(mapping)
    fst = FST(schemaId, fileId, structure, content, mapping)
    mealyFst, mooreFst, rules = fst.extraction()
    result = entity.updateSchema(schemaId, "", "", "", "", "", "", "", mealyFst, mooreFst, rules)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
