# coding=utf8
from multiprocessing import Queue
q = Queue(10)
for i in (range(7)):
    q.put("孙海宝")
    print(q.full())

try:
    q.put("消息4", True, 2)
    print("现有消息数量:%s" % q.qsize())
except:
    print("消息列队已满，现有消息数量:%s" % q.qsize())

try:
    q.put_nowait("消息4")
except:
    print("消息列队已满，现有消息数量:%s" % q.qsize())
#推荐的方式，先判断消息列队是否已满，再写入
if not q.full():
    q.put_nowait("消息4")

#读取消息时，先判断消息列队是否为空，再读取
if not q.empty():
    for i in range(q.qsize()):
        print(q.get_nowait())