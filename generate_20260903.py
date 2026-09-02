#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import html, json, re, textwrap, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
YMD = '20260903'
KOR_DATE = '2026년 9월 3일 목요일'
MARKER = f'MORNING_BRIEFING_{YMD}'
ROOT = Path('/Users/taesungkim/morning-reports')
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
HTML_PATH = ROOT / f'daily-briefing-{YMD}.html'
WORLD_IMG = ASSETS / f'world-webtoon-{YMD}.png'
DOMESTIC_IMG = ASSETS / f'domestic-webtoon-{YMD}.png'
UA = {'User-Agent': 'Mozilla/5.0 morning-report-bot'}

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def yahoo(symbol: str):
    data = json.loads(fetch(f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=5d&interval=1d'))['chart']['result'][0]
    closes = [x for x in data['indicators']['quote'][0]['close'] if x is not None]
    price = float(closes[-1]); prev = float(closes[-2])
    return {'symbol': symbol, 'price': price, 'change': price - prev, 'pct': (price - prev) / prev * 100}

def naver_day(code: str):
    raw = fetch(f'https://finance.naver.com/item/sise_day.naver?code={code}').decode('euc-kr', 'ignore')
    dates = re.findall(r'<span class="tah p10 gray03">([0-9]{4}\.[0-9]{2}\.[0-9]{2})</span>', raw)
    prices = re.findall(r'<td class="num"><span class="tah p11">([0-9,]+)</span></td>', raw)
    rows = []
    for i, d in enumerate(dates[:10]):
        base = i * 6
        if base < len(prices):
            rows.append((d, prices[base]))
    return rows

def pct_change(new: str, old: str) -> float:
    n = int(new.replace(',', '')); o = int(old.replace(',', ''))
    return (n - o) / o * 100

def esc(s): return html.escape(str(s), quote=True)
def yt_url(title: str): return 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(title)

def card_html(n, item):
    return f'''<article class="news-card"><div class="num">{n:02d}</div><div class="news-copy"><div class="eyebrow">{esc(item['cat'])}</div><h3>{esc(item['title'])}</h3><p class="source">{esc(item['source'])} · {esc(item['time'])}</p><p><strong>내용요약</strong> {esc(item['summary'])}</p><p><strong>예상여파</strong> {esc(item['impact'])}</p></div><div class="actions"><a class="btn primary" href="{esc(item['link'])}" target="_blank" rel="noopener noreferrer">기사보기</a><a class="btn ghost" href="{esc(yt_url(item['title']))}" target="_blank" rel="noopener noreferrer">유튜브 영상 보기</a></div></article>'''

def metric_line(name, obj):
    return f"<div class=\"metric\"><b>{esc(name)}</b><span>{obj['price']:,.2f} · {obj['change']:+,.2f} ({obj['pct']:+.2f}%)</span></div>"

def load_font(size):
    for p in ['/System/Library/Fonts/AppleSDGothicNeo.ttc', '/System/Library/Fonts/Supplemental/AppleGothic.ttf', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf']:
        try: return ImageFont.truetype(p, size=size)
        except Exception: pass
    return ImageFont.load_default()

def draw_panel(draw, box, theme, title, caption, bg):
    x0,y0,x1,y1 = box
    F24,F22,F18 = load_font(24), load_font(22), load_font(18)
    draw.rounded_rectangle(box, radius=24, fill=bg, outline='#17120e', width=6)
    draw.rectangle((x0, y0+44, x1, y0+48), fill='#17120e')
    draw.text((x0+18, y0+10), title, font=F24, fill='#241910')
    cx, cy = (x0+x1)//2, (y0+y1)//2 - 16
    def person(px, py, coat='#4b79b6'):
        draw.ellipse((px-24, py-70, px+24, py-22), fill='#f3d5b8', outline='#20140f', width=3)
        draw.rounded_rectangle((px-34, py-20, px+34, py+54), radius=18, fill=coat, outline='#20140f', width=3)
        draw.line((px, py+54, px-22, py+95), fill='#20140f', width=5); draw.line((px, py+54, px+26, py+93), fill='#20140f', width=5)
        draw.line((px-32, py+6, px-60, py-6), fill='#20140f', width=5); draw.line((px+32, py+6, px+58, py-10), fill='#20140f', width=5)
    def chip(px, py):
        draw.rounded_rectangle((px-70, py-45, px+70, py+45), radius=14, fill='#eef4fb', outline='#23344d', width=4)
        for dx in (-90,-78,78,90):
            draw.line((px+dx, py-24, px+dx, py+24), fill='#23344d', width=4)
        for dy in (-60,-48,48,60):
            draw.line((px-24, py+dy, px+24, py+dy), fill='#23344d', width=4)
        draw.text((px-24, py-18), 'AI', font=F24, fill='#9f2f26')
    if theme == 'tariff-chip':
        chip(cx-70, cy+20); draw.rectangle((cx+20, cy-30, cx+150, cy+90), fill='#fff7e8', outline='#6b4c2c', width=4)
        draw.text((cx+42, cy+10), 'TARIFF', font=F22, fill='#9f2f26'); person(cx+118, cy+112, '#5f8a73')
    elif theme == 'price-tag':
        draw.rounded_rectangle((cx-200, cy-20, cx-30, cy+96), radius=18, fill='#eef4fb', outline='#23344d', width=4)
        draw.text((cx-162, cy+12), 'PRICE', font=F22, fill='#23344d'); draw.text((cx+18, cy+8), '↑', font=F24, fill='#9f2f26'); person(cx+104, cy+112, '#a4654c')
    elif theme == 'fx-budget':
        draw.rectangle((cx-200, cy-24, cx-42, cy+92), fill='#fffdf8', outline='#23344d', width=4); draw.text((cx-170, cy+10), 'FX', font=F22, fill='#23344d')
        draw.rectangle((cx+8, cy-20, cx+134, cy+86), fill='#eef4fb', outline='#23344d', width=4); draw.text((cx+28, cy+12), 'BUDGET', font=F22, fill='#9f2f26'); person(cx+118, cy+112, '#5b84ba')
    elif theme == 'shopping':
        draw.rounded_rectangle((cx-188, cy-22, cx-42, cy+90), radius=18, fill='#fff7e8', outline='#6b4c2c', width=4)
        draw.text((cx-160, cy+10), 'MART', font=F22, fill='#6b4c2c'); draw.line((cx+24, cy-10, cx+90, cy+56), fill='#d43a30', width=7); person(cx+110, cy+112, '#7862a8')
    elif theme == 'assembly':
        draw.rounded_rectangle((cx-210, cy-28, cx+144, cy+96), radius=20, fill='#eef4fb', outline='#23344d', width=4)
        draw.text((cx-162, cy+10), 'ASSEMBLY', font=F22, fill='#23344d'); person(cx-110, cy+112, '#5a88c7'); person(cx+56, cy+112, '#a4654c')
    elif theme == 'policy':
        draw.rectangle((cx-180, cy+8, cx-40, cy+92), fill='#d8b39b', outline='#6b4c2c', width=4)
        draw.text((cx-150, cy+16), 'PLAN', font=F22, fill='#6b4c2c'); draw.rectangle((cx+18, cy-20, cx+126, cy+88), fill='#eef4fb', outline='#23344d', width=4)
        draw.text((cx+34, cy+14), 'RICE', font=F22, fill='#9f2f26'); person(cx+116, cy+112, '#5f8a73')
    elif theme == 'rain':
        draw.rectangle((cx-200, cy+24, cx+140, cy+86), fill='#9dc3e8', outline='#264a72', width=4)
        for bx,by,w,h,c in [(-180,-10,78,94,'#c88860'),(-86,-22,64,106,'#b9c7d8'),(6,-4,72,88,'#d8b39b')]: draw.rectangle((cx+bx, cy+by, cx+bx+w, cy+by+h), fill=c, outline='#264a72', width=4)
        draw.line((cx-26, cy-18, cx-6, cy+36), fill='#2d7fb9', width=5); draw.line((cx+12, cy+4, cx+32, cy+52), fill='#2d7fb9', width=5); person(cx-40, cy+112, '#7862a8')
    elif theme == 'local-city':
        draw.rectangle((cx-190, cy-28, cx-30, cy+94), fill='#fff7e8', outline='#6b4c2c', width=4); draw.text((cx-156, cy+10), 'CITY', font=F22, fill='#6b4c2c')
        draw.rectangle((cx+10, cy-34, cx+126, cy+88), fill='#eef4fb', outline='#23344d', width=4); draw.text((cx+34, cy+12), 'ASK', font=F24, fill='#23344d'); person(cx+116, cy+114, '#5a88c7')
    elif theme == 'factory-ai':
        draw.rectangle((cx-200, cy-12, cx-30, cy+92), fill='#d8b39b', outline='#6b4c2c', width=4); draw.rectangle((cx+10, cy-20, cx+122, cy+82), fill='#eef4fb', outline='#23344d', width=4)
        draw.text((cx+34, cy+10), 'AI', font=F24, fill='#9f2f26'); person(cx+126, cy+112, '#5f8a73')
    else:
        person(cx, cy+84)
    draw.rounded_rectangle((x0+18, y1-98, x1-18, y1-18), radius=18, fill='#fffdf8', outline='#1a1713', width=4)
    draw.multiline_text((x0+30, y1-86), textwrap.fill(caption, width=17), font=F18, fill='#1d2432', spacing=4)

def draw_paper(title, scenes, outpath):
    W,H=1600,2200
    img=Image.new('RGB',(W,H),'#f3e7d1'); d=ImageDraw.Draw(img)
    for y in range(0,H,10): d.line((0,y,W,y), fill=(244,236,220), width=1)
    d.rounded_rectangle((24,24,W-24,H-24), radius=36, fill='#f7ecd9', outline='#15110d', width=8)
    d.rounded_rectangle((66,56,W-66,176), radius=24, fill='#182744', outline='#10192c', width=4)
    F60,F26 = load_font(60), load_font(26)
    d.text((96,82), title, font=F60, fill='white'); d.text((96,138), '실제 PNG 만평 · 반복 구도 대신 이슈별 다른 장면', font=F26, fill='#f6d29f')
    margin_x,margin_y,gap=70,220,28; pw=(W-margin_x*2-gap)//2; ph=(H-margin_y-90-gap*3)//4
    fills=['#fff7ee','#eaf3ff','#fff2e6','#f3efff','#eef8ef','#fff8dd','#edf6f7','#fff0f0']
    for i,(ttl,caption,theme) in enumerate(scenes):
        r,c=divmod(i,2); x0=margin_x+c*(pw+gap); y0=margin_y+r*(ph+gap); x1=x0+pw; y1=y0+ph
        draw_panel(d, (x0,y0,x1,y1), theme, f'{i+1:02d}. {ttl}', caption, fills[i])
    img=img.filter(ImageFilter.UnsharpMask(radius=1,percent=130,threshold=3)); img.save(outpath)

market = {k: yahoo(v) for k, v in [('S&P 500','^GSPC'),('나스닥','^IXIC'),('다우','^DJI'),('러셀2000','^RUT'),('SOXX','SOXX'),('달러/원','KRW=X'),('WTI','CL=F'),('VIX','^VIX')]}
review_names = [('지투파워','388050'),('대한전선','001440'),('SK하이닉스','000660')]
review_rows = []
for name, code in review_names:
    rows = naver_day(code)
    d1, p1 = rows[0]; d0, p0 = rows[1]
    review_rows.append({'name':name,'code':code,'d1':d1,'p1':p1,'d0':d0,'p0':p0,'pct':pct_change(p1,p0)})

candidate_pool = ['대한전선','LS ELECTRIC','한미반도체','SK하이닉스','이수페타시스','한화비전']
idea_cards = [
    {'name':'대한전선','code':'001440.KS','theme':'AI 전력망·송배전 직결 베타','reason':'AI 데이터센터와 미국 내 반도체 생산 확대 뉴스는 결국 전력망과 송배전 투자로 번지기 쉽습니다. 한국장에서는 대형 반도체보다 전선·변압기 쪽이 장 초반 검색량과 수급 민감도로 먼저 반응하는지 관찰하는 메모가 적절합니다.','point':'전선·변압기 동조화, 거래대금 급증 여부, 북미 전력 인프라 기사 재확산'},
    {'name':'한미반도체','code':'042700.KS','theme':'후공정 장비·미국 반도체 생산 확대 민감주','reason':'미국의 반도체 표적관세 예고는 단순 관세 이슈를 넘어 현지 생산과 공급망 재배치 압박을 키우는 뉴스입니다. 한국장에서는 메모리 대표주보다 후공정 장비와 패키징 체인 종목이 뉴스 민감도로 먼저 움직이는지 볼 필요가 있습니다.','point':'HBM 장비주 동반 강도, 외국인·기관 수급, 미국 생산 확대 해석'},
    {'name':'SK하이닉스','code':'000660.KS','theme':'AI 메모리 대표 기준선','reason':'반도체 관세와 미국 생산 압박 뉴스가 커질수록 결국 메모리 대형주의 시초가와 외국인 수급이 전체 반도체 해석의 기준선이 됩니다. 오늘도 강한 방향 판단보다 대표주의 반응을 기준선으로 두는 편이 맞습니다.','point':'시초가 갭, 외국인 수급, SOXX 강세의 국내 연장 여부'}
]

summary_bullets_ai = [
    '오늘 AI·스타트업 면은 모델 성능 경쟁보다 운영 책임, 의료 데이터 연결, 금융창구 자동화, 대형 자금조달, 지역 인재 육성처럼 실제 도입 단계 뉴스가 앞줄에 섰습니다.',
    '오픈소스 인프라 책임 논쟁은 AI 도입의 병목이 이제 모델 선택보다 운영·보안·장애 대응 체계로 이동하고 있음을 보여줍니다.',
    '의료 데이터 통합과 은행 멀티모달 상담 뉴스는 AI가 민감 정보와 규제 산업 깊숙이 들어가면서 신뢰·설명 책임이 더 중요해지고 있음을 시사합니다.',
    '원더풀의 대규모 자금 유치와 지자체 교육 프로그램은 AI 경쟁이 빅테크만의 이야기가 아니라 자본시장과 인재 양성으로도 확장되고 있음을 보여줍니다.',
    '시장 연결은 보조선으로만 두고, 오늘은 AI가 산업 운영 방식과 공공·금융·의료의 업무 구조를 어떻게 바꾸는지 읽는 브리핑으로 보는 편이 적절합니다.'
]
ai_news = [
    {'cat':'운영·인프라','title':'“AI 모델보다 중요한 건 운영”…오픈소스 인프라, 누가 책임지나 - 디지털데일리','source':'디지털데일리','time':'09-03 06:00 KST 전후','link':'https://news.google.com/rss/articles/CBMiYkFVX3lxTE5HTWRkVHl3NU12eGV6eFRWQTlWaDR0NDF1ak1zOWpXZE1NVXpsS003WnlRanpKZ3d5aDRQTkVHS181YkEzREpfMnhhZEUzRjNSNHFTRU5WX0s2QXVrRkxBV09B?oc=5','summary':'오픈소스 기반 AI 인프라를 실제 서비스로 굴릴 때 누가 장애와 보안, 업데이트 책임을 질 것인지 짚은 기사입니다. AI 경쟁의 핵심이 모델 성능표보다 운영 안정성과 책임 구조로 옮겨가고 있음을 보여줍니다.','impact':'기업 현장에서는 새로운 모델 도입보다 운영 거버넌스와 보안 체계 점검이 먼저 중요해질 수 있고, 공공·금융권 도입 속도에도 영향을 줄 가능성이 있습니다.'},
    {'cat':'의료 데이터','title':'흩어진 의료데이터 하나로 잇는 힘…의료 AI ‘미래 여는 열쇠’ [건강한겨레] - 한겨레','source':'한겨레','time':'09-03 05:01 KST 전후','link':'https://news.google.com/rss/articles/CBMia0FVX3lxTE9Tc2NNSFY2MGxMUmt1ZW5YbTlHTHI2Nmp3aEZOSnFxYzJjS044b0Y4d2xwdGdIeDk2elF0U0ppcG9RdmF1cmptWWIyaFR0UnpDT1NtVGgxT3ZDc1pSbVkwNG53UjFkb0U2aGN3?oc=5','summary':'흩어진 의료 데이터를 연결해 의료 AI 활용도를 높이는 흐름을 다룬 기사입니다. 의료 AI의 성패가 알고리즘 자체보다 데이터 표준화와 연결 인프라에 달려 있음을 보여줍니다.','impact':'병원·보험·공공보건 분야에서 데이터 연동과 개인정보 보호 논의가 함께 커질 수 있고, 실제 도입 속도는 규제 정비에 좌우될 가능성이 있습니다.'},
    {'cat':'금융 AI','title':'은행 AI 상담, 전화·화면으로…\'멀티모달 금융창구\' 경쟁 - 전자신문','source':'전자신문','time':'09-02 17:00 KST 전후','link':'https://news.google.com/rss/articles/CBMiTkFVX3lxTFAxZHVMdl93bWVTWDU3eGxSekJsVnFmNDBSaV9jUzVZM25qcGVRSkRiY3pUUEpLeUZzbzQxMnRSX05sX0tPaVJUY2dSYWVzZw?oc=5','summary':'은행권이 전화와 화면을 결합한 멀티모달 AI 상담 창구 경쟁에 나서고 있다는 기사입니다. AI가 검색과 챗봇을 넘어 실제 고객 응대와 업무 프로세스 전면으로 확장되고 있음을 보여줍니다.','impact':'금융권에서는 편의성뿐 아니라 오답 책임, 민원 대응, 고령층 접근성 같은 운영 기준이 함께 중요해질 수 있습니다.'},
    {'cat':'스타트업 자금조달','title':'AI OS 개발사 원더풀, 50억 달러 가치로 5.5억 달러 유치 - Investing.com 한국어','source':'Investing.com 한국어','time':'09-03 00:40 KST 전후','link':'https://news.google.com/rss/articles/CBMid0FVX3lxTE5DazNKbFdFQzltYVlOVmM2S0M2MVVpeVAwWXF1eFUxTmt1TFZKT19MY1RqSGVTaEhDdHRJMlVVS3JzRHBBcUU1ZmtmZDZ6Q0o1Q1NaeDBxeXJ2aU1IbEhLbmNCWnpJX0VVS1RMaWUyZkFyQmVvbm1B?oc=5','summary':'AI 운영체제 성격의 기업이 대규모 자금을 유치했다는 기사입니다. 투자시장이 단순 모델 시연보다 기업 업무를 감싸는 플랫폼형 AI에 더 큰 가치를 부여하고 있음을 보여줍니다.','impact':'국내에서도 범용 챗봇보다 워크플로우형 AI와 기업용 운영 레이어에 대한 관심이 커질 수 있지만, 수익화 검증 요구도 함께 커질 수 있습니다.'},
    {'cat':'인재·교육','title':'AI시대 청년인재 키운다…관악구 \'생성형 AI 마스터 클래스\' - 연합뉴스','source':'연합뉴스','time':'09-02 13:21 KST','link':'https://news.google.com/rss/articles/CBMiYEFVX3lxTE41ODQ5bkI4b1F4NV9QQlkwbndmQWgzT0NGblpwdDNDRFRQSVpORXZwTEN2V0RpSUVDdm1VbVhYckdQSW9ydW42eXA2eXNLMU5TdXlKSHB5UlNlV1lqVjkwatIBYEFVX3lxTE41ODQ5bkI4b1F4NV9QQlkwbndmQWgzT0NGblpwdDNDRFRQSVpORXZwTEN2V0RpSUVDdm1VbVhYckdQSW9ydW42eXA2eXNLMU5TdXlKSHB5UlNlV1lqVjkwag?oc=5','summary':'지자체가 청년 대상 생성형 AI 실전 교육을 여는 흐름을 다룬 기사입니다. AI 경쟁이 기업 간 기술 싸움만이 아니라 지역 인재 확보와 교육 인프라 경쟁으로 넓어지고 있음을 보여줍니다.','impact':'지방정부와 대학, 기업 협력 프로그램이 늘어날 수 있고, 산업 현장에서는 실무형 AI 인력 수요가 더 커질 가능성이 있습니다.'},
]

summary_bullets_world = [
    '오늘 세계뉴스는 미국의 반도체 표적관세 예고, 연준 베이지북의 물가 부담 진단, 원화 강세와 세수 부담, 뉴욕장 달러-원 흐름처럼 통상·물가·환율 이슈가 한데 묶였습니다.',
    '반도체 표적관세 뉴스는 미중 경쟁이 다시 관세와 현지 생산 압박의 언어로 돌아오고 있음을 보여줍니다.',
    '연준 베이지북은 이란 전쟁과 관세가 결국 미국 소비자 물가 부담으로 번지고 있다는 점을 상기시킵니다.',
    '환율 관련 기사들은 강달러 일변도에서 벗어난 국면이 각국 예산과 수출기업 계산법을 다시 바꾸고 있음을 시사합니다.',
    '오늘 국제면은 투자 베팅보다 관세·환율·물가가 생활비와 정책 계산서에 어떤 배경선을 만드는지 읽는 브리핑으로 보는 편이 적절합니다.'
]
world_news = [
    {'cat':'통상·반도체','title':'美상무장관, \'반도체 표적관세\' 예고…"美서 안만들면 대가" - 연합뉴스','source':'연합뉴스','time':'09-03 00:20 KST 전후','link':'https://news.google.com/rss/articles/CBMiW0FVX3lxTE9fc0JILU9UaVh2Sm42ckQ2SVFaRmdTeTNkMy1lS0hYTklhZEQwakw3ME5PZUdpRVk5OEJXSy0wdjUzMDNkcHFhamZPbTVuMjdWR0lMSm9tQndrXzTSAWBBVV95cUxQRHhkXzlzbEVtaDBQYjkxcXduaXdMeUVfZERwQ05Db2RxUE1jeEZKbWszekRuVlBSVk5ySGozZ0JWSGNBOEhuemkydmhIN01YVkZKRko1Ym1KT0c2N0RQTUk?oc=5','summary':'미국 상무장관이 미국 내 생산이 없는 반도체에 표적관세를 예고한 기사입니다. 반도체 경쟁이 기술 우위뿐 아니라 생산지와 공급망 재배치 압박으로 다시 번지고 있음을 보여줍니다.','impact':'한국 기업들도 현지 투자와 공급망 다변화 계산을 더 자주 점검해야 할 수 있고, 동맹국 산업정책 공조 논의도 거세질 가능성이 있습니다.'},
    {'cat':'물가·전쟁','title':'연준 베이지북 "이란 전쟁·관세 발 물가 인상에 미국 소비자들 부담 느껴" - YTN','source':'YTN','time':'09-03 06:09 KST 전후','link':'https://news.google.com/rss/articles/CBMiXkFVX3lxTE9kZXYyRGVQdUxIb1R0Q2dvNW8zbEpyc0VvSDg3aC03SW4zczdaRS1ZRXhyS3g4cnBrTTl6Mm5fQjlHWmNXUm93WGZRQ2xUY05aRlJTckZaR3ZhY0xlVXc?oc=5','summary':'연준 베이지북이 이란 전쟁과 관세발 물가 인상 때문에 미국 소비자 부담이 커지고 있다고 진단한 기사입니다. 지정학과 통상 이슈가 결국 일상 물가와 소비심리 문제로 번지고 있음을 보여줍니다.','impact':'금리 경로 해석이 더 복잡해질 수 있고, 전쟁과 관세 뉴스가 단순 외교면을 넘어 생활비 이슈로 자주 연결될 가능성이 있습니다.'},
    {'cat':'환율·재정','title':'예산에 1490원 환율 적용…원화강세에 세수 비상 - 마켓인','source':'마켓인','time':'09-03 05:00 KST 전후','link':'https://news.google.com/rss/articles/CBMic0FVX3lxTE52cnBCOHF5Y2xmYXpnRTRNTW00VzNnVzJjazF2djdDZXlaV3VfeXY3bVB4cjZzcUgwQWJlNi1lSllCUnpoNndVZXR6VTJvbmtXQmhrTGh1UDBZS0VnNFlvVU1tdFluY1QxWHhQT3hjT0dKOGs?oc=5','summary':'예산 편성의 환율 가정과 실제 원화 강세 사이의 차이를 짚은 기사입니다. 환율이 기업 실적뿐 아니라 세수와 재정 추계에도 직접 영향을 주는 변수임을 보여줍니다.','impact':'정부의 세수 보정과 재정 운용 논의가 더 자주 나올 수 있고, 수출기업들도 환율 민감도 관리가 한층 중요해질 수 있습니다.'},
    {'cat':'외환시장','title':'‘강엔’반전에 원달러 환율 1350원대로…2년만 최저 - v.daum.net','source':'v.daum.net','time':'09-03 05:02 KST 전후','link':'https://news.google.com/rss/articles/CBMiT0FVX3lxTE1tM1FwRFl4VG9MalZqa1J5UC0wWFlic0RmSTVCM2ExLVFXbHpXcnk2U2F3ekwyTzhxVE1kOEZlTTltMHZrNjk0Z0VsX3NrdGs?oc=5','summary':'엔화 반전과 함께 원달러 환율이 1350원대로 내려왔다는 기사입니다. 환율 방향이 수입물가에는 부담 완화 요인이지만 수출기업 계산에는 새로운 변수로 작동하고 있음을 보여줍니다.','impact':'수입업계와 여행·유통에는 숨통이 트일 수 있지만, 수출단가와 세수 가정에는 조정 압력이 커질 수 있습니다.'},
    {'cat':'뉴욕장 환율','title':'달러-원, 뉴욕장서 1,360원 초반대 거래 - 연합인포맥스','source':'연합인포맥스','time':'09-02 22:36 KST','link':'https://news.google.com/rss/articles/CBMicEFVX3lxTE9YdGZPTUt0TFRpYWNKQTlIeTZfY091RkpIZmd4b05OaGlqODZsU2RyMWRvYTBHTXczWkJLb3Blc2trRUdYeWFUdVQzWjhNalhDTmZ4ZTFJeEt4akpybDFJYUY4NjkxN3lOVjMzR3V5OW0?oc=5','summary':'뉴욕장에서 달러-원이 1360원 초반대에 거래됐다는 기사입니다. 장중 원화 흐름이 국내 현물장만이 아니라 글로벌 야간 흐름과도 더 밀접하게 연결되고 있음을 보여줍니다.','impact':'수출입 기업과 외환 당국, 투자자 모두 야간 변동성 관리가 더 중요해질 수 있고, 장전 환율 해석이 더 민감해질 가능성이 있습니다.'},
]

summary_bullets_domestic = [
    '오늘 국내면은 추석 물가 대책, 예산안 국회 제출, 국회 개회 메시지, 지역 현안 건의, 비 소식처럼 정책·정치·생활 뉴스가 함께 섞여 있습니다.',
    '정부의 추석 민생안정대책은 물가와 체감 생활비 관리가 여전히 국정의 맨 앞 과제임을 보여줍니다.',
    '예산안과 정기국회 관련 기사는 앞으로 몇 주간 정치 뉴스의 무게중심이 예산 심사와 입법 우선순위로 이동할 수 있음을 시사합니다.',
    '지역 현안과 지방의회법 이슈는 중앙정치 외에도 지역 행정과 제도 개선 뉴스가 꾸준히 쌓이고 있음을 보여줍니다.',
    '오늘 국내면은 종목 재료보다 물가, 예산, 입법, 지역 생활 현안을 아침에 빠르게 훑는 쪽에 무게를 둡니다.'
]
domestic_news = [
    {'cat':'정부·민생물가','title':'정부 "물가 압력 최소화"…추석 민생안정대책 신속 추진 - korea.kr','source':'korea.kr','time':'09-03 04:06 KST 전후','link':'https://news.google.com/rss/articles/CBMibEFVX3lxTE1LWlV1aFpYTG9iOUxxcTNOTklUSWdNRGxXZVRPZUFuVTBlZjdaaEh2RjBpem5DNkdkYkFVUUY5UldOUHd6LXNLUjliRFhpQlRDb2lNUThMYW8wMXNjTERrQ05EM1ctbm9PRUh3Wg?oc=5','summary':'정부가 추석을 앞두고 물가 압력을 최소화하기 위한 민생안정대책을 서두르겠다는 기사입니다. 체감 물가와 장바구니 부담이 여전히 정책 우선순위의 맨 앞에 놓여 있음을 보여줍니다.','impact':'농축산물과 생활필수품, 교통 수요 관련 대책이 이어질 수 있고, 명절 체감경기와 여론에도 영향을 줄 가능성이 있습니다.'},
    {'cat':'예산·국회','title':'정부 예산안 3일 국회로…강원도·정치권 ‘국회 증액’ 원팀 시동 - v.daum.net','source':'v.daum.net','time':'09-03 00:09 KST 전후','link':'https://news.google.com/rss/articles/CBMiT0FVX3lxTFBlMk5zLVA3bkZsMmVOdUUyNC1ZemVfZHJJLUVsd25LcWhScjdJcmtGSUdORjlmd1plUENKcURLRkxFcE9PWU1mSjlUVVhLMXM?oc=5','summary':'정부 예산안이 국회로 넘어가고 지역과 정치권이 증액 논의에 들어간다는 기사입니다. 예산 시즌이 시작되며 중앙정부와 지역 이해관계가 본격적으로 맞붙는 국면을 보여줍니다.','impact':'SOC·지역사업·복지 예산을 둘러싼 국회 공방이 커질 수 있고, 각 부처의 정책 우선순위 조정도 이어질 가능성이 있습니다.'},
    {'cat':'국회·입법','title':'조정식 의장 “시대에 부응하는 입법으로 국민 삶 개선” [정기국회 개회] - 헤럴드경제','source':'헤럴드경제','time':'09-01 15:11 KST 전후','link':'https://news.google.com/rss/articles/CBMiV0FVX3lxTFB4eHNaYnMxd09SZjJmZnJNZ2d2a1NBNi1yN1R4RmU3VnBueHNiRllhekpQWldpeGZzeTlzTHROdjNPRWtXTlhTRW9GRDdCd2UwTVJwUTg3NA?oc=5','summary':'정기국회 개회와 함께 시대 변화에 맞는 입법으로 국민 삶을 개선하겠다는 메시지를 다룬 기사입니다. 가을 국회가 예산뿐 아니라 민생 법안 처리 속도와 우선순위를 두고 평가받는 기간이 될 수 있음을 보여줍니다.','impact':'여야가 생활 법안과 쟁점 법안을 어떻게 배치하는지가 여론 흐름과 국정 동력에 영향을 줄 가능성이 있습니다.'},
    {'cat':'지역 정책·균형발전','title':'증평군 "성장 가능 콤팩트 도시 지원해야" 정부에 제안 - 연합뉴스','source':'연합뉴스','time':'09-02 15:30 KST 전후','link':'https://news.google.com/rss/articles/CBMiYEFVX3lxTFBGT1BzcE50N1Q5SGg3OFhuY3piM2tvdkkwLUozNThpNmViV0ZROExQMWp3NWFDNW9LSHp2V0FOWGlfckJUN1VXUXB6Y0F6ZzJVd3dWWDlhX0hEUkhsMHpPeNIBYEFVX3lxTFBGT1BzcE50N1Q5SGg3OFhuY3piM2tvdkkwLUozNThpNmViV0ZROExQMWp3NWFDNW9LSHp2V0FOWGlfckJUN1VXUXB6Y0F6ZzJVd3dWWDlhX0hEUkhsMHpPeA?oc=5','summary':'증평군이 성장 가능성이 높은 콤팩트 도시에 대한 지원을 정부에 제안했다는 기사입니다. 지역소멸과 균형발전 논의가 추상적 구호를 넘어 생활권 단위의 행정 전략으로 구체화되고 있음을 보여줍니다.','impact':'지방소멸 대응 예산과 생활 인프라 배분 논의가 이어질 수 있고, 다른 지자체의 유사 요구도 늘어날 가능성이 있습니다.'},
    {'cat':'날씨·생활','title':'[날씨] 전국 비‥충청·전북 이틀간 최대 200mm - MBC 뉴스','source':'MBC 뉴스','time':'09-03 00:03 KST 전후','link':'https://news.google.com/rss/articles/CBMid0FVX3lxTE0xSnRyN3JZbnhNYVhHMHQzQ2JYYkY4V2VNSkxES3pzY1czUHRyQjN6WDZSMWQ3V0NXNHdOam1QS3prWGh4eWl6T2hQYTA1dUtRMWg2YXJ1SWtmYThld3VhZlhLSm9VZDVNNjItWnhlUVhLbzB1aWpz0gF3QVVfeXFMT2s5SGJPdWNXcFI1bGpVWVV4X2lRSFNJZ19pc0Z0X3o0SU1IODU0emwxU3ppd0FEaHU0SDVnM1ZiNXNMUmNZT1o3bnV4WFo2b3R2eWxmQ3pscVFtckxrWUNQRzM2OW9MUlFlTmFYVmF4QnhZNjByN1E?oc=5','summary':'전국에 비가 내리고 충청과 전북에 많은 비가 예보됐다는 기사입니다. 출근길 교통과 지역 안전, 시설 점검, 야외 일정 조정이 함께 필요한 날씨 상황입니다.','impact':'지자체 재난 공지와 침수 대비가 늘어날 수 있고, 물류와 통학·출근 동선에도 단기 영향이 생길 가능성이 있습니다.'},
]

review_html=''.join(f"<tr><td>{esc(r['name'])}<br><span class=\"caption\">{esc(r['code'])}.KS</span></td><td>{esc(r['d0'])} {esc(r['p0'])}원 → {esc(r['d1'])} {esc(r['p1'])}원</td><td>{esc(r['d1'])} 정규장</td><td><b>{r['pct']:+.2f}%</b></td><td><a href=\"https://finance.naver.com/item/sise_day.naver?code={esc(r['code'])}\" target=\"_blank\">출처보기</a></td></tr>" for r in review_rows)
idea_html=''.join(f"<div class=\"idea-card\"><span class=\"pill\">관찰 아이디어</span><h3>{esc(x['name'])} <em>{esc(x['code'])}</em></h3><p><b>관련 테마</b> {esc(x['theme'])}</p><p><b>연결 이유</b> {esc(x['reason'])}</p><p><b>단기 확인 포인트</b> {esc(x['point'])}</p></div>" for x in idea_cards)
css = ROOT.joinpath('daily-briefing-20260706.html').read_text(encoding='utf-8').split('<style>',1)[1].split('</style>',1)[0]

world_scenes = [
    ('반도체 표적관세','생산지를 둘러싼 압박이 다시 커진다.','tariff-chip'),
    ('연준 베이지북','전쟁과 관세가 결국 물가로 번진다.','price-tag'),
    ('예산 환율 계산','환율 변화가 세수와 재정 계산서를 흔든다.','fx-budget'),
    ('원화 강세 반전','환율 방향이 수입과 수출의 셈법을 바꾼다.','shopping'),
    ('뉴욕장 달러-원','야간 외환 흐름이 장전 해석의 일부가 된다.','fx-budget'),
    ('반도체 공급망','관세 뉴스가 동맹 산업정책을 압박한다.','tariff-chip'),
    ('생활 물가 부담','국제 뉴스가 장바구니 가격으로 이어진다.','price-tag'),
    ('통상·환율 복합리스크','관세·물가·환율이 한 화면에 겹친다.','shopping'),
]
domestic_scenes = [
    ('추석 물가 대책','명절 물가와 생활비 관리가 우선 과제다.','policy'),
    ('예산안 국회 제출','지역과 중앙이 예산 줄다리기에 들어간다.','assembly'),
    ('정기국회 개회','입법 성과가 곧 민생 평가로 연결된다.','assembly'),
    ('콤팩트 도시 제안','지역 생존 전략이 생활권 단위로 세분화된다.','local-city'),
    ('전국 비','출근길과 지역 안전 공지가 중요하다.','rain'),
    ('지역 행정 요구','지방 의제도 중앙정책의 일부가 된다.','local-city'),
    ('물가 점검','장바구니 부담을 낮추라는 신호가 이어진다.','policy'),
    ('생활형 국정 과제','예산·입법·날씨를 함께 챙겨야 하는 아침이다.','rain'),
]

draw_paper('세계 뉴스 8컷 만평', world_scenes, WORLD_IMG)
draw_paper('국내 뉴스 8컷 만평', domestic_scenes, DOMESTIC_IMG)

html_doc = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>아침 통합 보고서 — {KOR_DATE}</title><meta name="x-marker" content="{MARKER}"><style>{css}</style></head><body><main class="page"><header class="hero"><div class="hero-top"><div><div class="kicker">대표님용 고정 구성 리포트</div><h1>아침 통합 보고서</h1><p class="lead">{KOR_DATE} · 미국증시·AI·세계뉴스·국내뉴스를 2026-07-06 승인본 구조 그대로 유지해 정리했습니다. 오늘도 투자 추천이 아니라 간추린 아침뉴스와 시장 참고 메모 성격을 유지하고, 정책·사회·국제·생활 뉴스를 먼저 읽을 수 있게 배치했습니다.</p></div><div class="stamp"><b>{MARKER}</b><br>작성 {now.strftime('%Y-%m-%d %H:%M:%S KST')}<br>승인 스타일 유지</div></div><nav class="nav"><a href="#market">미국증시 보고</a><a href="#ai">AI·스타트업 보고</a><a href="#world">세계뉴스 보고</a><a href="#domestic">국내뉴스 보고</a></nav></header>
<section class="section" id="market"><div class="section-title"><h2>미국증시 보고</h2><span class="caption">직전 미국 정규장 마감 · Yahoo Finance chart API</span></div><div class="note">직전 미국 정규장은 S&amp;P500 {market['S&P 500']['pct']:+.2f}%, 나스닥 {market['나스닥']['pct']:+.2f}%, 다우 {market['다우']['pct']:+.2f}%였습니다. SOXX는 {market['SOXX']['pct']:+.2f}%였고 달러/원은 {market['달러/원']['price']:.2f}, WTI는 {market['WTI']['price']:.2f}입니다. 오늘 한국장은 미국 반도체 생산 압박 기사, 원화 강세와 환율 재계산, AI 인프라 뉴스의 번짐 강도를 참고 메모 수준으로 보는 편이 적절합니다.</div><div class="summary-grid">{metric_line('S&P 500',market['S&P 500'])}{metric_line('나스닥',market['나스닥'])}{metric_line('다우',market['다우'])}{metric_line('러셀2000',market['러셀2000'])}</div></section>
<section class="section"><div class="section-title"><h2>핵심 요약</h2><span class="caption">목요일 아침 브리핑</span></div><div class="summary-grid"><div class="metric"><b>① 미국장</b><span>기술주와 반도체 강세가 이어졌지만 관세와 환율 뉴스가 함께 따라붙는 구간입니다.</span></div><div class="metric"><b>② 국제면</b><span>반도체 표적관세, 연준 물가 진단, 원화 강세와 예산 환율 계산이 겹쳤습니다.</span></div><div class="metric"><b>③ 국내면</b><span>추석 물가 대책, 예산안 국회 제출, 정기국회 개회, 지역 현안, 비 소식이 오늘의 생활·정책 배경선입니다.</span></div><div class="metric"><b>④ AI면</b><span>운영 책임, 의료 데이터, 금융 AI 창구, 대형 자금조달, 지역 인재 양성이 전면에 섰습니다.</span></div></div></section>
<section class="section" id="review"><div class="section-title"><h2>📈 어제 연결 아이디어</h2><span class="caption">최근 완료 정규장 {review_rows[0]['d1']} 복기</span></div><table><thead><tr><th>종목</th><th>종가 비교</th><th>기준 거래일</th><th>등락률</th><th>출처</th></tr></thead><tbody>{review_html}</tbody></table></section>
<section class="section"><div class="two"><div class="panel"><h2>주요 지수/섹터</h2><ul><li><b>지수:</b> 미국장은 S&amp;P500 {market['S&P 500']['pct']:+.2f}%, 나스닥 {market['나스닥']['pct']:+.2f}%였고 SOXX는 {market['SOXX']['pct']:+.2f}%였습니다.</li><li><b>원자재·환율:</b> WTI {market['WTI']['price']:.2f}, 달러/원 {market['달러/원']['price']:.2f}는 장전 해석의 보조선입니다.</li><li><b>변동성:</b> VIX {market['VIX']['price']:.2f}로 공포 급등 구간은 아니지만 관세·환율 뉴스가 체감 변동성을 키울 수 있습니다.</li></ul></div><div class="panel"><h2>급등·급락 메모</h2><ul><li><b>반도체:</b> SOXX 강세가 있어도 미국 생산 압박과 관세 뉴스가 붙어 있어 과열 해석보다는 기준선 확인이 우선입니다.</li><li><b>환율:</b> 원화 강세 기사는 수입물가에는 숨통을 주지만 수출주 해석은 더 복잡하게 만들 수 있습니다.</li><li><b>톤 조절:</b> 본 보고서는 추천이 아니라 아침 뉴스와 시장 반응 가능성을 정리한 참고 메모입니다.</li></ul></div></div></section>
<section class="section"><div class="section-title"><h2>한국 증시 영향</h2><span class="caption">목요일 장전 체크 포인트 메모</span></div><div class="checklist"><div class="check"><b>반도체</b> 미국 반도체 표적관세 예고가 직접 악재인지, 현지 생산 확대 압박으로 읽히는지 장 초반 해석을 나눠 볼 필요가 있습니다.</div><div class="check"><b>전력 인프라</b> AI 인프라 뉴스는 여전히 전선·변압기·전력설비 종목군으로 먼저 번질 가능성이 있습니다.</div><div class="check"><b>환율</b> 원화 강세와 야간 달러-원 흐름이 수출주·수입주 체감 온도를 어떻게 바꾸는지 확인이 필요합니다.</div><div class="check"><b>정책·민생</b> 추석 물가 대책과 예산안 국회 제출은 시장 재료보다 생활·정책 일정의 배경 뉴스로 읽는 편이 적절합니다.</div></div></section>
<section class="section" id="ideas"><div class="section-title"><h2>🔗 오늘 연결 아이디어 3건</h2><span class="caption">투자권유 아님 · 후보군 {esc(', '.join(candidate_pool))} 중 직결성·뉴스 민감도 기준 압축</span></div><div class="idea-grid">{idea_html}</div></section>
<section class="section" id="todo"><div class="section-title"><h2>오늘 체크 이벤트</h2><span class="caption">목요일 정리용 메모</span></div><div class="checklist"><div class="check"><b>해외</b> 미국 반도체 관세 후속 발언, 연준 물가 해석, 뉴욕장 환율 흐름 확인</div><div class="check"><b>국내 정책</b> 추석 물가 대책 세부안, 예산안 국회 반응, 정기국회 쟁점 확인</div><div class="check"><b>생활</b> 충청·전북 강수, 지역별 침수·교통 공지, 출근길 안전 정보 확인</div><div class="check"><b>시장</b> 장 초반 전선·전력주와 메모리 대표주의 반응을 분리해서 확인</div></div></section>
<section class="section"><div class="section-title"><h2>출처</h2><span class="caption">시장·뉴스 검증 경로</span></div><div class="panel"><ul><li><b>시장 데이터:</b> Yahoo Finance chart API</li><li><b>한국 종목 전일 종가:</b> 네이버페이 증권 일별시세</li><li><b>뉴스 링크:</b> Google 뉴스 RSS 기사 링크</li></ul></div></section>
<section class="section dark" id="ai"><div class="section-title"><h2>🤖 AI·스타트업 보고</h2><span class="caption">간추린 아침뉴스 5줄</span></div><div class="panel"><ul>{''.join(f'<li>{esc(x)}</li>' for x in summary_bullets_ai)}</ul></div></section><section class="section"><div class="section-title"><h2>AI 관련 소식 5개</h2><span class="caption">내용요약 → 예상여파 → 기사/영상</span></div><div class="news-list">{''.join(card_html(i+1,n) for i,n in enumerate(ai_news))}</div></section>
<section class="section dark" id="world"><div class="section-title"><h2>🌍 세계뉴스 보고</h2><span class="caption">간추린 아침뉴스 5줄</span></div><div class="panel"><ul>{''.join(f'<li>{esc(x)}</li>' for x in summary_bullets_world)}</ul></div></section><section class="section"><div class="section-title"><h2>세계 주요 뉴스 5개</h2><span class="caption">내용요약 → 예상여파 → 기사/영상</span></div><div class="news-list">{''.join(card_html(i+1,n) for i,n in enumerate(world_news))}</div></section>
<section class="section cartoon-section" id="worldtoon"><div class="section-title"><h2>🌍 세계 뉴스 8컷 만평</h2><span class="caption">실제 웹툰/신문만화풍 PNG · 장면 반복 최소화</span></div><div class="webtoon-art-wrap"><img class="webtoon-art" src="assets/world-webtoon-{YMD}.png?v={YMD}a" alt="세계 뉴스 이슈를 2×4 웹툰 만평으로 표현한 이미지"><p class="webtoon-note"><strong>구성:</strong> 반도체 관세, 연준 물가 진단, 환율·세수 계산, 야간 달러-원 흐름 등을 서로 다른 장면으로 표현한 PNG입니다.</p></div></section>
<section class="section dark" id="domestic"><div class="section-title"><h2>🇰🇷 국내뉴스 보고</h2><span class="caption">간추린 아침뉴스 5줄</span></div><div class="panel"><ul>{''.join(f'<li>{esc(x)}</li>' for x in summary_bullets_domestic)}</ul></div></section><section class="section"><div class="section-title"><h2>국내 주요 뉴스 5개</h2><span class="caption">내용요약 → 예상여파 → 기사/영상</span></div><div class="news-list">{''.join(card_html(i+1,n) for i,n in enumerate(domestic_news))}</div></section>
<section class="section cartoon-section" id="domestictoon"><div class="section-title"><h2>🇰🇷 국내 뉴스 8컷 만평</h2><span class="caption">실제 웹툰/신문만화풍 PNG · 장면 반복 최소화</span></div><div class="webtoon-art-wrap"><img class="webtoon-art" src="assets/domestic-webtoon-{YMD}.png?v={YMD}a" alt="국내 뉴스와 생활 이슈를 2×4 웹툰 만평으로 표현한 이미지"><p class="webtoon-note"><strong>구성:</strong> 추석 물가 대책, 예산안 국회 제출, 정기국회, 지역 현안, 많은 비 등을 서로 다른 장면으로 표현한 PNG입니다.</p></div></section>
<footer>{MARKER} · 출처: Google 뉴스 RSS 기사 링크, Yahoo Finance chart API, 네이버페이 증권 일별시세. 본 보고서는 정보 제공용이며 투자 권유가 아닙니다.</footer></main></body></html>'''
HTML_PATH.write_text(html_doc, encoding='utf-8')
print(HTML_PATH)
print(WORLD_IMG)
print(DOMESTIC_IMG)
