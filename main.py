import requests
import re
import json
import selenium
import time
import sys
from selenium import webdriver

__data__ = sys.path[0] + r'\data'

# 别忘了在这里改用户名和密码
# 其实这里可以把用户名和密码封装成类的属性
# 但是我懒
# 主要是涉及到好几个函数需要改
# 如果在这里改动执行不通过的话
# 就把下面

__username__ = ''
__password__ = ''

class TopicSearch():
    def __init__(self, keyword: str):
        self.topicPage = []
        self.topicList = []
        self.pageList = []
        self.postList = []
        self.postContent = []
        self.finished = []
        self.autoSave = sys.path[0] + '\\autosave\\' + keyword + '.json'
        print("Launching the webdriver...", end="")
        try:
            edgePath = r'MicrosoftWebDriver.exe'
            self.driver = webdriver.Edge(executable_path=edgePath)
        except selenium.common.exceptions.WebDriverException:
            self.driver = None
            print("Executable not found")
        else:
            print("OK")

    def __del__(self):
        self.driver.quit()

    def reload(self):
        self.driver.quit()
        print("Launching the webdriver...", end="")
        try:
            edgePath = r'MicrosoftWebDriver.exe'
            self.driver = webdriver.Edge(executable_path=edgePath)
        except selenium.common.exceptions.WebDriverException:
            self.driver = None
            print("Executable not found")
        else:
            print("OK")

    def dumpToFile(self):
        indexList = []
        global __data__
        for post in self.postContent:
            fileName = str(post['id'])
            indexList.append(post['id'])
            with open(__data__ + '\\' + fileName + '.json', 'w', encoding='utf-8') as file:
                json.dump(post, file, ensure_ascii=False)
        with open(__data__ + '\\index.json', 'w', encoding='utf-8') as file:
            json.dump(indexList, file, ensure_ascii=False)

    def saveStatus(self):
        with open(self.autoSave, 'w', encoding='utf-8') as file:
            json.dump({
                'topicPage': self.topicPage,
                'topicList': self.topicList,
                'pageList': self.pageList,
                'postList': self.postList,
                'postContent': self.postContent,
                'finishedPost': self.finished,
                'autoSave': self.autoSave
            }, file)

    def loadStatus(self, filePath: str):
        status = {}
        print('---------------------')
        print('Loading file from', filePath)
        with open(filePath, encoding='utf-8') as file:
            status = json.load(file)
        self.topicPage = status['topicPage']
        self.topicList = status['topicList']
        self.pageList = status['pageList']
        self.postList = status['postList']
        self.postContent = status['postContent']
        print(len(self.postContent), 'posts saved')
        self.finished = status['finishedPost']
        print(len(self.finished), 'pages scrapped')
        print('---------------------')
        self.autoSave = filePath

    def searchKeyword(self, keyword: str):
        print('Info:    Searching for the keyword', keyword, '...')
        driver = self.driver
        url = "https://s.weibo.com/topic?q=%s&pagetype=topic&topic=1&Refer=weibo_topic" % (
            keyword,)
        driver.get(url)
        self.topicList = ['https://s.weibo.com' + re.sub(
            '&amp;', '&', item) for item in re.findall('<li><a href="(.*?)">第', driver.page_source)]
        self.topicList.append(url)
        print('Info:    Success.', len(self.topicList), 'URLs retrieved.')
        self.saveStatus()

    def preprocessTopicList(self):
        cnt = 0
        driver = self.driver
        for page in self.topicList:
            driver.get(page)
            content = driver.page_source
            self.topicPage.extend(re.findall(
                '<a class="name" href="(.*?)" ', content))
            cnt += 1
            print('Info:    Page', cnt, 'scrapped. |',
                  len(self.topicPage), 'pending')
            if cnt % 25 == 0:
                print('Info:    Wait for 10 seconds.')
                self.saveStatus()
                time.sleep(10)

    def testPages(self):
        '''
        从微博话题页面中获取每页微博的连接，需要先执行`preprocessTopicList()`函数
        '''
        cnt = 0
        for page in self.topicPage:
            cnt += 1
            self.testPage(page)
            print('Info:    Testing page', cnt, ', ',
                  len(self.topicPage), 'in total.')
            if cnt % 50 == 0:
                print('Info:    Wait for 10 seconds.')
                self.saveStatus()
                time.sleep(10)
            if cnt % 250 == 0:
                self.reload()
                self.getLoginCookie()

    def getLoginCookie(self):
        '''
        跳转到微博界面并登录，为保证成功登录，程序会在登录前暂停45秒，在登录后暂停10秒
        '''
        global __username__, __password__
        time.sleep(45)
        driver = self.driver
        print("Info:    Logging in...")
        driver.get("http://www.weibo.com/login.php")
        while True:
            try:
                driver.find_element_by_xpath('//*[@id="loginname"]').send_keys(
                    __username__)
                driver.find_element_by_xpath(
                    '//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(__password__)
                driver.find_element_by_xpath(
                    '//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
                driver.find_element_by_xpath(
                    '//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
                break
            except selenium.common.exceptions.ElementNotInteractableException:
                print('Error:   Elements not interactable')
                print('Refreshing the page...')
                driver.refresh()
                time.sleep(20)
            except selenium.common.exceptions.InvalidSelectorException:
                print("Info:    Already logged in")
                break
        print('Info:    Wait for 10 seconds')
        time.sleep(10)
        try:
            driver.find_element_by_xpath('//*[@id="loginname"]')
        except selenium.common.exceptions.InvalidSelectorException:
            print("Info:    Success")
        else:
            print("Error:   Login failed")
            self.getLoginCookie()

    def testPage(self, url: str) -> str:
        '''
        从微博话题页面中提取话题页面每页的链接，被`TestPages()`函数调用
        '''
        driver = self.driver
        while True:
            driver.get(url)
            curTime = time.time()
            print('Info:    Received:', len(driver.page_source) / 1024, 'KiB')
            if '您最近的访问环境异常，请先进行身份验证!' in driver.page_source:
                print('Error:   Abnormal response')
                time.sleep(45)
            else:
                break
        linkList = re.findall(
            '<li><a href="(.*?)">第.*?页</a></li>', driver.page_source)
        self.pageList.extend(
            ['https://s.weibo.com' + re.sub('&amp;', '&', item) for item in linkList])
        self.pageList.append(url)
        print('Info:    Page tested.', len(self.pageList), 'pages pending')
        return (curTime, driver.page_source)

    def scrapPage(self, url: str) -> tuple:
        '''
        抓取每页微博的内容，每页有25篇微博，平均20篇是不重复的微博
        '''
        driver = self.driver
        while True:
            fail = True
            while fail:
                try:
                    driver.get(url)
                except selenium.common.exceptions.TimeoutException:
                    fail = True
                    driver.refresh()
                    time.sleep(15)
                except (
                    ConnectionRefusedError,
                    urllib3.exceptions.NewConnectionError,
                    urllib3.exceptions.MaxRetryError
                ):
                    fail = True
                    time.sleep(10)
                else:
                    fail = False
            curTime = time.time()
            contentLen = len(driver.page_source) / 1024
            if not '您最近的访问环境异常，请先进行身份验证!' in driver.page_source:
                print('Info:    Received:', contentLen, 'KiB')
                self.finished.append(url)
                return {'content': driver.page_source, 'colTime': curTime}
            else:
                print('Error:   Abnormal resopnse.')
                self.driver.delete_all_cookies()
                self.getLoginCookie()

    def scrapList(self):
        '''
        抓取列表中的所有微博
        '''
        cnt = 0
        for page in self.pageList:
            cnt += 1
            if page in self.finished:
                print('Info:    Page', cnt, 'already scrapped')
                # 跳过已完成的页面，用于自动保存文件的重新加载
                continue
            print("Scrapping page", cnt, '|', len(self.pageList), 'in total')
            self.postContent.extend(self.analyzePage(**self.scrapPage(page)))
            if cnt % 50 == 0:
                print('Info:    Wait for 10 seconds.', 'Totally',
                      len(self.postContent), 'received.')
                self.saveStatus()
                time.sleep(10)
            if cnt % 500 == 0:
                print('Info:    Clearing the memory.')
                self.reload()
                self.getLoginCookie()
        self.saveStatus()

    def analyzePage(self, content: str, colTime: float) -> list:
        '''
        接受`scrapPage`函数返回的结果，使用正则表达式对微博内容进行提取
        '''
        contents = re.findall(
            r'<div class="card-wrap" action-type="feed_list_item" mid=".*?">\n([\d\D]*?)<!--/card-wrap-->', content)
        # 分析发现微博页面的内容可以提取为结构化的数据块
        postContents, postLinks, postInteractions, postVIP = [], [], [], []
        for post in contents:
            postContents.append(re.findall(
                '<p class="txt" .*? nick-name="(.*?)">\n([\s\S]*?)</p>', post)[-1])
            # 某些较长的微博会存在“展开全文”，因此选择提取最后一段内容
            postLinks.append(re.findall(
                '<p class="from">\n.*?<a href="(.*?)" target="_blank" .*?">([\s\S]*?)</a>', post)[-1])
            postInteractions.append(re.findall(
                '转发 (.*?)</a></li>\n[\s\S]*?评论 (.*?)</a></li>[\s\S]*?<em>(.*?)</em>', post)[-1])
            temp = re.findall('icon-vip-(.*?)"', post)
            postVIP.append(temp[0] if temp else [''])
            # 获取用户认证信息
        weiboPosts = []
        weiboPost = {}
        for x, y, z, u in zip(postContents, postInteractions, postLinks, postVIP):
            weiboPost = {}
            weiboPost['link'] = 'https:' + re.search(
                '(//weibo.com/.*?/.*?)\?', z[0]).group()[:-1]
            weiboPost['id'] = hash(weiboPost['link'])
            # 使用hash值唯一确定微博，有极小概率出现重复
            if weiboPost['id'] in self.postList:
                continue
            # 跳过重复的微博
            weiboPost['uName'] = x[0]
            weiboPost['content'] = re.sub('<.*?>', '', x[1])
            weiboPost['content'] = re.sub('[\s\n]*?', '', weiboPost['content'])
            # 清除HTML标记
            weiboPost['uid'] = re.findall(
                '//weibo.com/(.*?)/', weiboPost['link'])[0]
            weiboPost['uVIP'] = u
            weiboPost['time'] = re.sub('[\n]*?', '', z[1]).strip()
            weiboPost['time'] = re.sub(
                ' ([^x00-xff][\s\S]*)$', '', weiboPost['time'])
            # 有些时间会出现“转赞人数超过……”
            try:
                weiboPost['forward'] = int(
                    y[0]) if y[0] else 0
            except ValueError:
                weiboPost['forward'] = 1000000
            try:
                weiboPost['comment'] = int(
                    y[1]) if y[1] else 0
            except ValueError:
                weiboPost['comment'] = 1000000
            try:
                weiboPost['like'] = int(
                    y[2]) if y[2] else 0
            except ValueError:
                weiboPost['like'] = 1000000
            # 检查100w+的情况，把100w+视为100w
            weiboPost['collectTime'] = colTime
            weiboPost['keyWords'] = re.findall('#(.*?)#', weiboPost['content'])
            # 正文中以`#'分隔的是关键词（但是当正文里有#号时会出现识别错误，不清楚机制）
            self.postList.append(weiboPost['id'])
            weiboPosts.append(weiboPost)
        print('Info:    ', len(weiboPosts), 'weibos processed.')
        return weiboPosts


def mergeLists(src1: list, src2: list) -> list:
    idList = []
    target = []
    try:
        for item in src1:
            if not item['id'] in idList:
                target.append(item)
                idList.append(item['id'])
        for item in src2:
            if not item['id'] in idList:
                target.append(item)
                idList.append(item['id'])
    except:
        target = []
        idList = []
    finally:
        return target


def searchForKeyWord(keyWordList: list) -> list:
    result = []
    try:
        for keyword in keyWordList:
            temp = TopicSearch(keyword)
            try:
                with open(temp.autoSave, 'r', encoding='utf-8') as file:
                    pass
            except FileNotFoundError:
                temp.getLoginCookie()
                temp.searchKeyword(keyword)
                time.sleep(10)
                temp.preprocessTopicList()
                time.sleep(10)
                temp.testPages()
                time.sleep(10)
                temp.scrapList()
            else:
                temp.loadStatus(temp.autoSave)
                if len(temp.finished) < len(temp.pageList):
                    temp.getLoginCookie()
                    temp.scrapList()
                else:
                    print(keyword, 'has been scrapped')
            result.extend(temp.postContent)
    finally:
        return result


if __name__ == "__main__":
    # weibo = TopicSearch()
    # weibo.getLoginCookie()
    # weibo.loadStatus(
    #     r'F:\VS Code\workspace\python\datamining\weibo\autosave.json')
    # weibo.scrapList()
    keyWordList = ['核酸检测', '援助物资', '境外输入', '有序复工',
                   '硬核防疫', '热干面醒了', '特朗普决定不再使用中国病毒说法', '疫情评估', '居家隔离', '离鄂通道', '美国疫情', '意大利疫情', '英国疫情', '西班牙疫情', '欧洲疫情', '韩国疫情', '日本疫情', '湖北 重启', '方舱', '美国 确诊', '意大利 确诊', '韩国 确诊', '日本 确诊', '抗疫 启程', '疫情', '口罩']
    result = searchForKeyWord(keyWordList)
    with open(r'F:\VS Code\workspace\python\datamining\weibo\posts.json', 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False)
