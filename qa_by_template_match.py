import re
from py2neo import Graph
from config import config
from src.loader import load_graph_info
from src.model import Model

class GraphQA:
    def __init__(self, config):
        self.graph = Graph("http://localhost:7474", auth=("neo4j", "123456"))
        self.entities_set, self.relations_set, self.question_templet = load_graph_info(config)
        self.model = Model()
        print('''
        桃园三结义人物关系知识图谱加载完毕！
        可以查询桃园三结义的相关人物关系~
        ''')

    '''回答问题'''

    def query(self, question):
        global graph_search_result, answer
        info = self.extract_sentence(question)  # 提取图谱中有的信息
        possible_templates = self.get_possible_templates(info)  # 获取可能的模板
        sort_templates = self.get_sort_templates(question, possible_templates)  # 句子相似度计算,由高到低排序可能的模板
        # 根据模板进行cypher查询并回答
        for cypher, answer, info, score in sort_templates:
            cypher = self.fill_info(cypher, info)
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
        entities = self.model.get_entities(self.entities_set, sentence)
        relations = self.model.get_relations(self.relations_set, sentence)
        return {"%ENT%": entities,
                "%REL%": relations}

    def get_possible_templates(self, info):
        """
        获取可能的模板，将check换成对应的info
        :param info:
        :return:
        """
        possible_templates = []
        for temp, cypher, answer, check in self.question_templet:  # 获取可能的模板信息
            for key, count in check.items():
                if len(info.get(key, [])) != count:  # 如果提取到的实体不能满足check中的实体数量就不可能匹配这个模板
                    break
            possible_templates.append([temp, cypher, answer, info])  # 添加模板信息
        return possible_templates

    def get_sort_templates(self, sentence, templates):
        """
        还原模板问题，并根据句子相似度算法进行排序
        :param sentence:
        :param templates:
        :return:
        """
        sort_templates = []
        for temp, cypher, answer, info in templates:
            template_query = self.fill_info(temp, info)
            score = self.model.sentence_similarity(sentence, template_query)
            sort_templates.append([cypher, answer, info, score])  # 不需要原问题模板了
        sort_templates = sorted(sort_templates, reverse=True, key=lambda x: x[3])
        return sort_templates

    def fill_info(self, template, info):
        '''
        替换所有对应的info内容
        :param template:
        :param info:
        :return:
        '''
        for key, values in info.items():
            # print(key, values)
            for i, value in enumerate(values):
                key = key[:4] + ('%d' % i) + '%'
                template = template.replace(key, value)
        return template



    def create_answer(self, graph_search_result, answer, info):
        if answer == 'REL':
            if not graph_search_result:
                return '对不起，没有合适的答案'
            result = list(graph_search_result[0][answer].types())[0]  # 获取关系
            info['%REL%'].append(result)
            answer_template = '%ENT0%的%REL0%是%ENT1%'
            result = self.fill_info(answer_template, info)
        return result


if __name__ == '__main__':
    QA = GraphQA(config)
    # while True:
    #     question = input('请输入您想问的问题：')
    #     answer = QA.query(question)
    #     print(answer)
    # 测试用例
    answer = QA.query('刘备和张飞是什么关系')
    print(answer)
    answer = QA.query('张飞和刘备是什么关系')
    print(answer)
