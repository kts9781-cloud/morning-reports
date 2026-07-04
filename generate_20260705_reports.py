#!/usr/bin/env python3
import html, json, os, re, shutil, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

now=datetime.now(ZoneInfo('Asia/Seoul'))
DATE=now.strftime('%Y%m%d')
DATE_DASH=now.strftime('%Y-%m-%d')
BASE='https://kts9781-cloud.github.io/morning-reports'
ROOT=os.path.dirname(os.path.abspath(__file__))
WORLD_SRC='/Users/taesungkim/.hermes/profiles/bis/cache/images/openai_codex_gpt-image-2-medium_20260705_063309_ed439e3a.png'
KOREA_SRC='/Users/taesungkim/.hermes/profiles/bis/cache/images/openai_codex_gpt-image-2-medium_20260705_063506_5db69b13.png'
UA={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 morning-report-bot'}

def fetch(url, timeout=25):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_json(url):
    return json.loads(fetch(url).decode('utf-8'))

def esc(s):
    return html.escape(str(s), quote=True)

def yahoo(symbol):
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol, safe='')+'?range=5d&interval=1d'
    j=fetch_json(url)
    res=j['chart']['result'][0]
    q=res['indicators']['quote'][0]
    closes=[x for x in q.get('close', []) if x is not None]
    price=float(res['meta'].get('regularMarketPrice') or closes[-1])
    prev=float(closes[-2] if len(closes)>1 else price)
    ch=price-prev
    pct=(ch/prev*100) if prev else 0.0
    return price, ch, pct

def rss(url, limit=10):
    data=fetch(url)
    root=ET.fromstring(data)
    items=[]; seen=set()
    for it in root.findall('./channel/item'):
        title=(it.findtext('title') or '').strip()
        link=(it.findtext('link') or '').strip()
        pub=(it.findtext('pubDate') or '').strip()
        clean=re.sub(r'\s+-\s+[^-]{2,45}$', '', title).strip()
        if not clean: continue
        key=re.sub(r'\W+', '', clean.lower())[:45]
        if key in seen: continue
        seen.add(key)
        items.append({'title':clean, 'link':link, 'pub':pub})
        if len(items)>=limit: break
    return items

def pick_queries(queries, fallback_url):
    out=[]; seen=set()
    for q in queries:
        url='https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=ko&gl=KR&ceid=KR:ko'
        try:
            cands=rss(url, 8)
        except Exception:
            cands=[]
        for item in cands:
            key=re.sub(r'\W+', '', item['title'].lower())[:45]
            if key not in seen:
                seen.add(key); out.append(item); break
    if len(out)<5:
        try:
            for item in rss(fallback_url, 20):
                key=re.sub(r'\W+', '', item['title'].lower())[:45]
                if key not in seen:
                    seen.add(key); out.append(item)
                if len(out)>=5: break
        except Exception:
            pass
    return out[:5]

def yt_url(title):
    return 'https://www.youtube.com/results?search_query='+urllib.parse.quote(title)

def make_summary(title, scope):
    if any(k in title for k in ['증시','시장','금리','환율','유가','물가','채권']):
        return f'{scope}에서 금융시장과 거시 변수에 직접 연결되는 소식입니다. 원문에서 수치와 발언 맥락을 함께 확인할 필요가 있습니다.'
    if any(k in title for k in ['AI','반도체','수출','무역','관세','기업','배터리']):
        return f'{scope}의 산업·공급망 이슈입니다. 관련 업종의 투자심리와 정책 대응이 같이 움직일 수 있습니다.'
    if any(k in title for k in ['전쟁','중동','우크라','안보','외교','협상']):
        return f'{scope}의 외교·안보 변수입니다. 에너지·방산·해운 등 민감 업종으로 파급될 가능성이 있습니다.'
    return f'{scope} 주요 매체가 전한 핵심 이슈입니다. 정책·생활·경제 심리에 이어질 수 있어 후속 보도를 확인해야 합니다.'

def make_impact(title, scope):
    if any(k in title for k in ['금리','물가','환율','달러','유가','증시','시장']):
        return '금리·환율·위험선호에 반영되며 주식·채권·원자재 변동성을 키울 수 있습니다.'
    if any(k in title for k in ['반도체','AI','수출','무역','관세','기업','배터리']):
        return '수출주·기술주·공급망 관련 업종의 실적 기대와 밸류에이션에 영향을 줄 수 있습니다.'
    if any(k in title for k in ['폭염','장마','날씨','재난','의료','교육']):
        return '소비·물류·공공서비스 운영에 단기 부담이 커질 수 있어 생활물가와 대응책을 점검해야 합니다.'
    return f'{scope} 정책 대응과 소비·투자심리에 후행 영향이 나타날 수 있어 추가 확인이 필요합니다.'

