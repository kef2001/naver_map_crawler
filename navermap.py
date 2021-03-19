#coding:utf-8
import requests
from multiprocessing import Pool
from urllib import parse
import pandas as pd
import time
import json

headers = {'accept': 'application/json, text/plain, */*',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4',
'cache-control': 'no-cache',
'content-type': 'application/json',
'pragma': 'no-cache',
'referer': 'https://map.naver.com/',
'sec-ch-ua': '"Chromium";v="86", "\"Not\\A;Brand";v="99", "Whale";v="2"',
'sec-ch-ua-mobile': '?0',
'sec-fetch-dest': 'empty',
'sec-fetch-mode': 'cors',
'sec-fetch-site': 'same-origin',
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Whale/2.9.115.16 Safari/537.36'}
s = requests.Session()

def getQuery(search,page):
    query = {'caller': 'pcweb',
    'query' : search,
    'type' : 'all',
    'searchCoord' : '127.11621522903444;37.32955988981438',
    'page': page,
    'displayCount': 20,
    'isPlaceRecommendationReplace': True,
    'lang' : 'ko'
    }
    return (parse.urlencode(query,encoding='UTF-8',doseq=True))

def getRequests(text):
    query = getQuery(text,15)
    mapurl = 'https://map.naver.com/v5/api/search'
    mainpage = s.get(mapurl,params = query,headers=headers)
    getjson = mainpage.json()
    info = {}
    if getjson['result']['type'] != 'place':
        print('검색어가 잘못되었습니다.')
        return
    total = getjson['result']['place']['totalCount']
    if total <20:
        page = total // 20
    elif total > 20:
        page = total // 20
        if page > 15:
            page = 16
    for i in getjson['result']['place']['list']:
        info[i['name']] = {'id':i['id'],'storename':i['name'],'category':i['category'][0],'reviewCount':i['reviewCount'],\
            'hasNaverBooking':i['hasNaverBooking'],'roadAddress':i['roadAddress'],'address':i['address'],'tel':i['tel'],'score':0}

    for i in range(2,page):
        query = getQuery(text,i)
        secondpage = s.get(mapurl,params = query,headers=headers)
        secondjson = secondpage.json()
        for j in secondjson['result']['place']['list']:
            info[j['name']] = {'id':j['id'],'storename':j['name'],'category':j['category'][0],'reviewCount':j['reviewCount'],\
            'hasNaverBooking':j['hasNaverBooking'],'roadAddress':j['roadAddress'],'address':j['address'],'tel':j['tel'],'score':0}
        time.sleep(0.3) # 너무 빠른 속도로 차단당하지 않기 위해 일정 간격을 둠
        
        print(i,' 페이지 추출중')

        for i in info:
            storeid = info[i]['id']
            detailurl = f'https://map.naver.com/v5/api/sites/detail/{storeid}?lang=ko'
            info[i]['detailurl'] = detailurl
        
        pool = Pool(processes = 2)
        result = []
        result = pool.map(getDetail, info.values())
        pool.close()
        pool.join()

        return result

def getDetail(t):
    url = t['detailurl']
    detailpage = s.get(url,headers=headers)
    detailjson = detailpage.json()

    t['to_go'] = False
    t['delivery'] = False
    if detailjson.get('bookingReviews'):
        score = detailjson['bookingReviews']['avgScore']
        t['score'] = score
    for j in detailjson['summary']['options']:
        if j['name'] == '포장':
            t['to_go'] = True
        if j['name'] =='배달':
            t['delivery'] = True
    return t


def main():
    text = input("검색어를 입력해주세요 \n>>>>")
    result = getRequests(text)
    data = pd.DataFrame(result)
    del data['id']
    del data['hasNaverBooking']
    del data['detailurl']
    data.to_csv('output.csv',encoding='utf-8-sig')

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(int(end-start),"초 소요됨")