"""
stage0_mooc_dataset.py
Reads the Chinese MOOC dataset, translates DSA concepts to English,
and saves outputs/concept_nodes.csv with 100+ concepts.
Run this ONCE before stage3_relations.py.
"""
import json, pandas as pd, os

CN_TO_EN = {
    '数组':'array','动态数组':'dynamic array','动态数组类':'dynamic array',
    '多维数组':'multidimensional array','创建多维数组':'multidimensional array',
    '数组下标':'array index','数组下标运算':'array index',
    '数组元素':'array element','数组元素逻辑次序':'array element',
    '链表':'linked list','单链表':'singly linked list',
    '双向链表':'doubly linked list','循环链表':'circular linked list',
    '链表节点':'linked list node','哈希链表节点':'linked list node',
    '栈':'stack','栈顶':'stack top','栈底':'stack bottom',
    '进栈':'push','出栈':'pop','栈溢出':'stack overflow',
    '队列':'queue','循环队列':'circular queue','双端队列':'deque',
    '优先队列':'priority queue','事件队列':'event queue','等待队列':'waiting queue',
    '树':'tree','二叉树':'binary tree','完全二叉树':'binary tree',
    '二叉搜索树':'binary search tree','平衡二叉搜索树':'binary search tree',
    '平衡二叉树':'balanced binary tree','红黑树':'red-black tree',
    'AVL树':'avl tree','B树':'b-tree','B+树':'b+ tree',
    '哈夫曼树':'huffman tree','堆':'heap','最小堆':'min heap','最大堆':'max heap',
    '字典树':'trie','前缀树':'trie','线段树':'segment tree',
    '搜索树':'search tree','语法树':'syntax tree','生成树':'spanning tree',
    '层次遍历':'level order traversal','遍历':'traversal',
    '根节点':'root node','根节点 ':'root node','叶节点':'leaf node','节点':'node',
    '图':'graph','有向图':'directed graph','幅有向图':'directed graph',
    '无向图':'undirected graph','加权图':'weighted graph',
    '连通图':'connected graph','强连通图':'strongly connected graph',
    '邻接矩阵':'adjacency matrix','邻接表':'adjacency list',
    '深度优先搜索':'depth-first search','广度优先搜索':'breadth-first search',
    '最短路':'shortest path','最短路径':'shortest path',
    '最短路径问题':'shortest path','最小生成树':'minimum spanning tree',
    '拓扑排序':'topological sort','拓扑排序的序列':'topological sort',
    '排序':'sorting','冒泡排序':'bubble sort','选择排序':'selection sort',
    '插入排序':'insertion sort','快速排序':'quicksort',
    '合并排序':'merge sort','归并排序':'merge sort','堆排序':'heap sort',
    '基数排序':'radix sort','计数排序':'counting sort',
    '计数排序算法':'counting sort','桶排序':'bucket sort','交换排序':'exchange sort',
    '二分搜索':'binary search','二分查找':'binary search',
    '线性搜索':'linear search','顺序查找':'sequential search','搜索':'searching',
    '哈希':'hashing','散列':'hashing','散列函数':'hash function',
    '哈希表':'hash table','散列表':'hash table','哈希冲突':'hash collision',
    '时间复杂度':'time complexity','空间复杂度':'space complexity',
    '计算复杂度':'computational complexity',
    '算法复杂度':'algorithm complexity','计算算法复杂度':'algorithm complexity',
    '大O符号':'big-o notation','渐近分析':'asymptotic analysis',
    '算法正确性':'algorithm correctness',
    '递归':'recursion','递推':'recurrence','迭代':'iteration',
    '动态规划':'dynamic programming','记忆化':'memoization',
    '贪心':'greedy algorithm','贪心法':'greedy algorithm',
    '分治':'divide and conquer','回溯':'backtracking',
    '指针':'pointer','引用':'reference','内存':'memory',
    '动态内存分配':'memory allocation','内存管理':'memory management',
    '内存分配':'memory allocation',
    '并查集':'union find','不相交集合':'disjoint set',
    '字符串':'string','字符串匹配':'string matching',
    '算法':'algorithm','数据结构':'data structure',
}

def translate(cn):
    cn = cn.strip()
    if cn in CN_TO_EN:
        return CN_TO_EN[cn]
    for k, v in CN_TO_EN.items():
        if k in cn and len(k) >= 3:
            return v
    return None

def build_concept_nodes():
    os.makedirs('outputs', exist_ok=True)

    # 1. CS course IDs
    cs_ids = set()
    with open('data/raw/course-field.json', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            if ('计算机科学与技术' in item.get('field',[]) or
                    '软件工程' in item.get('field',[])):
                cs_ids.add('C_' + str(item['course_id']))
    print(f"CS courses: {len(cs_ids)}")

    # 2. CS concept IDs
    cs_concept_ids = set()
    with open('data/raw/concept-course.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2 and parts[1] in cs_ids:
                cs_concept_ids.add(parts[0])
    print(f"CS concepts: {len(cs_concept_ids)}")

    # 3. Translate to English (deduplicated)
    seen_en = set()
    rows = []
    with open('data/raw/concept.json', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if item['id'] not in cs_concept_ids:
                continue
            en = translate(item['name'])
            if en and en not in seen_en:
                seen_en.add(en)
                rows.append({'concept_id': item['id'],
                             'name_cn': item['name'],
                             'concept': en})

    # 4. Also add all concepts from the caption datasets
    caption_concepts = [
        'array','binary search','binary search tree','divide and conquer',
        'graph','hash table','heap','kruskal','minimum spanning tree',
        'pointer','prim','priority queue','queue','radix sort','recursion',
        'shortest path','sorting','stack','symbol table','trie','union find',
        'big-o notation',
    ]
    for c in caption_concepts:
        if c not in seen_en:
            seen_en.add(c)
            rows.append({'concept_id': 'caption_dataset',
                         'name_cn': c, 'concept': c})

    df = pd.DataFrame(rows).drop_duplicates(subset=['concept'])
    df.to_csv('outputs/concept_nodes.csv', index=False)

    print(f"\n✅ Total unique English concepts: {len(df)}")
    print("All concepts:")
    for c in sorted(df['concept'].tolist()):
        print(f"  {c}")
    return df

if __name__ == '__main__':
    build_concept_nodes()