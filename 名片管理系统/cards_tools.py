card_list = []


def show_menu():

    """显示菜单
    """
    print("*" * 50)
    print("欢迎使用【菜单管理系统】V1.0")
    print("")
    print("1. 新建名片")
    print("2. 显示全部")
    print("3. 查询名片")
    print("")
    print("0. 退出系统")
    print("*" * 50)


def new_card():

    """新建名片
    """
    print("-" * 50)
    print("功能：新建名片")
    # 1. 提示用户输入名片信息
    name = input("请输入姓名：")
    phone = input("请输入电话：")
    qq = input("请输入 QQ 号码：")
    email = input("请输入邮箱：")

    # 2. 将用户信息保存到一个字典
    card_dict = {"name": name,
                 "phone": phone,
                 "qq": qq,
                 "email": email}
    # 3. 将用户字典添加到名片列表
    card_list.append(card_dict)
    print(card_dict)

    # 4. 提示添加成功信息
    print("成功添加 %s 的名片" % card_dict["name"])


def show_all():

    """显示全部
    """
    print("-" * 50)
    print("功能：显示全部")
    # 打印表头
    for name in ["姓名", "电话", "QQ", "邮箱"]:
        print(name, end="\t\t")

    print("")

    # 打印分隔线
    print("=" * 50)
    if len(card_list) == 0:
        print("提示：没有任何名片记录")
        return
    else:
        for card_dict in card_list:
            print("%s\t\t%s\t\t%s\t\t%s" % (card_dict["name"],
                                        card_dict["phone"],
                                        card_dict["qq"],
                                        card_dict["email"]))


def search_card():

    """搜索名片
    """
    print("-" * 50)
    print("功能：搜索名片")
    find_name = input("请输入姓名：")
    for card_dict in card_list:
        if card_dict["name"] == find_name:
            print("姓名\t\t\t电话\t\t\tQQ\t\t\t邮箱")
            print("-" * 40)
            print("%s\t\t%s\t\t%s\t\t%s" % (card_dict["name"],
                                        card_dict["phone"],
                                        card_dict["qq"],
                                        card_dict["email"]))
            break
        else:
             print("找不到这个人 %s" % find_name)


def deal_card(find_dict):
    print(find_dict)
    action_str = input("请选择要执行的操作"
                       "[1]修改 [2]删除 [0]返回上级菜单"
                       )
    if action_str == "1":
        find_dict["name"] = input("请输入姓名：")
        find_dict["phone"] = input("请输入电话：")
        find_dict["qq"] = input("请输入QQ：")
        find_dict["email"] = input("请输入邮件：")
        print("%s 的名片修改成功" % find_dict["name"])
    elif action_str == "2":
        card_list.remove(find_dict)
        print("删除成功")
    elif action_str == "0":
        print("返回上级菜单")


def find_dict():
    find_name = input("请输入姓名：")
    for card_dict in card_list:
        if card_dict["name"] == find_name:
            print(card_dict)
            return card_dict




