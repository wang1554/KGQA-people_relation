from copy import deepcopy


class Answer:
    def __init__(self):
        pass

    # 填充实体、关系、属性等槽位
    def fill_info(self, template, info):
        """
        替换所有对应的info内容
        """
        for key, values in info.items():
            for i, value in enumerate(values):
                key = key[:4] + ('%d' % i) + '%'
                template = template.replace(key, value)
        return template

    # 获取图谱结果
    def get_graph_result(self, graph, cypher, info):
        cypher_filled = self.fill_info(cypher, info)
        graph_result = graph.run(cypher_filled).data()
        # print(cypher_filled)
        return graph_result

    # 根据图谱结果获取关系
    def rel_from_result(self, graph_result, answer, answer_template, info):
        rel = list(graph_result[0][answer].types())[0]  # 获取关系
        info['%REL%'].append(rel)
        result = self.fill_info(answer_template, info)
        return result

    # 根据图谱结果获的名字
    def name_from_result(self, graph_result, answer, answer_template, info):
        name = graph_result[0][answer]['NAME']  # 获取名字
        info['%ENT%'].append(name)
        result = self.fill_info(answer_template, info)
        return result

    def answer1(self, graph, cypher, answer, info):
        # 方向1获取图谱结果:两个人的关系可能有两种方向，比如A是B的哥哥，B是A的弟弟
        graph_result = self.get_graph_result(graph, cypher, info)
        # 方向2获取图谱结果
        info_reverse = deepcopy(info)  # 浅拷贝是同一个字典会乱，必须用深拷贝
        info_reverse['%ENT%'] = info_reverse['%ENT%'][::-1]  # 转换关系
        graph_result_reverse = self.get_graph_result(graph, cypher, info_reverse)
        # 如果都没就返回兜底回答
        if not graph_result and not graph_result_reverse:
            return '', None
        # 生成答句
        answer_template, result1, result2 = '%ENT0%的%REL0%是%ENT1%', '', ''
        # 方向1生成答句
        if graph_result:
            result1 = self.rel_from_result(graph_result, answer, answer_template, info)
        # 方向2生成答句
        if graph_result_reverse:
            result2 = self.rel_from_result(graph_result_reverse, answer, answer_template, info_reverse)
        # 合并答句
        result = result1 + ' ' + result2
        return result, graph_result

    def answer2(self, graph, cypher, answer, info):
        # 获取图谱结果
        graph_result = self.get_graph_result(graph, cypher, info)
        # 如果都没就返回兜底回答
        if not graph_result:
            return '', None
        # 生成答句
        answer_template, result = '%ENT0%的%REL0%是%ENT1%', ''
        result = self.name_from_result(graph_result, answer, answer_template, info)
        return result, graph_result

    # nlg，生成回答问题的语句
    def create_answer(self, graph, cypher, answer, info):
        result = ''
        obj_cypher = None
        if answer == 'REL':
            result, obj_cypher = self.answer1(graph, cypher, answer, info)
        elif answer == 'm':
            result, obj_cypher = self.answer2(graph, cypher, answer, info)
        return result.strip(), obj_cypher


if __name__ == '__main__':
    an = Answer()
    fill = an.fill_info('Match (n {NAME:"%ENT0%"})-[REL]->(m {NAME:"%ENT1%"}) return REL',
                        {'%ENT%': ['张飞', '刘备'], '%REL%': []})
    print(fill)
