def get_triplet_data(config):
    triplet = []
    need_people = ['刘备', '张飞', '关羽']
    with open(config['row_data_path'], encoding='utf8') as lines:
        for line in lines:
            head, tail, rel = line.split('###')[:3]
            triplet.append([head, rel, tail])
    writer = open(config['triplet_data_path'], 'w', encoding='utf8')
    for head, rel, tail in triplet:
        if head in need_people or tail in need_people:
            writer.write('%s\t%s\t%s\n' % (head, rel, tail))
    writer.close()
    return triplet


if __name__ == '__main__':
    import sys

    sys.path.append('..')
    from config import config

    config['row_data_path'] = '../data/rel_data.txt'
    config['triplet_data_path'] = '../data/triplet_data.txt'
    test = get_triplet_data(config)
