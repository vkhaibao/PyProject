# coding=utf8
class Fib(object):
    def __init__(self, n):
        self.n = n
        self.current = 0
        self.num1 = 0
        self.num2 = 1

    def __next__(self):
        """被next()函数调用来获取下一个数"""
        if self.current < self.n:
            num = self.num1
            self.num1, self.num2 = self.num2, self.num1+self.num2
            self.current += 1
            return num
        else:
            raise StopIteration

    def __iter__(self):
        """迭代器的__iter__返回自身即可"""
        return self


fib = Fib(15)
for num in fib:
    print(num, end="\n")
    
li = list(Fib(15))
print(li)
tp = tuple(Fib(6))
print(tp)
