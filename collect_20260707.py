# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, email.utils, datetime as dt, re, json, sys
from html import unescape
KST=dt.timezone(dt.timedelta(hours=9))
today=dt.datetime.now(KST).date()
headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
def fetch(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=20) as r: return r.read()
def rss(q,hl='ko',gl='KR',ceid='KR:ko',n=15):
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':hl,'gl':gl,'ceid':ceid})
    out=[]
    try:
        root=ET.fromstring(fetch(url))
        for item in root.findall('.//item'):
            title=unescape(item.findtext('title') or '')
            link=item.findtext('link') or ''
            pub=item.findtext('pubDate') or ''
            src=item.find('source'); source=src.text if src is not None else ''
            try: t=email.utils.parsedate_to_datetime(pub).astimezone(KST)
            except Exception: t=None
            if t and t.date()==today:
                # filter noisy
                if any(bad in title for bad in ['운세','스포츠','부고','인사','영상','다시보기']): continue
                out.append({'title':title,'source':source,'time':t.strftime('%H:%M KST'),'link':link,'pubDate':pub})
    except Exception as e:
        out.append({'error':str(e),'q':q})
    return out[:n]
def uniq(arr):
    seen=set(); out=[]
    for x in arr:
        if 'error' in x: continue
        key=re.sub(r'\s+-\s+.*$','',x['title']).strip()
        if key and key not in seen:
            seen.add(key); out.append(x)
    return out
queries={
 'ai':['AI 반도체 데이터센터 전력 생성형AI after:2026-07-07 before:2026-07-08','AI칩 HBM 삼성전자 SK하이닉스 엔비디아 after:2026-07-07 before:2026-07-08','오픈AI 앤트로픽 AI 스타트업 after:2026-07-07 before:2026-07-08','데이터센터 전력 AI after:2026-07-07 before:2026-07-08'],
 'world':['세계뉴스 국제 이란 홍해 미국 중국 유럽 after:2026-07-07 before:2026-07-08','국제뉴스 우크라이나 러시아 중동 미국 after:2026-07-07 before:2026-07-08','홍해 이란 이스라엘 미국 폭염 중국 AI after:2026-07-07 before:2026-07-08'],
 'domestic':['국내뉴스 한국 경제 반도체 환율 증시 after:2026-07-07 before:2026-07-08','삼성전자 실적 코스피 환율 반도체 클러스터 after:2026-07-07 before:2026-07-08','한국 AI 데이터센터 전력 반도체 클러스터 after:2026-07-07 before:2026-07-08'],
 'market':['뉴욕증시 마감 2026년 7월 6일 나스닥 다우 S&P500','미국 증시 마감 2026년 7월 6일 반도체 엔비디아 테슬라']
}
res={}
for k,qs in queries.items():
    arr=[]
    for q in qs: arr += rss(q,n=20)
    res[k]=uniq(arr)[:12]
# Naver prices for previous connection ideas from latest json/html fallback
stocks={'SK하이닉스':'000660','HD현대일렉트릭':'267260','대한전선':'001440','삼성전자':'005930','한화에어로스페이스':'012450'}
prices={}
for name,code in stocks.items():
    url=f'https://finance.naver.com/item/sise_day.naver?code={code}&page=1'
    try:
        txt=fetch(url).decode('euc-kr','ignore')
        rows=re.findall(r'<span class="tah p10 gray03">([0-9.]+)</span>.*?<span class="tah p11">([0-9,]+)</span>', txt, re.S)
        prices[name]=rows[:6]
    except Exception as e: prices[name]=str(e)
res['prices']=prices
open('broad_20260707.json','w',encoding='utf-8').write(json.dumps(res,ensure_ascii=False,indent=2))
print(json.dumps({k:len(v) if isinstance(v,list) else 'prices' for k,v in res.items()},ensure_ascii=False))
