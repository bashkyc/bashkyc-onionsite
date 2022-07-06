import json, hashlib

#requirements for an exchange to be listed
requirements = {
    "kyc-check": "==True", #"kyc-check = true" means the opposite of what you'd think
    "kyc-type": "<=2",
    "score": ">=6.5",
}

#list of manually removed exchanges
banned = [
    "BlockDX", #absurdly low (completely unusable) liquidity, and the spread is insane
    "Morphtoken", #"Service is not available" (?). Might be temporary or shut down permanently
]

#manual score changes
score_boost = {
    "LocalMonero": 1,
    "AgoraDesk": 1,
}

#list of currencies supported by each exchange
currencies = {
    "Bisq" : "BTC, XMR(i), ETH(i), LTC(i), +more",
    "RoboSats" : "BTC-LN",
    "LocalMonero" : "XMR, BTC(i), ETH(i), LTC(i), +more",
    "AgoraDesk" : "BTC, XMR, ETH(i), LTC(i), USDT(i), +more",
    "Majestic Bank" : "BTC, XMR, LTC",
    "Kilos Swap" : "BTC, XMR, LTC",
    "Boltz" : "BTC, BTC-LN, ETH",
    "Coin Swap" : "BTC, BTC-LN, XMR, LTC",
    "Sideshift.ai" : "BTC, BTC-LN, XMR, ETH, LTC, BCH, +more",
    "Swapuz" : "BTC, XMR, ETH, LTC, BCH, +more",
    "Kuyumcu" : "XMR, XNO",
    "HodlHodl" : "BTC",
    "Infinity Exchanger" : "BTC, XMR, LTC, BCH",
    "StealthEX" : "BTC, XMR, ETH, LTC, BCH, +more",
    "TradeOgre" : "BTC, LTC, USDT, XMR(i), ETH(i), LTC(i), +more",
    "LocalCryptos" : "BTC, ETH, LTC, BCH, DASH",
}



class Exchange:
    def __init__(self, raw_json):
        self.from_json(raw_json)

    def __hash__(self):
        return hash(self.__dict__.values())

    #extract relevant json data
    def from_json(self, raw_json):
        j = raw_json
        self.name = j["name"]
        self.description = j["long-description"].replace("\n", " ").split("<br>")[0]

        #adjust score to be x/5 instead of x/10W
        self.score = ((round(j["score"]) / 2) - 0.5) + score_boost.get(self.name, 0)

        #automatically detects supported currencies. Only finds BTC & XMR automatically.
        #this feature is unused currently
        #self.currencies = [
        #    i[1] for i in (("xmr", "XMR"), ("btc", "BTC")) if j[i[0]]
        #] + ["INCOMPLETE"] #"INCOMPLETE" should be removed when manually inputting the supported currencies

        self.currencies = currencies.get(self.name, "ERROR")

        self.fiat = j["cash"]

        #determines the "type" of exchange (p2p vs centralized, & custodial vs non-custodial)
        trade_type = "p2p" if j["p2p"] else "centralized"
        custody_type = {True:"", "semi":"semi-", False:"non-"}[j["custodial"]]
        self.trade_type = f"{trade_type} {custody_type}custodial"

        #set clearweb url
        self.url = j["url"]
        if type(self.url) == list: self.url = self.url[0]

        #set onion url
        onion_url = j["tor-onion"]
        self.onion = ""
        if onion_url and onion_url != "false":
            #if there is ONLY a Tor url, then don't repeat it as the regular url
            if onion_url == j["url"]: self.url = ""
            self.onion = onion_url


#read json file "exchanges.json"
def read_json():
    #check each exchange to see if it meets the requirements, return a "cleaned" list
    def purge_exchanges(exchanges):
        passed = []
        for exchange in exchanges:
            if exchange["name"] in banned: continue

            for r in requirements:
                #compare the exchange's value to the requirements
                eval_str = f"{exchange[r]}{requirements[r]}"
                if not eval(eval_str): break

            else: passed.append(exchange)
        return passed

    with open("exchanges.json", "r") as f:
        exchanges = purge_exchanges(
            json.load(f)["exchanges"]
        )
        exchanges = [Exchange(e) for e in exchanges]
        return sorted(exchanges, key = lambda x: x.score, reverse = True)

