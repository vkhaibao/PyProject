import cards_tools
while True:

    # TODO(小明) 显示系统菜单

    action = input("请选择操作功能："
                   "[1]新增名片 [2]显示所有名片 [3]查询 [4]修改或者删除"":"
                   )

    print("您选择的操作是：%s" % action)

    # 根据用户输入决定后续的操作
    if action in ["1", "2", "3", "4"]:
        if action == "1":
            cards_tools.new_card()

        elif action == "2":
            cards_tools.show_all()

        elif action == "3":
            cards_tools.search_card()
        elif action == "4":
            cards_tools.deal_card(cards_tools.find_dict())
    elif action == "0":
        print("欢迎再次使用【名片管理系统】")

        break
    else:
        print("输入错误，请重新输入")