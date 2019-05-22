from requests import Request, Session
from lxml import html

BASE_HEADERS = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',
                 'Accept-Encoding' : 'gzip, deflate, br',
                 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Accept-Language': 'en-US,en;q=0.5',
                 'Referer': 'https://bus.sumy.ua/as.php?as=sum',
                 'Connection': 'keep-alive',
                 'Cookie': 's=1',
                 'Upgrade-Insecure-Requests': '1'}

def request_session_params(date, session):
    url = 'https://bus.sumy.ua/as.php?as=sum'

    req = Request('GET', url, headers=BASE_HEADERS.copy())
    prepped = req.prepare()

    response = session.send(prepped, verify=False)

    tree = html.fromstring(response.text)
    params = {}
    for input in tree.xpath("//form[@id='form1']/input"):
        attr_name = ''.join(input.xpath('./@name'))
        attr_value = ''.join(input.xpath('./@value'))
        params[attr_name] = attr_value

    bd_to = '1335'
    bd_to_st = 'Гадяч АС'

    params['to'] = bd_to
    params['to-st'] = bd_to_st
    params['when'] = date
    return params

def request_busses_html(params, session):
    url = 'https://bus.sumy.ua/reys.php'

    hdrs = BASE_HEADERS.copy()
    hdrs['Content-Type'] = 'application/x-www-form-urlencoded'

    bd = compose_params(params)

    req = Request('POST', url, headers=hdrs, data=bd.encode('utf-8'))
    prepped = req.prepare()

    response = session.send(prepped, verify=False)
    return response.text


def compose_params(p):
    return '&'.join(['='.join(i) for i in p.items()]).replace(' ', '+')

def get_busses(date = '23.05.2019'):
    session = Session()
    params = request_session_params(date, session)
    tree = html.fromstring(request_busses_html(params, session))

    busses = []

    for row in tree.xpath('//td/form'):
        info = {}
        info['number'] = row.xpath("./input[@name='number']/@value")[0].strip()
        info['fdepdest_short'] = row.xpath("./input[@name='fdepdest_short']/@value")[0].strip()
        t = row.xpath("./input[@name='from_departure_time']/@value")[0].strip()
        info['from_departure_time'] = ''.join((t[0].replace('0',''), t[1:]))
        info['to_arrival'] = row.xpath("./input[@name='to_arrival']/@value")[0].strip()
        info['tr'] = row.xpath("./input[@name='tr']/@value")[0].strip()
        info['tu_markl'] = row.xpath("./input[@name='tu_markl']/@value")[0].strip()
        info['seats_kol'] = row.xpath("./input[@name='seats_kol']/@value")[0].strip()
        info['price'] = row.xpath("./input[@name='price']/@value")[0].strip()
        busses.append(info)
    return busses