# Required cartoon files
shutil.copyfile(WORLD_SRC, os.path.join(ROOT, f'world-cartoon-{DATE}.png'))
shutil.copyfile(KOREA_SRC, os.path.join(ROOT, f'korea-cartoon-{DATE}.png'))

markets={'S&P 500':'^GSPC','나스닥':'^IXIC','다우':'^DJI','러셀2000':'^RUT','반도체 ETF(SOXX)':'SOXX','달러/원':'KRW=X','WTI':'CL=F','금':'GC=F','VIX':'^VIX'}
market_rows=[]
for name,sym in markets.items():
    try:
        p,ch,pct=yahoo(sym)
        market_rows.append((name,p,ch,pct))
    except Exception as e:
        market_rows.append((name,'수집 실패',0,0))

world=pick_queries([
    '미국 증시 OR 뉴욕증시 when:2d','국제 유가 중동 미국 when:2d','중국 경제 무역 when:2d','유럽 경제 금리 when:2d','AI 규제 기술 국제 when:7d'
], 'https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko')
korea=pick_queries([
    '한국 경제 정책 when:2d','정부 정책 한국 when:2d','국회 입법 한국 when:2d','반도체 수출 한국 when:7d','폭염 장마 날씨 한국 when:2d'
], 'https://news.google.com/rss/search?q=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD%20when%3A2d&hl=ko&gl=KR&ceid=KR:ko')
if len(world)<5 or len(korea)<5:
    raise SystemExit(f'news collection failed world={len(world)} korea={len(korea)}')

style='''
:root{--bg:#f5f7fb;--card:#fff;--ink:#172033;--muted:#64708a;--line:#dfe6f2;--blue:#2563eb;--green:#078554;--red:#d92d20;--ytbg:#fff1f2;--yt:#be123c;--shadow:0 10px 28px rgba(20,32,55,.08)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR","Apple SD Gothic Neo",Arial,sans-serif;line-height:1.6}.wrap{max-width:1060px;margin:0 auto;padding:24px 14px 64px}.hero{background:linear-gradient(135deg,#1d4ed8,#0f172a);color:#fff;border-radius:28px;padding:30px 24px;margin-bottom:28px;box-shadow:0 14px 40px rgba(15,23,42,.18)}.hero h1{margin:6px 0 8px;font-size:34px}.hero p{margin:0;color:#dbeafe}.eyebrow{font-size:13px;letter-spacing:.08em;font-weight:800;opacity:.82}.block{margin:30px 0 46px}.label-title{font-size:29px;margin:0 0 16px}.panel,.summary,.cartoon{background:#fff;border:1px solid var(--line);border-radius:22px;padding:18px;box-shadow:var(--shadow)}.summary{border-left:5px solid var(--blue)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.metric,.idea{background:#fff;border:1px solid var(--line);border-radius:18px;padding:15px;box-shadow:var(--shadow);margin:12px 0}.metric b{font-size:20px}.up{color:var(--green)}.down{color:var(--red)}.news-list{display:flex;flex-direction:column;gap:14px;margin-top:16px}.news-card{display:grid;grid-template-columns:58px minmax(0,1fr) 172px;gap:16px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:20px;padding:16px;box-shadow:var(--shadow)}.badge{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:#e8f0ff;color:#1d4ed8;font-weight:900;font-size:18px}.news-body h3{margin:0 0 8px;font-size:18px;line-height:1.35}.news-body p{margin:5px 0;color:#34405a}.tag{display:inline-block;font-weight:900;color:#1d4ed8;margin-right:5px}.actions{display:flex;flex-direction:column;gap:9px}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:40px;border-radius:999px;text-decoration:none;font-weight:900;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}.btn.yt{background:var(--ytbg);color:var(--yt);border-color:#fecdd3}.small{color:var(--muted);font-size:13px}.cartoon img{display:block;width:100%;max-width:760px;margin:16px auto 0;border-radius:24px;border:1px solid var(--line);box-shadow:0 14px 38px rgba(20,32,55,.16)}@media(max-width:760px){.news-card{grid-template-columns:1fr}.actions{flex-direction:row;flex-wrap:wrap}.hero h1{font-size:28px}}'''

