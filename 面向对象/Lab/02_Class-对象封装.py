"""
01. 封装
1、封装 是面向对象编程的一大特点
2、面向对象编程的 第一步 —— 将 属性 和 方法 封装 到一个抽象的 类 中
3、外界 使用 类 创建 对象，然后 让对象调用方法
4、对象方法的细节 都被 封装 在 类的内部
"""
class person:
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

    def __str__(self):
        return "%s的体重%.2f" % (self.name, self.weight)

    def run(self):
        print("%s爱跑步" % self.name)
        self.weight -= 0.5

    def eat(self):
        print("%s吃货" % self.name)
        self.weight += 1.0


xiaoming = person("小明", 75)

xiaoming.run()
xiaoming.eat()
xiaoming.eat()
xiaoming.run()
xiaoming.run()
xiaoming.run()
xiaoming.run()
xiaoming.run()

xiaomei = person("小美", 45)

xiaomei.run()
xiaomei.eat()


print(xiaoming)

print(xiaomei)


"""
需求

房子(House) 有 户型、总面积 和 家具名称列表
新房子没有任何的家具
家具(HouseItem) 有 名字 和 占地面积，其中
席梦思(bed) 占地 4 平米
衣柜(chest) 占地 2 平米
餐桌(table) 占地 1.5 平米
将以上三件 家具 添加 到 房子 中
打印房子时，要求输出：户型、总面积、剩余面积、家具名称列表

剩余面积

在创建房子对象时，定义一个 剩余面积的属性，初始值和总面积相等
当调用 add_item 方法，向房间 添加家具 时，让 剩余面积 -= 家具面积
"""


class HouseItem:
    def __init__(self, name, area):
        """

        :param name:家具名称
        :param area:占地面积
        """
        self.name = name
        self.area = area

    def __str__(self):
        return "[%s] 占地面积 %.2f" % (self.name, self.area)


"""
剩余面积

在创建房子对象时，定义一个 剩余面积的属性，初始值和总面积相等
当调用 add_item 方法，向房间 添加家具 时，让 剩余面积 -= 家具面积
"""


class House:
    def __init__(self, house_type, area):
        self.house_type = house_type
        self.area = area
        self.free_area = area
        self.item_list = []

    def __str__(self):
        return ("户型：%s\n总面积：%.2f[剩余：%.2f]\n家具：%s"
                % (self.house_type, self.area,
                   self.free_area, self.item_list[:]))

    def add_item(self, item):
        print("要添加 %s" % item)
        if item.area > self.free_area:
            print("%s 的面积太大，不能添加到房子中" % item.name)
            return
        # 2. 将家具的名称追加到名称列表中
        self.item_list.append(item.name)

        # 3. 计算剩余面积
        self.free_area -= item.area


# 创建家具


bed = HouseItem("席梦思", 4)
chest = HouseItem("衣柜", 2)
table = HouseItem("餐桌", 1.5)
print(bed.area)
print(chest.area)
print(table.area)

# 2. 创建房子对象


my_home = House("两室一厅", 60)

my_home.add_item(bed)
my_home.add_item(chest)
my_home.add_item(table)

print(my_home)






