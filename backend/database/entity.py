import pymongo
from bson import ObjectId


class Entity:

    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.database = self.client["widmpdf"]

    def getDatabase(self):
        return self.database

    def getUserInfoByUserId(self, userId):
        user_collection = self.database.get_collection("user")
        userInfo = user_collection.find_one({"_id": ObjectId(userId)})
        return userInfo

    def getSchemaInfoBySchemaId(self, schemaId):
        schema_collection = self.database.get_collection("schema")
        schemaInfo = schema_collection.find_one({"schema_id": schemaId}, {"_id": 0})
        return schemaInfo

    def updateUserInfoForSchema(self, userId, schemaId, schemaName):
        user_collection = self.database.get_collection("user")
        userInfo = user_collection.find_one({"_id": ObjectId(userId)})
        schema = {
            "id": schemaId,
            "name": schemaName
        }
        schemaList = userInfo["schema"].copy()
        schemaList.append(schema)
        user_collection.update_one({"_id": ObjectId(userId)}, {"$set": {"schema": schemaList}})
        userInfo = user_collection.find_one({"_id": ObjectId(userId)})
        return userInfo

    def insertSchema(self, schema):
        schema_collection = self.database.get_collection("schema")
        _id = schema_collection.insert_one(schema).inserted_id
        schemaInfo = schema_collection.find_one({"_id": ObjectId(_id)}, {"_id": 0})
        return schemaInfo

    def updateSchema(self, schemaId, ignoreTokes, minSupport, patternList, attribute, dtd, pdfFile, mapping, mealyFst, mooreFst, rules):
        schema_collection = self.database.get_collection("schema")
        schemaInfo = schema_collection.find_one({"schema_id": schemaId}, {"_id": 0})
        if ignoreTokes == "":
            ignoreTokes = schemaInfo['ignore_token']
        if minSupport == "":
            minSupport = schemaInfo['minimum_support']
        if patternList == "":
            patternList = schemaInfo['pattern_list']
        if attribute == "":
            attributes = schemaInfo['attributes']
        else:
            attributes = schemaInfo['attributes']
            attributes.append(attribute)
        if dtd == "":
            dtd = schemaInfo['dtd']
        if mapping == "":
            mapping = schemaInfo['mapping']
        if mealyFst == "":
            mealyFst = schemaInfo['mealy_fst']
        if mooreFst == "":
            mooreFst = schemaInfo['moore_fst']
        if rules == "":
            rules = schemaInfo['rules']
        if pdfFile == "":
            file_list = schemaInfo['file_list']
        else:
            file_list = schemaInfo['file_list']
            file_list.append(pdfFile)

        schema_collection.update_one({"schema_id": schemaId}, {"$set": {"ignore_token": ignoreTokes,
                                                                        "minimum_support": float(minSupport),
                                                                        "pattern_list": patternList,
                                                                        "attributes": attributes,
                                                                        "dtd": dtd,
                                                                        "mapping": mapping,
                                                                        "mealy_fst": mealyFst,
                                                                        "moore_fst": mooreFst,
                                                                        "rules": rules,
                                                                        "file_list": file_list}})
        schemaInfo = schema_collection.find_one({"schema_id": schemaId}, {"_id": 0})
        return schemaInfo

    def insertFiles(self, files):
        files_collection = self.database.get_collection("files")
        _id = files_collection.insert_one(files).inserted_id
        filesInfo = files_collection.find_one({"_id": ObjectId(_id)}, {"_id": 0})
        return filesInfo

    def getFileInfoBySchemaIdAndFileId(self, schemaId, fileId):
        files_collection = self.database.get_collection("files")
        filesInfo = files_collection.find_one({"schema_id": schemaId, "file_id": fileId}, {"_id": 0})
        return filesInfo

    def updateStructureById(self, schemaId, fileId, structure, pc):
        files_collection = self.database.get_collection("files")
        files_collection.update_one({"schema_id": schemaId, "file_id": fileId}, {"$set": {"structure": structure,
                                                                                          "position": pc}})
        filesInfo = files_collection.find_one({"schema_id": schemaId, "file_id": fileId}, {"_id": 0})
        return filesInfo

    def test(self):
        db_list = self.client.list_database_names()
        if "widmpdf" in db_list:
            print("widmpdf 已存在！")

        collection = self.database["user"]
        collection_list = self.database.list_collection_names()
        x = ""
        if "user" in collection_list:  # testMongoCol 集合是否存在
            print("user！")
            x = collection.find_one()
        print(x)


if __name__ == '__main__':
    Entity().test()
