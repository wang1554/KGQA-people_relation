import re
import json
import time
from py2neo import Graph
from collections import defaultdict


def clean_text(head, rel, tail):
    """
    有些特殊符号会影响cypher语句需要过滤掉
    """
    head = re.sub('·| |（.+）|\(.+\)', '', head)
    rel = re.sub('·| |《|》|、|（.+）|，|&', '', rel)
    tail = re.sub('·| |（.+）|\(.+\)', '', tail)
    return head, rel, tail


def read_triplet_data(path):
    rel_dic = defaultdict(dict)
    # 读取实体-关系-实体三元组文件
    with open(path, encoding="utf8") as lines:
        for line in lines:
            head, rel, tail = line.strip().split("\t")  # 取出三元组
            # head, rel, tail = clean_text(head, rel, tail)  # 这组数据比较干净不用过滤
            rel_dic[head][rel] = tail
    return rel_dic


class Builder:
    def __init__(self, config):
        self.cypher = ''
        self.num_cypher = 0
        self.data = defaultdict(set)
        self.rel_dic = defaultdict(dict)

        # 连接图谱&创建谱图
        self.graph = Graph(config['url'], auth=(config['user'], config['password']))
        self.build_graph()

    def build_graph(self):
        # 读取数据
        self.rel_dic = read_triplet_data(config['triplet_data_path'])
        # 生成cypher语句
        self.creat_cypher()

        # 运行cypher语句
        self.run_cypher()
        # 保存图谱信息用于后续问答内容
        self.save_kg_data()

    def creat_cypher(self):
        self.cypher = ""
        in_graph_entity = set()  # 用于检测是否有创建的实体了
        for i, head in enumerate(self.rel_dic):
            # 构建头实体 加name方便看,也方便找
            if head not in in_graph_entity:
                self.cypher += "CREATE (%s:人 {NAME:'%s'})" % (head, head) + "\n"
                in_graph_entity.add(head)
            # 构建头尾实体之间关系
            for relation, tail in self.rel_dic[head].items():
                # 构建尾实体 加name方便看,也方便找
                if tail not in in_graph_entity:
                    self.cypher += "CREATE (%s:人 {NAME:'%s'})" % (tail, tail) + "\n"
                    in_graph_entity.add(tail)
                self.cypher += "CREATE (%s)-[:%s]->(%s)" % (head, relation, tail) + "\n"
        self.num_cypher = len(self.cypher.split('CREATE'))

    def run_cypher(self):
        # 执行建表脚本
        st = time.time()
        clean_cypher = 'MATCH (n) DETACH DELETE n'
        self.graph.run(clean_cypher)
        print('清图耗时:', time.time() - st)

        st = time.time()
        self.graph.run(self.cypher)
        print('建图耗时:', time.time() - st)
        print('共执行%d条cypher语句' % self.num_cypher)

        for head in self.rel_dic:
            self.data['entities'].add(head)
            for rel, tail in self.rel_dic[head].items():
                self.data['relations'].add(rel)
                self.data['entities'].add(tail)

    def save_kg_data(self):
        # 转换成JSON serializable方便保存
        data = dict((x, list(y)) for x, y in self.data.items())
        with open(config['kg_data_path'], "w", encoding="utf8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys

    sys.path.append("../..")
    from config import config

    config['triplet_data_path'] = '../data/triplet_data.txt'
    config['kg_data_path'] = '../output/kg_data.json'

    br = Builder(config)
