#coding=utf8
jsondic = dict
jsondic = {
        "正式环境": {
            "host01": ["hdd01", "hdd02"],
            "host02": ["hdd01", "hdd02"]
        },
        "测试环境": {
            "host03": ["hdd01", "hdd02"],
            "host04": ["hdd01", "hdd02"]
        }
    }
jsondic["正式环境"]["host01"].append("hdd03")
print(jsondic["正式环境"]["host01"])