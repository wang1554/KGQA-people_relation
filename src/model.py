import re


class Model:
    def __init__(self):
        pass

    # 获得问题中提到的实体，两种方法都行
    # 但没有数据就用正则（规则：正则。模型：NER）
    def get_entities(self, entities_set, sentence):
        entities = re.findall("|".join(entities_set), sentence)
        return entities

    def get_relations(self, relations_set, sentence):
        relations = re.findall("|".join(relations_set), sentence)
        return relations

    # 获取匹配分值，也是规则和模型两种
    # 没有数据就用jaccard距离直接算，也可以用编辑距离、词袋后的余弦相似度等简单算法
    def sentence_similarity(self, string1, string2):
        jaccard_distance = len(set(string1) & set(string2)) / len(set(string1) | set(string2))
        return jaccard_distance


if __name__ == '__main__':
    mo = Model()

    entities = mo.get_entities(('今天', '天气', '不错'), '今天天气不错啊~')
    print(entities)

    score_high = mo.sentence_similarity('今天吃北京烤鸭', '明天吃宫保鸡丁')
    score_low = mo.sentence_similarity('今天吃北京烤鸭', '压根不一样的句子')
    print(score_high, score_low)

