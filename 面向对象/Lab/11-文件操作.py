# *-* coding:utf8 *-*
import os


"""
02. 文件的基本操作
    在 计算机 中要操作文件的套路非常固定，一共包含三个步骤：

    打开文件
        读、写文件
        读 将文件内容读入内存
    写 将内存内容写入文件
        关闭文件

    2.2 操作文件的函数/方法
        在 Python 中要操作文件需要记住 1 个函数和 3 个方法
            序号	函数/方法	说明
            01	open	打开文件，并且返回文件操作对象
            02	read	将文件内容读取到内存
            03	write	将指定内容写入文件
            04	close	关闭文件
        open 函数负责打开文件，并且返回文件对象
        read/write/close 三个方法都需要通过 文件对象 来调用

    2.3 read 方法 —— 读取文件
        open 函数的第一个参数是要打开的文件名（文件名区分大小写）
            如果文件 存在，返回 文件操作对象
            如果文件 不存在，会 抛出异常
        read 方法可以一次性 读入 并 返回 文件的 所有内容
        close 方法负责 关闭文件
        如果 忘记关闭文件，会造成系统资源消耗，而且会影响到后续对文件的访问
        注意：read 方法执行后，会把 文件指针 移动到 文件的末尾
            # 1. 打开 - 文件名需要注意大小写
            file = open("README")

            # 2. 读取
            text = file.read()
            print(text)

            # 3. 关闭
            file.close()
        在开发中，通常会先编写 打开 和 关闭 的代码，再编写中间针对文件的 读/写 操作！

        文件指针（知道）

        文件指针 标记 从哪个位置开始读取数据
        第一次打开 文件时，通常 文件指针会指向文件的开始位置
        当执行了 read 方法后，文件指针 会移动到 读取内容的末尾
            默认情况下会移动到 文件末尾

        思考

        如果执行了一次 read 方法，读取了所有内容，那么再次调用 read 方法，还能够获得到内容吗？
        答案

        不能
        第一次读取之后，文件指针移动到了文件末尾，再次调用不会读取到任何的内容
    2.4 打开文件的方式
        open 函数默认以 只读方式 打开文件，并且返回文件对象
        f = open("文件名", "访问方式")
            访问方式	说明
            r	以只读方式打开文件。文件的指针将会放在文件的开头，这是默认模式。如果文件不存在，抛出异常
            w	以只写方式打开文件。如果文件存在会被覆盖。如果文件不存在，创建新文件
            a	以追加方式打开文件。如果该文件已存在，文件指针将会放在文件的结尾。如果文件不存在，创建新文件进行写入
            r+	以读写方式打开文件。文件的指针将会放在文件的开头。如果文件不存在，抛出异常
            w+	以读写方式打开文件。如果文件存在会被覆盖。如果文件不存在，创建新文件
            a+	以读写方式打开文件。如果该文件已存在，文件指针将会放在文件的结尾。如果文件不存在，创建新文件进行写入
        频繁的移动文件指针，会影响文件的读写效率，开发中更多的时候会以 只读、只写 的方式来操作文件
        写入文件示例
            # 打开文件
            f = open("README", "w")

            f.write("hello python！\n")
            f.write("今天天气真好")

            # 关闭文件
            f.close()
    2.5 按行读取文件内容
        read 方法默认会把文件的 所有内容 一次性读取到内存
        如果文件太大，对内存的占用会非常严重
        readline 方法
        readline 方法可以一次读取一行内容
        方法执行后，会把 文件指针 移动到下一行，准备再次读取
        读取大文件的正确姿势
        # 打开文件
            file = open("README")

            while True:
                # 读取一行内容
                text = file.readline()

                # 判断是否读到内容
                if not text:
                    break

                # 每读取一行的末尾已经有了一个 `\n`
                print(text, end="")

            # 关闭文件
            file.close()
"""
file = open("./05-继承.py", encoding='utf-8')
while True:
    # 读取一行内容
    text = file.readline()

    # 判断是否读到内容
    if not text:
        break

    # 每读取一行的末尾已经有了一个 `\n`
    print(text, end="")

# 关闭文件
file.close()
print("*=" * 50)
"""
2.6 文件读写案例 —— 复制文件
    目标

    用代码的方式，来实现文件复制过程
    
    小文件复制
    打开一个已有文件，读取完整内容，并写入到另外一个文件
    # 1. 打开文件
        file_read = open("README")
        file_write = open("README[复件]", "w")
        
        # 2. 读取并写入文件
        text = file_read.read()
        file_write.write(text)
        
        # 3. 关闭文件
        file_read.close()
        file_write.close()
    
    大文件复制
    打开一个已有文件，逐行读取内容，并顺序写入到另外一个文件   
    # 1. 打开文件
        file_read = open("README")
        file_write = open("README[复件]", "w")
        
        # 2. 读取并写入文件
        while True:
            # 每次读取一行
            text = file_read.readline()
        
            # 判断是否读取到内容
            if not text:
                break
        
            file_write.write(text)
        
        # 3. 关闭文件
        file_read.close()
        file_write.close()     
"""
# 小文件复制
file = open("./05-继承.py", encoding='utf-8')
filecopy = open("../copy.py", 'w')
text = file.read()
filecopy.write(text)
file.close()
filecopy.close()


# 大文件复制
file = open("./05-继承.py", encoding='utf-8')
filecopy = open("../copy02.py", 'w')
while True:
    text = file.readline()
    if not text:
        break
        pass
    filecopy.write(text)

file.close()
filecopy.close()
print("*&" * 50)

"""
03. 文件/目录的常用管理操作
    在 终端 / 文件浏览器、 中可以执行常规的 文件 / 目录 管理操作，例如：
        创建、重命名、删除、改变路径、查看目录内容、……
    在 Python 中，如果希望通过程序实现上述功能，需要导入 os 模块
    文件操作
        序号	方法名	说明	示例
        01	rename	重命名文件	os.rename(源文件名, 目标文件名)
        02	remove	删除文件	os.remove(文件名)
    
    目录操作
        序号	方法名	说明	示例
        01	listdir	目录列表	os.listdir(目录名)
        02	mkdir	创建目录	os.mkdir(目录名)
        03	rmdir	删除目录	os.rmdir(目录名)
        04	getcwd	获取当前目录	os.getcwd()
        05	chdir	修改工作目录	os.chdir(目标目录)
        06	path.isdir	判断是否是文件	os.path.isdir(文件路径)
    提示：文件或者目录操作都支持 相对路径 和 绝对路径   
"""
#os.rename("../copy.py", "../copy01.py")
print(os.listdir("../"))

"""
4.1 ASCII 编码和 UNICODE 编码
    ASCII 编码
        计算机中只有 256 个 ASCII 字符
        一个 ASCII 在内存中占用 1 个字节 的空间
    UTF-8 编码格式
        计算机中使用 1~6 个字节 来表示一个 UTF-8 字符，涵盖了 地球上几乎所有地区的文字
        大多数汉字会使用 3 个字节 表示
        UTF-8 是 UNICODE 编码的一种编码格式  
    unicode 字符串       
        要能够正确的遍历字符串，在定义字符串时，需要 在字符串的引号前，增加一个小写字母 u，
        告诉解释器这是一个 unicode 字符串（使用 UTF-8 编码格式的字符串）     
    # *-* coding:utf8 *-*

        # 在字符串前，增加一个 `u` 表示这个字符串是一个 utf8 字符串
        hello_str = u"你好世界"
        
        print(hello_str)
        
        for c in hello_str:
            print(c)                 
"""
hello_str = u"你好世界"

print(hello_str)

for c in hello_str:
    print(c)