metrics=''.join([f'<div class="metric"><div>{esc(n)}</div><b class="{"up" if isinstance(p,float) and pct>=0 else "down"}">{p:,.2f}</b><div class="small">{ch:+.2f} ({pct:+.2f}%)</div></div>' if isinstance(p,float) else f'<div class="metric"><div>{esc(n)}</div><b>{esc(p)}</b></div>' for n,p,ch,pct in market_rows])
ideas=[
('반도체·AI 밸류체인','나스닥·SOXX 흐름이 한국 반도체 대형주와 장비주의 장중 탄력 차이를 만들 수 있습니다.','미국 기술주 선별 장세, 원/달러 방향, 외국인 선물 수급'),
('환율 민감 내수·수입주','달러/원 하락은 항공·음식료·유통 등 비용 부담 완화 기대를 키우지만 수출 대형주는 환율 효과 둔화 우려가 생길 수 있습니다.','장 초반 환율, 외국인 현물 순매수, 유가'),
('에너지·방어주와 정책 테마','유가·금·VIX 조합에 따라 방산·전력·에너지 헤지 수요와 배당·방어주 선호가 교차할 수 있습니다.','미 국채금리, WTI, 국내 정책 뉴스')]
idea_html=''.join([f'<div class="idea"><h3>{i}. {esc(t)}</h3><p><span class="tag">연결고리</span>{esc(b)}</p><p><span class="tag">관찰 포인트</span>{esc(c)}</p></div>' for i,(t,b,c) in enumerate(ideas,1)])
market_html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{DATE_DASH} 미국증시 아이디어 보고서</title><style>{style}</style></head><body><main class="wrap"><section class="hero"><div class="eyebrow">MORNING MARKET BRIEFING · {DATE_DASH}</div><h1>미국증시 아이디어 보고서</h1><p>실시간 시장 지표와 한국장 연결 아이디어를 분리해 정리했습니다.</p></section><section class="block summary"><h2>미국증시 보고</h2><p>주요 미국 지수와 반도체·환율·원자재 흐름을 함께 보며 한국장 업종별 차별화에 대비합니다.</p></section><section class="block"><h2 class="label-title">주요 미국 지수/시장 흐름</h2><div class="grid">{metrics}</div><p class="small">자료: Yahoo Finance chart API, 생성 시점 KST {DATE_DASH} 아침.</p></section><section class="block"><h2 class="label-title">오늘 연결 아이디어 3건</h2>{idea_html}</section></main></body></html>'''

def card_html(items, start, scope):
    out=[]
    for offset,item in enumerate(items, start):
        out.append(f'''<article class="news-card"><div class="badge">{offset}</div><div class="news-body"><h3>{esc(item['title'])}</h3><p><span class="tag">내용요약</span>{esc(make_summary(item['title'], scope))}</p><p><span class="tag">예상여파</span>{esc(make_impact(item['title'], scope))}</p><p class="small">{esc(scope)} · Google News RSS · {esc(item.get('pub',''))}</p></div><div class="actions"><a class="btn" href="{esc(item['link'])}" target="_blank" rel="noopener">기사보기</a><a class="btn yt" href="{esc(yt_url(item['title']))}" target="_blank" rel="noopener">유튜브 영상 보기</a></div></article>''')
    return ''.join(out)

cache=f'{DATE}0630'
news_html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{DATE_DASH} 뉴스 보고서</title><style>{style}</style></head><body><main class="wrap"><section class="hero"><div class="eyebrow">MORNING NEWS BRIEFING · {DATE_DASH}</div><h1>뉴스 보고서</h1><p>세계뉴스 5건과 국내뉴스 5건, 기사 원문 및 유튜브 검색 링크를 카드형으로 정리했습니다.</p></section><section class="block"><h2 class="label-title">세계뉴스</h2><div class="news-list">{card_html(world,1,'세계뉴스')}</div></section><section class="block cartoon"><h2>세계뉴스 8컷 만평</h2><p class="small">실제 인물·정당명·기업로고·신문사명 복제 없이 상징으로 구성한 세로형 8컷 포스터입니다.</p><img src="{BASE}/world-cartoon-{DATE}.png?v={cache}" alt="세계뉴스 8컷 만평"></section><section class="block"><h2 class="label-title">국내뉴스</h2><div class="news-list">{card_html(korea,6,'국내뉴스')}</div></section><section class="block cartoon"><h2>국내뉴스 8컷 만평</h2><p class="small">실제 인물·정당명·기업로고·신문사명 복제 없이 상징으로 구성한 세로형 8컷 포스터입니다.</p><img src="{BASE}/korea-cartoon-{DATE}.png?v={cache}" alt="국내뉴스 8컷 만평"></section></main></body></html>'''

open(os.path.join(ROOT,f'daily-market-briefing-{DATE}.html'),'w',encoding='utf-8').write(market_html)
open(os.path.join(ROOT,f'daily-news-briefing-{DATE}.html'),'w',encoding='utf-8').write(news_html)
print('generated', f'daily-market-briefing-{DATE}.html', f'daily-news-briefing-{DATE}.html', len(world), len(korea))
print('world titles:', [x['title'] for x in world])
print('korea titles:', [x['title'] for x in korea])