#automatically create the "exchanges" html page
def create_html(exchanges):
    #create a hash of the exchange list to know when something has changed
    #currently this isn't used, at some point may be used to detect and confirm changes before overwriting
    def get_config_id():
        exchange_hashes = [str(hash(e)).encode() for e in exchanges]
        return hashlib.sha1(b"1337".join(exchange_hashes)).hexdigest()

    #create the lines of html code
    lines = []
    lines += [
        '<!DOCTYPE HTML PUBLIC><body style="background-color:#d3d3d3;"><link rel = "icon" href = "images/anon.png"><title>BASH KYC - Fiat Exchanges</title>',
        '<style>',
        'h2{text-align:center;display: block;font-size: 1.75em;margin-top: 0.67em;margin-bottom: 0.67em;margin-left: 0;margin-right: 0;font-weight: bold;}',
        'img {float: left;}',
        'body{margin:40px auto;max-width:1000px;line-height:1.6;font-size:18px;color:#444;padding:0 10px}',
        '</style>',
        '<strong>Note</strong>: Some exchanges "unofficially" support certain currencies.',
        'For example, Bisq can be used to indirectly trade Monero and Litecoin (XMR -> BTC -> LTC), even though it technically only supports Bitcoin.',
        'Currencies which can be traded indirectly will be marked with "(i)".',
        'For example, XMR(i) or LTC(i).',
        '<br><br>',
    ]

    fiat_exchanges, crypto_exchanges = [], []
    for e in exchanges:
        e_lines = [
            f'<h2 style="display: inline;" id="{e.name}">{e.name}</h2><br>',
            f'{e.description}<br>',
            f'<strong>rating</strong>: {e.score if e.fiat else e.score + 0.5}/5&emsp;',
            f'<strong>type</strong>: {e.trade_type}&emsp;',
            #f'<br><strong>supported currencies</strong>: {", ".join(e.currencies)}',
            f'<br><strong>supported currencies</strong>: {e.currencies}',
        ]

        if e.url: e_lines.append(
            f'<br><strong>website</strong>: <a href="{e.url}" target="_blank" rel="nofollow noreferrer noopener">{e.url}</a>'
        )
        if e.onion: e_lines.append(
            f'<br><strong>onionsite</strong>: <a href="{e.onion}" target="_blank" rel="nofollow noreferrer noopener">{e.onion}</a></a>'
        )
        e_lines.append('<br><br>')
        if e.fiat: fiat_exchanges += e_lines
        else: crypto_exchanges += e_lines

    lines.append('<h1 style="font-size:250%;" id="fiat">Buy/Sell Cryptocurrency With Fiat</h1>')
    lines.append('These exchanges provide KYC-free methods to buy cryptocurrency with fiat, or with other cryptocurrencies.<br><br>')
    lines += fiat_exchanges
    lines.append('<h1 style="font-size:250%;" id="crypto">Cryptocurrency-Only Exchanges/Swaps</h1>')
    lines.append('These exchanges support KYC-free trading between cryptocurrencies, but cannot be used to convert to/from fiat.<br><br>')
    lines += crypto_exchanges
    lines += [
        '<br><br><br>'
        '<strong>This list was not created by me</strong>, it is from <a href="https://kycnot.me/" target="_blank" rel="nofollow noreferrer noopener">kycnot.me</a>.',
        'It has been modified, by removing exchanges which are too KYC-friendly, tweaking some rankings, and simplifying by reducing the amount of information shown.',
        'Full credit goes to kycnotme.',
    ]
    lines.append(f'<!--{get_config_id()}-->')
    return lines

#write html to file
def write_html(html_lines, filename = "exchanges.html"):
    with open(filename, "w") as f:
        for line in html_lines: f.write(line + "\n")

if __name__ == "__main__":
    if input("overwrite current file (y/n)? ") == "y":
        write_html(create_html(read_json()))