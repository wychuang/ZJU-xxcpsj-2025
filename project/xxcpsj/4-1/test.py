import urllib.request
try:
    urllib.request.urlopen("http://www.xfyun.cn")
    print("网络连接正常")
except:
    print("网络连接问题")