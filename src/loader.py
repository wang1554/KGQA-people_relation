import json

import pandas


class Loader:
    def __init__(self, config):
        self.entities_set = set()
        self.relations_set = set()
        self.question_templet = []
        self.load(config['kg_data_path'], config['template_path'])

    def load(self, kg_data_path, template_path):
        self.load_kg_data(kg_data_path)
        self.load_templet(template_path)
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
        for index in range(len(dataframe)):
            question = dataframe["question"][index]
            cypher = dataframe["cypher"][index]
            answer = dataframe["answer"][index]
            check = dataframe["check"][index]
            self.question_templet.append([question, cypher, answer, json.loads(check)])
        return


def load_graph_info(config):
    lr = Loader(config)
    return lr.entities_set, lr.relations_set, lr.question_templet


if __name__ == '__main__':
    import sys

    sys.path.append("..")
    from config import config

    config['kg_data_path'] = '../output/kg_data.json'
    config['template_path'] = '../output/template.xlsx'

    entities_set, relations_set, question_templet = load_graph_info(config)
