import re
import json
import pandas
import itertools
from py2neo import Graph
from config import config


class GraphQA:
    def __init__(self, config):
        self.graph = Graph("http://localhost:7474", auth=("neo4j", "123456"))
        self.kg_data_path = config['kg_data_path']
        self.template_path = config['template_path']
        self.load(self.kg_data_path, self.template_path)
        print('''
        桃园三结义人物关系知识图谱加载完毕！
        可以查询桃园三结义的相关人物关系~
        ''')

    # 加载模板
    def load(self, schema_path, templet_path):
        self.load_kg_data(schema_path)
        self.load_templet(templet_path)
        return

    # 加载图谱信息
    def load_kg_data(self, path):
        with open(path, encoding="utf8") as f:
            kg_data = json.load(f)
        self.relations_set = set(kg_data["relations"])
        self.entities_set = set(kg_data["entities"])
        return

    # 加载模板信息
    def load_templet(self, path):
        dataframe = pandas.read_excel(path)
        self.question_templet = []
        for index in range(len(dataframe)):
            question = dataframe["question"][index]
            cypher = dataframe["cypher"][index]
            cypher_check = dataframe["check"][index]
            answer = dataframe["answer"][index]
            self.question_templet.append([question, cypher, json.loads(cypher_check), answer])
        return

    # 回答问题
    def query(self, question):
        info = self.extract_sentence(question)  # 提取图谱中有的信息
        possible_templates = self.get_possible_templates(info)  # 获取可能的模板
        sort_templates = self.get_sort_templates(question, possible_templates)  # 句子相似度计算,由高到低排序可能的模板
        # 根据模板进行cypher查询并回答
        for temp, cypher, answer, info, score in sort_templates:
            cypher = self.fill_info(info, cypher)
            graph_search_result = self.graph.run(cypher).data()
            # print(graph_search_result)
            # print(type(graph_search_result))
            # 最高分命中的模板不一定在图上能找到答案, 当不能找到答案时，运行下一个搜索语句, 找到答案时停止查找后面的模板
            if graph_search_result:
                break
        answer = self.create_answer(graph_search_result, answer, info)
        # 对问题进行预处理，提取需要的信息
        return answer

    def extract_sentence(self, sentence):
        entities = re.findall("|".join(self.entities_set), sentence)  # 获得问题中提到的实体，两种方法都行
        relations = re.findall("|".join(self.relations_set), sentence)  # 但没有数据就用正则（规则：正则。模型：NER）
        return {"%ENT%": entities,
                "%REL%": relations}

    def get_possible_templates(self, info):
        possible_templates = []
        for temp, cypher, check, answer in self.question_templet:
            for key, count in check.items():
                if len(info.get(key, [])) < count:
                    break
            possible_templates.append([temp, cypher, answer, info])
        return possible_templates

    def get_sort_templates(self, sentence, templates):
        sort_templates = []
        for temp, cypher, answer, info in templates:
            template_query = self.fill_info(info, temp)
            score = self.sentence_similarity(sentence, template_query)
            sort_templates.append([temp, cypher, answer, info, score])
        sort_templates = sorted(sort_templates, reverse=True, key=lambda x: x[4])
        return sort_templates

    def fill_info(self, info, template):
        for key, values in info.items():
            for i, value in enumerate(values):
                key = '%ENT' + ('%d' % i) + '%'
                template = template.replace(key, value)
        return template

    def sentence_similarity(self, string1, string2):
        jaccard_distance = len(set(string1) & set(string2)) / len(set(string1) | set(string2))
        return jaccard_distance

    def create_answer(self, graph_search_result, answer, info):
        if not graph_search_result:
            return '对不起，没有合适的答案'
        result = list(graph_search_result[0][answer].types())[0]
        return result

if __name__ == '__main__':
    QA = GraphQA(config)
    while True:
        question = input('请输入您想问的问题：')
        answer = QA.query(question)
        print(answer)
    # 测试用例
    # answer = QA.query('刘备和张飞是什么关系')
    # print(answer)
    # answer = QA.query('张飞和刘备是什么关系')
    # print(answer)
