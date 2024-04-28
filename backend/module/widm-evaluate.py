import evaluate
from evaluate import load
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report, \
    precision_recall_fscore_support

from backend.database.entity import Entity


def compareFormat(predictions, trues):
    new_prediction = dict()
    new_groundTruths = dict()

    mainKey = predictions.keys()
    for key1 in mainKey:
        if isinstance(predictions[key1], dict):
            subKey = predictions[key1].keys()
            for key2 in subKey:
                new_prediction[key1 + "." + key2] = predictions[key1][key2]
        else:
            new_prediction[key1] = predictions[key1]

    mainKey = trues.keys()
    for key1 in mainKey:
        if isinstance(trues[key1], dict):
            subKey = trues[key1].keys()
            for key2 in subKey:
                # if trues[key1][key2] == '':
                #     trues[key1][key2] = ' '
                new_groundTruths[key1 + "." + key2] = trues[key1][key2]
        else:
            # if trues[key1] == '':
            #     trues[key1] = ' '
            new_groundTruths[key1] = trues[key1]

    predictions = dict()
    groundTruth = new_groundTruths

    # gold & pred
    tp = 0
    for key, value in new_prediction.items():
        if isinstance(value, list):
            true_value = new_groundTruths[key]
            if (len(value) == 0) and len(value) == len(true_value):
                tp = tp + 1
                predictions[key] = list()
            elif (len(value) == 0) and len(value) != len(true_value):
                continue
            elif len(value) != len(true_value):
                predictions[key] = list()
                for idx, v in enumerate(value):
                    predictions[key].append(v)
            else:
                add = True
                predictions[key] = list()
                for idx, v in enumerate(value):
                    predictions[key].append(v)
                    if v != true_value[idx]:
                        add = False
                if add:
                    tp = tp + 1
        else:
            true_value = new_groundTruths[key]
            if value == true_value:
                predictions[key] = value
                tp = tp + 1
            elif value != '':
                predictions[key] = value

    # predictions = list()
    # groundTruth = list()
    # for key, value in new_prediction.items():
    #     if isinstance(value, list):
    #         true_value = new_groundTruths[key]
    #         attr_value = key + '#1'
    #         if len(value) != len(true_value):
    #             attr_value = key + '#0'
    #         else:
    #             for idx, v in enumerate(value):
    #                 if v != true_value[idx]:
    #                     attr_value = key + '#0'
    #                     break
    #
    #         predictions.append(attr_value)
    #         groundTruth.append(key + '#1')
    #     else:
    #         true_value = new_groundTruths[key]
    #         if value == true_value:
    #             attr_value = key + '#1'
    #         else:
    #             attr_value = key + '#0'
    #         predictions.append(attr_value)
    #         groundTruth.append(key + '#1')
    print('predictions = ' + str(predictions))
    print('groundTruth = ' + str(groundTruth))
    print('predictions length = ' + str(len(predictions)))
    print('groundTruth length = ' + str(len(groundTruth)))
    print('tp = ' + str(tp))
    return predictions, groundTruth, tp


class WIDM_EVALUATE:
    def __init__(self, predictions, groundTruths):
        self.predictions, self.groundTruths, self.tp = compareFormat(predictions, groundTruths)
        # self.predictions = predictions
        # self.groundTruths = groundTruths

    def getPrecision(self):
        if len(self.predictions) == 0:
            precision = 0.0
        else:
            precision = self.tp / len(self.predictions)
        # micro_precision_score = precision_score(self.groundTruths, self.predictions, average='micro')
        print("precision = " + str(precision))
        return precision

    def getRecall(self):
        if len(self.groundTruths) == 0:
            recall = 0.0
        else:
            recall = self.tp / len(self.groundTruths)
        # micro_recall_score = recall_score(self.groundTruths, self.predictions, average='micro')
        print("recall = " + str(recall))
        return recall

    def getF1Score(self, precision, recall):
        if (precision == 0) and (recall == 0):
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)
        # micro_recall_score = recall_score(self.groundTruths, self.predictions, average='micro')
        print("f1 = " + str(f1))
        return f1

    def getMicroF1(self):
        micro_f1_score = f1_score(self.groundTruths, self.predictions, average='micro')
        print("micro_f1=" + str(micro_f1_score))
        return micro_f1_score

    def getMacroF1(self):
        macro_f1_score = f1_score(self.groundTruths, self.predictions, average='macro')
        print("macro_f1=" + str(macro_f1_score))
        return macro_f1_score

    def getClassification_report(self):
        print(classification_report(self.groundTruths, self.predictions))


if __name__ == '__main__':
    schema_id = '9c0f7fc5ee544156ba895006e1197e6c'  # 填寫要正確的schema id
    groundTruths_id = '5c48fa41c267499aac064f81f4fe8d25'  # 填寫正確的檔案結構的 file id
    groundTruths = Entity().getFileInfoBySchemaIdAndFileId(schema_id, groundTruths_id)

    schema_id = '9c0f7fc5ee544156ba895006e1197e6d'  # 填寫要擷取的schema id
    prediction_id = 'ed674ed204f2417f99cc02d426b9f221'  # 填寫程式擷取的檔案結構的 file id
    prediction = Entity().getFileInfoBySchemaIdAndFileId(schema_id, prediction_id)

    groundTruths = groundTruths.get('instance')
    prediction = prediction.get('instance')
    # prediction = {}

    evaluate = WIDM_EVALUATE(prediction, groundTruths)
    precision = evaluate.getPrecision()
    recall = evaluate.getRecall()
    f1 = evaluate.getF1Score(precision, recall)
    # micro_f1 = evaluate.getMicroF1()
    # macro_f1 = evaluate.getMacroF1()
    # evaluate.getClassification_report()
