import sys
import random

import requests
import json

from cookie_reader import init_cookie

NO_GRAPH = False

try:
    from matplotlib import pyplot as plt
except:
    print('W : No matplotlib library found!')
NO_GRAPH = True

cookie = init_cookie()

# check cookie
if not cookie:
    print('E : No cookie found!')
    sys.exit(1)

_word = '%E5%93%AA%E5%90%92%E4%B9%8B%E9%AD%94%E7%AB%A5%E9%99%8D%E4%B8%96'
_days = 180

_url_uniqid = 'http://index.baidu.com/Interface/ptbk?uniqid=%s'
_url_index = 'http://index.baidu.com/api/SearchApi/index?word=%s&area=0&days=%s'
_url_word_check = 'http://index.baidu.com/api/AddWordApi/checkWordsExists?word=%s'

_c_uniqid_data = 'data'
_c_index_data = 'data'
_c_index_uniqid = 'uniqid'
_c_index_uindex = 'userIndexes'
_c_index_wise = 'wise'
_c_check_data = 'data'
_c_check_result = 'result'


def get_random_color() -> str:
    '''
    return a hex color str
    '''

    hex_chr = '0123456789ABCDEF'

    return '#' + ''.join([random.choice(hex_chr) for _ in range(6)])


class BaiduIndexDecoder:
    def __init__(self, word :str, label=None):
        self.name = word
        self.label = label if label else word

        self.__word = word
        self.__index_json = dict()
        self.__uniqid_json = dict()

        self.__init_jsons()

    @property
    def __wise_data(self) -> str:
        return self.__index_json[_c_index_data][_c_index_uindex][0][_c_index_wise][_c_index_data]

    @property
    def __index_uniqid(self) -> str:
        return self.__index_json[_c_index_data][_c_index_uniqid]

    @property
    def __uniqid_key(self) -> str:
        return self.__uniqid_json[_c_uniqid_data]
        
    def __get_index_json(self) -> dict:
        print('M : getting data of \'%s\'...' % self.__word)
        rf = requests.get(_url_index % (self.__word, _days), cookies=cookie)

        return json.loads(rf.text)

    def __get_uniqid_json(self) -> dict:
        print('M : getting uniqid of \'%s\'...' % self.__word)
        rq = requests.get(_url_uniqid % self.__index_uniqid, cookies=cookie)

        return json.loads(rq.text)

    def __init_jsons(self):
        self.__index_json = self.__get_index_json()
        self.__uniqid_json = self.__get_uniqid_json()

    def __decrypt_by_key(self, data :str, key :str) -> str:
        '''
        original decrypt function:

        decrypt: function(t, e) {
            for (var n = t.split(""), i = e.split(""), a = {},
            r = [], o = 0; o < n.length / 2; o++) a[n[o]] = n[n.length / 2 + o];
            for (var s = 0; s < e.length; s++) r.push(a[i[s]]);
            return r.join("")
        }
        '''
        print('M : decrypting data by key...')
        
        key_map = {}

        for o in range(len(key) // 2):
                key_map[key[o]] = key[len(key) // 2 + o]

        data_str = ''

        for s in range(len(data)):
                data_str += key_map[data[s]]

        print('M : decryption success!')

        return data_str

    def get_real_data(self) -> list:
        data = self.__decrypt_by_key(self.__wise_data, self.__uniqid_key)

        return [int(x) for x in data.split(',')]

    def test_decrypt(self, data :str, key :str) -> str:
        return self.__decrypt_by_key(data, key)


class BaiduIndexManager:
    def __init__(self):
        self.__bdc_list = []

    def __check_word_exists(self, word :str) -> bool:
       rc = requests.get(_url_word_check % word, cookies=cookie)
       cjson = json.loads(rc.text)

       if cjson[_c_check_data] == '':  # empty keyword
           return False

       return cjson[_c_check_data][_c_check_result] == []

    def add_keyword(self, keyword :str, label :str=None):
        if keyword in [b.name for b in self.__bdc_list]:
                print('W : \'%s\' already in list!' % keyword)
                return
        
        print('M : checking word \'%s\' exists...' % keyword)
        if not self.__check_word_exists(keyword):
                print('W : \'%s\' is not exists! will not be added to graph!' % keyword)
                return
        
        print('M : \'%s\' exists!' % keyword)
        bdc = BaiduIndexDecoder(keyword, label)

        self.__bdc_list.append(bdc)

    def remove_keyword(self, keyword):
        for bdc in self.__bdc_list:
                if bdc.name == keyword:
                        self.__bdc_list.remove(bdc)

    def make_graph(self, title='Untitled graph', xlabel='day', ylabel='index'):
        if not self.__bdc_list:
                print('W : No data to draw!')
                return
        
        print('M : day range = %s' % _days)
        print('M : drawing...')
        df = self.__bdc_list[0].get_real_data()
        x = range(1, len(df) + 1)

        yl = [x.get_real_data() for x in self.__bdc_list[1:]]
        yl = [df] + yl

        for y, name in zip(yl, [bdc.label for bdc in self.__bdc_list]):
                plt.plot(x, y, label=name, color=get_random_color())
                
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.text(0, 0, 'index.baidu.com', alpha=0.1)
        plt.legend()
        plt.grid()

    def show_graph(self):
        print('M : show graph')

        plt.show()

    def save_graph(self, path :str):
        print('M : saving graph to %s' % path)
        
        plt.savefig(path)

        print('M : graph saved')


def main(self, *args):
    _help = \
    '''
    usage : python -m baidu_index (show/save) [keyword_list] [-p save path]
    '''

    args = list(args)

    if len(args) < 1:
        print(_help)
        return

    mode = 0  # 0 -- show   1 -- save
    illegal = ('save', 'show', '-p')

    if args[0] in ('show', 'save'):
        mode = ('show', 'save').index(args[0])
    else:
        print(_help)
        return
    args.pop(0)

    kwl = []
    pi = -1

    for i, k in zip(range(len(args)), args):
        if k in ('-l', '-p', 'd'):
            break

        kwl.append(k)

    try:
        pi = args.index('-p')
    except ValueError:
        pi = -1

    try:
        di = args.index('-d')
    except ValueError:
        di = -1

    [args.remove(k) for k in kwl]

    if di != -1:
        di = args.index('-d')
        
        try:
            global _days
            _days = int(args[di+1])
        except ValueError:
            print(_help)
            return

        args.pop(di+1)
        args.pop(di)
    
    if mode and pi != -1:
        pi = args.index('-p')
        p = args[pi+1]
        args.pop(pi+1)
        args.pop(pi)

    elif mode and pi == -1:
        print(_help)
        return

    elif not mode and pi != -1:
        print(_help)
        return

    if len(args) > 1 and args[0] != '-l':
        print(_help)
        return
    elif len(args) == 0:
        return
    
    args.remove('-l')
    lbl = []

    for _, l in zip(range(len(kwl)), args):
        lbl.append(l)
    
    # run manager

    mgr = BaiduIndexManager()

    if len(lbl) != len(kwl):
        s = len(kwl) - len(lbl)
        if s > 0:
            lbl += [None for _ in range(s)]  # fill with None

    for l, k in zip(lbl, kwl):
        mgr.add_keyword(k, l)
    
    mgr.make_graph('index in recent %s days' % _days)
    if mode:
        mgr.save_graph(p)
    else:
        mgr.show_graph()


if __name__ == '__main__':
    main(*sys.argv)


'''
if __name__ == '__main__':
    print('M : day range = %s' % _days)
    manager = BaiduIndexManager()
    manager.add_keyword('姜子牙', 'Jiangziya')
    manager.add_keyword('哪吒', 'Nezha')
    manager.make_graph('index in recent %s days' % _days)
    manager.save_graph('test.png')
'''
