import re
from py2neo import Graph
from config import config
from src.loader import load_graph_info
from src.model import Model
from src.answer import Answer


class GraphQA:
    def __init__(self, config):
        self.graph = Graph("http://localhost:7474", auth=("neo4j", "123456"))
        self.entities_set, self.relations_set, self.question_templet = load_graph_info(config)
        self.model = Model()
        self.answer = Answer()
        print('''
        桃园三结义人物关系知识图谱加载完毕！
        可以查询桃园三结义的相关人物关系~
        ''')

    '''回答问题'''

    def query(self, question):
        self.info = self.extract_sentence(question)  # 提取图谱中有的信息
        self.sort_templates = self.get_sort_possible_templates(self.question_templet, self.info, question)
        # 用于检查对应问题匹配到的模板
        # print('匹配的模板有:', [template for template, _, _, _, _ in self.sort_templates])
        # 根据模板进行cypher查询并回答
        for _, cypher, answer, info, score in self.sort_templates:
            result, self.obj_cypher = self.answer.create_answer(self.graph, cypher, answer, info)
            # 最高分命中的模板不一定在图上能找到答案, 当不能找到答案时，运行下一个搜索语句, 找到答案时停止查找后面的模板
            if result:
                return '回答:' + result
        return '回答:对不起，没有合适的答案'

    def extract_sentence(self, sentence):
        entities = self.model.get_entities(self.entities_set, sentence)
        relations = self.model.get_relations(self.relations_set, sentence)
        return {"%ENT%": entities,
                "%REL%": relations}

    def get_sort_possible_templates(self, question_templet, info, question):
        """
        获取可能的模板，然后根据相似度匹配排序返回降序的模板
        """
        possible_templates = self.get_possible_templates(question_templet, info, question)
        sort_templates = sorted(possible_templates, reverse=True, key=lambda x: x[4])
        return sort_templates

    def get_possible_templates(self, question_templet, info, question):
        possible_templates = []
        for temp, cypher, answer, check in question_templet:  # 获取可能的模板信息
            if self.check_info(check, info):  # 如果满足check的条件就添加到候选模板中
                template_query = self.answer.fill_info(temp, info)  # 填充成模板问句
                score = self.model.sentence_similarity(question, template_query)
                possible_templates.append([template_query, cypher, answer, info, score])  # 添加模板信息
        return possible_templates

    def check_info(self, check, info):
        for key, count in check.items():
            if len(info.get(key, [])) != count:  # 如果提取到的实体不能满足check中的实体数量就不可能匹配这个模板
                return False
        return True


if __name__ == '__main__':

    QA = GraphQA(config)

    '''测试用例'''
    print('-------------------------------')
    # 问题1的双向关系和无关系
    queries = ['刘备和张飞什么关系',
               '张飞和刘备什么关系',
               '刘备和关羽什么关系',
               '刘备和张辽什么关系',
               '特朗普和拜登什么关系']
    for query in queries:
        print('测试用例')
        print('问题:%s:' % query)
        print(QA.query(query))
        print('-------------------------------')

    # 问题2的有和无
    queries = ['刘备的三弟是谁',
               '谁是黄忠的主公',
               '特朗普的儿子是谁']
    for query in queries:
        print('测试用例')
        print('问题:%s:' % query)
        print(QA.query(query))
        print('-------------------------------')

    '''真实问答'''
    while True:
        question = input('请输入您想问的问题：')
        answer = QA.query(question)
        print(answer)
        print('-------------------------------')

