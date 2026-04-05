import requests
import json
import hashlib
import re

class BaiduTool:
    "百度贴吧、知道签到类"
    def __init__(self, cookieData):
        "验证登录Cookie"
        #创建Session
        self.__session = requests.session()
        #添加Cookie
        requests.utils.add_dict_to_cookiejar(self.__session.cookies, cookieData)
        #设置Header
        self.__session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0","Referer":"https://www.baidu.com/"})
        #设置重试次数
        retry = requests.adapters.HTTPAdapter(max_retries=3)
        self.__session.mount('http://', retry)
        self.__session.mount('https://', retry)

        try:
            content = self.__session.get("http://tieba.baidu.com/dc/common/tbs", timeout=(10, 30))
        except Exception as e:
            raise Exception(f"登录验证异常: {e}")
        data = json.loads(content.text)
        if data["is_login"] == 0:
            raise Exception("登录失败：Cookie异常")
        self.__tbs = data["tbs"]
        self.name = self.getLoginInfo()["userName"]

        try:
            self.getUserInfo()
        except Exception as e:
            self.getTiebaLike = self.getTiebaLikeX
        else:
            self.getTiebaLike = self.getTiebaLikeG
    
    def getTiebaLikeX(self):
        "获取关注的贴吧列表（贴吧数量≤200时使用这个函数获取贴吧列表）"
        content = self.__session.get("https://tieba.baidu.com/mo/q/newmoindex", timeout=(10, 30))
        data = json.loads(content.text)
        if data["no"] == 0:
            return [x["forum_name"] for x in data["data"]["like_forum"]]
        else:
            return []

    def getTiebaLikeG(self):
        "获取关注的贴吧列表迭代器（贴吧数量>200时使用这个函数获取贴吧列表，需要Stoken）"
        content = self.__session.get("http://tieba.baidu.com/f/like/mylike?&pn=1", timeout=(10, 30))

        #获取页面数，每页有20个贴吧
        match = re.search(r'/f/like/mylike\?&pn=(.*?)">尾页', content.text, re.I)
        tpn = int(match.group(1)) if match else 1

        tp = 1 #当前页面
        #编译正则表达式
        pattern = re.compile(r'<a href="/f\?kw=.*?title="(.*?)"\>')
        while (tp <= tpn):
            #获取当前页面贴吧名称数组
            tbname = pattern.findall(content.text)
            for x in tbname:
                yield x

            #获取下一页面
            tp += 1
            if tp <= tpn:
                content = self.__session.get(f"http://tieba.baidu.com/f/like/mylike?&pn={tp}", timeout=(10, 30))

    def getLoginInfo(self):
        "获取登录信息"
        return self.__session.get("https://zhidao.baidu.com/api/loginInfo", timeout=(10, 30)).json()

    def getUserInfo(self):
        "获取用户信息（需要Stoken）"
        return self.__session.get("https://tieba.baidu.com/f/user/json_userinfo", allow_redirects=False, timeout=(10, 30)).json()

    def tiebaSign(self, name):
        "签到指定贴吧"
        md5 = hashlib.md5(f'kw={name}tbs={self.__tbs}tiebaclient!!!'.encode('utf-8')).hexdigest()
        data = {
            "kw": name,
            "tbs": self.__tbs,
            "sign": md5
            }
        #构造签到数据包，客户端对参数加了MD5验证
        content = self.__session.post("http://c.tieba.baidu.com/c/c/forum/sign", data=data, timeout=(10, 30))
        data = json.loads(content.text)
        if data["error_code"] == 0:
            return {"code":0,"info":f'获得经验:{data["user_info"]["sign_bonus_point"]}  已连续签到{data["user_info"]["cont_sign_num"]}天'}
        else:
            return {"code":int(data["error_code"]),"info":data["error_msg"]}

    def zhidaoSign(self):
        "签到百度知道"
        content = self.__session.get("https://zhidao.baidu.com/", timeout=(10, 30))
        match = re.search(r'stoken":"(.*?)"', content.text, re.I)
        if not match:
            return {"code": -1, "info": "无法提取Stoken"}
        stoken = match.group(1)
        #这个Stoken与Cookie里面的Stoken不是一个东西
        
        data = {
            "cm": "100509",
            "utdata": "91%2C91%2C106%2C97%2C97%2C102%2C98%2C91%2C99%2C103%2C97%2C100%2C126%2C106%2C100%2C102%2C15823570069820",
            "stoken": stoken
            }
        headers = {
            "Referer": "https://zhidao.baidu.com/",
            "X-Requested-With": "XMLHttpRequest",
            "X-Ik-Token": stoken
        }
        content = self.__session.post("https://zhidao.baidu.com/submit/user", data=data, timeout=(10, 30))
        data = json.loads(content.text)
        if data["errorNo"] == 0:
            return {"code":0,"info":"签到成功"}
        else:
            return {"code":data["errorNo"],"info":data["errorMsg"]}

    def zhidaoTask(self, taskId: int):
        "百度知道任务领取"
        content = self.__session.get("https://zhidao.baidu.com/", timeout=(10, 30))
        match = re.search(r'stoken":"(.*?)"', content.text, re.I)
        if not match:
            return {"code": -1, "info": "无法提取Stoken"}
        stoken = match.group(1)

        headers = {
            "Referer": "https://zhidao.baidu.com/",
            "X-Requested-With": "XMLHttpRequest",
            "X-Ik-Token": stoken
        }
        data = {
            "taskId": taskId,
            "stoken": stoken
            }
        content = self.__session.post("https://zhidao.baidu.com/task/submit/getreward", data=data, timeout=(10, 30))
        data = json.loads(content.text)
        return {"code":data["errno"],"info":data["errmsg"]}

def zhidaoShopLottery(self):
        "百度知道商城免费抽奖"
        content = self.__session.get("https://zhidao.baidu.com/shop/lottery", timeout=(10, 30))
        
        # 1. 提取 LuckyToken
        match_lucky = re.search(r"luckyToken',\s*'(.*?)'", content.text, re.I)
        if not match_lucky:
            return {"code": -1, "info": "未能获取LuckyToken"}
        luckytoken = match_lucky.group(1)
        
        # 2. 提取 Stoken (用于伪装成 x-ik-token 请求头)
        match_stoken = re.search(r'stoken":"(.*?)"', content.text, re.I)
        if not match_stoken:
            return {"code": -1, "info": "未能获取Stoken"}
        stoken = match_stoken.group(1)
        
        # 3. 构造全新的请求头，加入 x-ik-token 校验
        headers = {
            "Referer": "https://zhidao.baidu.com/shop/lottery",
            "X-Requested-With": "XMLHttpRequest",
            "X-Ik-Token": stoken
        }
        
        # 4. 构造 POST 载荷
        data = {
            "type": 0,
            "token": luckytoken
        }
        
        # 5. 改用 POST 请求
        content = self.__session.post("https://zhidao.baidu.com/shop/submit/lottery", data=data, headers=headers, timeout=(10, 30))

        # JSON解析校验
        try:
            res_data = json.loads(content.text)
        except json.JSONDecodeError:
            return {"code": -1, "info": "未返回有效的JSON数据"}

        if res_data["errno"] == 0:
            # 抽奖成功时，提取中奖物品名称（如："25财富值"）
            return {"code": 0, "info": res_data["data"]["prizeList"][0]["name"]}
        else:
            return {"code": res_data["errno"], "info": res_data.get("errmsg", "未知错误")}
