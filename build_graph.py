from config import config
from src.prepare_data import get_triplet_data
from src.builder import Builder

if __name__ == '__main__':
    triplet_data = get_triplet_data(config)
    br = Builder(config)
