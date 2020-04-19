import pandas as pd
import numpy as np
import sys
import json
import re
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules

__keyWordList__ = [
    # 疫情相关（公共关键词）
    '疫情', '口罩', '病毒', '隔离', '新冠', '中国', '感染', '无症状', '发烧', '志愿者',
    '义工', '确诊', '长期存在', '检测', '突变', '捐赠', '阴性', '阳性', '死亡', '重症',
    'ICU', '治愈', '14天', '医生', '病例', '隐瞒', '发热', '发烧', '数据', '控制',
    '结束'
    # 国内疫情
    '武汉', '钟南山', '张文宏', '卫健委', '李文亮', '吹哨人', '雷神山', '火神山',
    'N95', '预约', '封城', '中央', '武汉加油', '院士', '抗疫', '希望', '封闭', '清零',
    '结束', '过去', '硬核', '果断', '致敬', '恢复', '免费', '信心', '奇迹', '平安',
    # 国际疫情
    '英国', '欧洲', '扣押', '意大利', '特朗普', '美国', '群体免疫', '塞尔维亚', '输入',
    '美联储', '白宫', '流感', '经验',
    # 新年
    '春运', '过年', '拜年', '年夜饭'
    # 复工
    '复工',
    # 学生群体
    '钉钉', '开学', '小学生', '中学生', '大学生', '毕业', '高考', '中考', '武汉大学',
    '清华大学', '华中科技大学', '复旦大学', '上海交通大学', '北京大学', '网课',
    # 其他关键词
    '2020', '今年', '火车', '飞机',
    # 旅游业相关
    '樱花',  '珞珈山', '黄鹤楼', '热干面', '奶茶',
]
__json_path__ = r'F:\VS Code\workspace\python\datamining\weibo\HW01.json'


class WeiboData():
    def __init__(self, fileName: str):
        temp = None
        self.rawData = []
        self.rawTopic = []
        with open(fileName, 'r', encoding='utf-8') as file:
            temp = pd.DataFrame(json.load(file))
            self.rawData = temp['content']
            self.rawTopic = temp['keyWords']
        # for record in self.rawData:
        #     record = re.sub('#.*?#', '', record)
        self.binaryMatrix = None
        self.keyWordMatrix = None
        self.result = None

    def preprocess(self, keyWordList: list):
        self.keyWordMatrix = []
        temp = None
        for record in self.rawData:
            temp = []
            for keyWord in keyWordList:
                if keyWord in record:
                    temp.append(keyWord)
            self.keyWordMatrix.append(temp)

    def toBinary(self):
        temp = TransactionEncoder()
        temp2 = temp.fit(self.keyWordMatrix).transform(self.keyWordMatrix)
        self.binaryMatrix = pd.DataFrame(temp2, columns=temp.columns_)

    def applyAprioriContent(self, support: float) -> pd.DataFrame:
        self.result = apriori(
            self.binaryMatrix, min_support=support, use_colnames=True, low_memory=True)
        temp = association_rules(
            self.result, metric='confidence', min_threshold=0.8)
        return temp

    def applyAprioriTopic(self, support: float) -> pd.DataFrame:
        processor = TransactionEncoder()
        binary = processor.fit(self.rawTopic).transform(self.rawTopic)
        return association_rules(apriori(
            pd.DataFrame(binary, columns=processor.columns_),
            min_support=support,
            use_colnames=True,
            low_memory=True
        ), metric='confidence', min_threshold=0.8
        )


def isSubset(src1, src2):
    return set(src1).issubset(src2)


def shrink(src: pd.DataFrame) -> pd.DataFrame:
    dropList = []
    targetList = src['itemsets']
    for i in range(len(src)):
        for j in range(i + 1, len(src)):
            if len(targetList[i]) < len(targetList[j]) and isSubset(targetList[i], targetList[j]) and i not in dropList:
                dropList.append(i)
    print(len(src) - len(dropList))
    return src.drop(dropList)


if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    dataset = WeiboData(__json_path__)
    dataset.preprocess(__keyWordList__)
    dataset.toBinary()
    # Windows 版本的 Excel 支持的csv编码格式为GBK编码，Linux与macOS系统可能需要将GBK编码改成UTF-8编码才能正常显示数据
    # 或者…… Excel 应该也可以修改打开文档的默认编码
    file = open(r'C:\Users\huang\OneDrive - mails.tsinghua.edu.cn\文档\上课\大二下学期\数据挖掘：方法与应用\pattern.csv',
                'w', newline='', encoding='gbk')
    dataset.applyAprioriContent(0.0005).to_csv(file)
    file.close()
    file = open(r'C:\Users\huang\OneDrive - mails.tsinghua.edu.cn\文档\上课\大二下学期\数据挖掘：方法与应用\patternTopic.csv',
                'w', newline='', encoding='gbk')
    dataset.applyAprioriTopic(0.0001).to_csv(file)
    file.close()
