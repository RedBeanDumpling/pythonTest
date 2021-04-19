import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request


class Blockchain(object):
    # 区块链初始化
    def __init__(self):
        self.chain = []  # 此列表表示区块链对象本身。
        self.currentTransaction = []  # 此列表用于记录目前在区块链网络中已经经矿工确认合法的交易信息，等待写入新区块中的交易信息。
        self.nodes = set()  # 建立一个无序元素集合。此集合用于存储区块链网络中已发现的所有节点信息
        # Create the genesis block(创建创世区块)
        self.new_block(proof=100, previous_hash=1)

    # 创建新区块
    def new_block(self, proof, previous_hash=None):
        # Creates a new Block and adds it to the chain(创建一个新的区块，并将其加入到链中)
        """
        生成新块
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
         """
        block = {
            'index': len(self.chain) + 1,  # 区块编号
            'timestamp': time(),  # 时间戳
            'transactions': self.currentTransaction,  # 交易信息
            'proof': proof,  # 矿工通过算力证明（工作量证明）成功得到的Number Once值，证明其合法创建了一个区块（当前区块）
            'previous_hash': previous_hash or self.hash(self.chain[-1])  # 前一个区块的哈希值
        }

        # Reset the current list of transactions(重置当前事务列表)
        '''
        因为已经将待处理（等待写入下一下新创建的区块中）交易信息列表（变量是：transactions）
        中的所有交易信息写入了区块并添加到区块链末尾，则此处清除此列表中的内容'
        '''
        self.currentTransaction = []
        # 将当前区块添加到区块链末端
        self.chain.append(block)
        return block

    # 创建新交易
    def new_transaction(self, sender, recipient, amount):
        # Adds a new transaction to the list of transactions(向交易列表中添加一个新的交易)
        """
                生成新交易信息，此交易信息将加入到下一个待挖的区块中
                :param sender: Address of the Sender  # 发送方
                :param recipient: Address of the Recipient # 接收方
                :param amount: Amount  # 数量
                :return: The index of the Block that will hold this transaction # 需要将交易记录在下一个区块中
        """
        self.currentTransaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        # 下一个待挖的区块中
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # 根据一个区块 来生成这个区块的哈希值（散列值）
        """
               生成块的 SHA-256 hash值
               :param block: <dict> Block
               :return: <str>
               转化为json编码格式之后hash，最后以16进制的形式输出
         """

        # 我们必须确保字典是有序的，否则我们会有不一致的哈希值，sort_keys=True指明了要进行排序
        '''
        首先通过json.dumps方法将一个区块打散，并进行排序（保证每一次对于同一个区块都是同样的排序）
        这个时候区块被转换成了一个json字符串（不知道怎么描述）
        然后，通过json字符串的encode()方法进行编码处理。
        其中encode方法有两个可选形参，第一个是编码描述字符串，另一个是预定义错误信息
        默认情况下，编码描述字符串参数就是：默认编码为 'utf-8'。此处就是默认编码为'utf-8'
        '''
        block_string = json.dumps(block, sort_keys=True).encode()
        # hexdigest(…)以16进制的形式输出
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]  # 区块链的最后一个区块

    # 工作量证明
    def proof_of_work(self, lastProof):
        """
        简单的工作量证明:
         - 查找一个 p' 使得 hash(pp') 以4个0开头
         - p 是上一个块的证明,  p' 是当前的证明
        :param last_proof: <int>
        :return: <int>
        """

        # #下面通过循环来使proof的值从0开始每次增加1来进行尝试，直到得到一个符合算法要求 的proof值为止
        proof = 0
        while self.valid_proof(lastProof, proof) is False:
            proof += 1  # 如果得到的proof值不符合要求，那么就继续寻找。
        # 返回这个符合算法要求的proof值
        return proof

    #  此函数是上一个方法函数的附属部分，用于检查哈希值是否满足挖矿条件。用于工作函数的证明中
    @staticmethod
    def valid_proof(lastProof, proof):
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        # 根据传入的参数proof来进行尝试运算，得到一个转码为utf-8格式的字符串
        guess = f'{lastProof}{proof}'.encode()
        # 将此字符串（guess）进行sha256方式加密，并转换为十六进制的字符串
        guessHash = hashlib.sha256(guess).hexdigest()
        # 验证该字符前4位是否为0，如果符合要求，就返回True，否则 就返回False
        return guessHash[:4] == '0000'


# 实例化我们的节点；加载 Flask 框架
app = Flask(__name__)

# 为我们的节点创建一个随机名称
node_identifier = str(uuid4()).replace('-', '')

# 实例化 Blockchain 类
blockchain = Blockchain()


# 创建 /transactions/new 端点，这是一个 POST 请求，我们将用它来发送数据
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # 将请求参数做了处理，得到的是字典格式的，因此排序会打乱依据字典排序规则
    values = request.get_json()

    # 检查所需字段是否在过账数据中
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400  # HTTP状态码等于400表示请求错误

    # 创建新交易
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


# 创建 /mine 端点，这是一个GET请求
@app.route('/mine', methods=['GET'])
def mine():
    # 我们运行工作证明算法来获得下一个证明
    last_block = blockchain.last_block  # 取出区块链现在的最后一个区块
    last_proof = last_block['proof']  # 取出这最后 一个区块的哈希值（散列值）
    proof = blockchain.proof_of_work(last_proof)  # 获得了一个可以实现优先创建（挖出）下一个区块的工作量证明的proof值。

    # 由于找到了证据，我们会收到一份奖励
    # sender为“0”，表示此节点已挖掘了一个新货币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # 将新块添加到链中打造新的区块
    previous_hash = blockchain.hash(last_block)  # 取出当前区块链中最长链的最后一个区块的Hash值，用作要新加入区块的前导HASH（用于连接）
    block = blockchain.new_block(proof, previous_hash)  # 将新区快添加到区块链最后

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


# 创建 /chain 端点，它是用来返回整个 Blockchain类
@app.route('/chain', methods=['GET'])
# 将返回本节点存储的区块链条的完整信息和长度信息。
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# 设置服务器运行端口为 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

