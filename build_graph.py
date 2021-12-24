import re
import json
import time
from py2neo import Graph
from config import config
from collections import defaultdict

# 连接图数据库
graph = Graph("http://localhost:7474", auth=("neo4j", "123456"))

rel_dic = defaultdict(dict)


def clean_text(head, rel, tail):
    head = re.sub('·| |（.+）|\(.+\)', '', head)
    rel = re.sub('·| |《|》|、|（.+）|，|&', '', rel)
    tail = re.sub('·| |（.+）|\(.+\)', '', tail)
    return head, rel, tail


# 读取实体-关系-实体三元组文件
with open(config['triplet_data_path'], encoding="utf8") as lines:
    i = 0
    for line in lines:
        head, rel, tail = line.strip().split("\t")  # 取出三元组
        if bool(re.search(r'\d', head)) or bool(re.search(r'\d', rel)) or bool(re.search(r'\d', tail)):
            continue
        head, rel, tail = clean_text(head, rel, tail)
        rel_dic[head][rel] = tail
        # i += 1
        # if i >= 500:
        #     break

# 构建cypher语句
cypher = ""
in_graph_entity = set()

for i, head in enumerate(rel_dic):

    # 构建头实体 加name方便看
    if head not in in_graph_entity:
        cypher += "CREATE (%s:人 {NAME:'%s'})" % (head, head) + "\n"
        in_graph_entity.add(head)

    for relation, tail in rel_dic[head].items():

        # 构建对应的尾实体
        if tail not in in_graph_entity:
            cypher += "CREATE (%s:人 {NAME:'%s'})" % (tail, tail) + "\n"
            in_graph_entity.add(tail)

        # 构建头尾实体之间关系
        cypher += "CREATE (%s)-[:%s]->(%s)" % (head, relation, tail) + "\n"
num_cypher = len(cypher.split('CREATE'))
# 执行建表脚本
st = time.time()
clean_cypher = 'MATCH (n) DETACH DELETE n'
graph.run(clean_cypher)
print('清图耗时:', time.time() - st)

st = time.time()
graph.run(cypher)
print('建图耗时:', time.time() - st)

data = defaultdict(set)
for head in rel_dic:
    data['entities'].add(head)
    for rel, tail in rel_dic[head].items():
        data['relations'].add(rel)
        data['entities'].add(tail)

# 转换成JSON serializable方便保存
data = dict((x, list(y)) for x, y in data.items())

with open(config['kg_data_path'], "w", encoding="utf8") as f:
    f.write(json.dumps(data, ensure_ascii=False, indent=2))

