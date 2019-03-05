class cat:

    def __init__(self, name):
        self.name = name

    def eat(self):
        print("%s 吃鱼" % self.name)

    def drink(self):
        print("%s 喝水" % self.name)

    def __del__(self):
        print("%s 去了" % self.name)

    def __str__(self):
        return "我是小猫：%s" % self.name



print("-" * 50)

print(dir(cat))

print(cat.eat(cat("tom")))
