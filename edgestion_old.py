# -*- coding:utf-8 -*-
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import json
import time
import glob
from selenium import webdriver
import time
import pymssql #运行此程序前，需要安装pymssql
import pandas as pd


def APS():
    starttime = time.time()
    file = r'./APS.csv'
    lst_dic = APSdownload()
    APSprocess(lst_dic)
    QueryGener(file)
    print('finish')
    endtime = time.time()
    print('总耗时', endtime - starttime, 'S')

def APS_update():
    starttime = time.time()
    file = r'./APS.csv'
    lst_dic = APSdownload()
    df = APSprocess(lst_dic)
    df_old = pd.read_csv(file)
    df_new = df[~df['doi'].isin(list(df_old['doi']))]
    print('新记录数',len(df_new))
    df.to_csv(r'./APS.csv',index = False)
    QueryGener(file)
    print('finish')
    endtime = time.time()
    print('总耗时', endtime - starttime, 'S')

def ACS_update():
    starttime = time.time()
    file = r'./ACS.csv'
    df_old = pd.read_csv(file)
    lst_dic_new = ACS_updatedownload(df_old)
    df = ACSprocess(lst_dic_new)
    df_new = df[~df['doi'].isin(list(df_old['doi']))]
    if len(df_new) == 0:
        print('无更新数据')
    else:
        print('新记录数',len(df_new))
        df_new.to_csv(r'./ACS_update.csv', index = False)
        file = r'./ACS_update.csv'
        QueryGener(file)
        print('finish')
        endtime = time.time()
        print('总耗时', endtime - starttime, 'S')

def APSdownload():
    lst_dic = []
    u = "https://journals.aps.org/search/results?clauses=%5B%7B%22field%22:%22all%22,%22value%22:%22%22,%22operator%22:%22AND%22%7D%5D&sort=recent&per_page=100&page=1&category=suggestion"
    r = requests.get(u)
    soupi = BeautifulSoup(r.text, 'lxml')
        #获取数据
    content = str(soupi.find_all('script')[9])
    num_papers = re.match('.*"suggestion":{"count":([\s\S]*),"value":"suggestion","label.*',content).group(1)
    num_pages = int(int(num_papers)/100) +1
    print('共',num_pages,'页')
    print('共',num_papers,'篇')
    for i in range(num_pages):
        u = "https://journals.aps.org/search/results?clauses=%5B%7B%22field%22:%22all%22,%22value%22:%22%22,%22operator%22:%22AND%22%7D%5D&sort=recent&per_page=100&page="+ str(i+1)+"&category=suggestion"
        r = requests.get(u)
        soupi = BeautifulSoup(r.text, 'lxml')
            #获取数据
        content = str(soupi.find_all('script')[9])

        result_re = re.match('.*{"hits":\[([\s\S]*)\],"facets".*',content)
        result_decode = result_re.group(1)

        result_n = result_decode.replace('},{"actions"','},\n{"actions"')
        results = result_n.split(',\n')
        num_page = len(results)
        print('当页记录数',num_page)

            #time.sleep(1)
        for result in results:
            dic = json.loads(result)
            lst_dic.append(dic)
        num_finish = len(lst_dic)
        print('已完成',num_finish,'篇','percent: {:.2%}'.format(float(num_finish)/float(num_papers)))
    print('爬取完毕')
    print(len(lst_dic))
    return(lst_dic)

def ACS():
    starttime = time.time()
    file = r'./ACS.csv'
    lst_dic = ACSdownload()
    df = ACSprocess(lst_dic)
    df.to_csv(r'./ACS.csv',index = False)
    QueryGener(file)
    print('finish')
    endtime = time.time()
    print('总耗时', endtime - starttime, 'S')


def APSprocess(lst_dic):
    '''
    输入数据字典列表
    '''
    print('开始数据处理')
    df = pd.DataFrame(lst_dic)
    #新建两列进行pdf，及html文档地址的存储
    df['pdf'] = ''
    df['html'] = ''
    for i in range(len(df)):
        dic = df.loc[i]['actions']
        df.loc[i,'pdf'] = dic['pdf']['link']
        df.loc[i,'html'] = dic['html']['link']

    #links:包含论文的文档下载地址
    #df['ExtraScore'] = df['Nationality'].apply(lambda x : 5 if x != '汉' else 0
    df['len_links'] = df['links'].apply(lambda x : len(x))
    list(set(df['len_links']))
    # [0,1]
    # 说明地址列最多只有一种地址
    def f_url(x):
        try:
            return x[0]['url']
        except:
            1
    def f_anchor(x):
        try:
            return x[0]['anchor']
        except:
            1
    def f_title(x):
        try:
            return x[0]['title']
        except:
            1
    df['links_url'] = df['links'].apply(f_url)
    df['links_anchor'] = df['links'].apply(f_anchor)
    df['links_title'] = df['links'].apply(f_title)

    #直接将links扩展为三列，links_url,links_anchor,links_title
    def Clean(x):
        processed_x = ''
        try:
            processed_x = BeautifulSoup(x, 'lxml').text
        except:
            1
        return processed_x
    df['link_fix'] = 'https://journals.aps.org' + df['link']
    df['summary_fix'] = df['summary'].apply(Clean)
    df['teaser_fix'] = df['teaser'].apply(Clean)
    df['title_fix'] = df['title'].apply(Clean)
    df['pdf_fix'] = 'https://journals.aps.org' + df['pdf']
    df['html_fix'] = 'https://journals.aps.org' + df['html']
    df['links_anchor_fix'] = df['links_anchor'].apply(Clean)
    df['links_title_fix'] = df['links_title'].apply(Clean)
    print('数据处理完成')
    return df

def ACSprocess(lst_dic):
    '''
    输入数据字典列表
    '''
    print('开始数据处理')
    df = pd.DataFrame(lst_dic)
    df['img_paper_fix'] = 'https://pubs.acs.org' + df['img_paper']
    df['img_journal_fix'] = 'https://pubs.acs.org' + df['img_journal']
    df['doi'] = df['doi'].str.replace('doi/','')
    df['Abstract_fix'] = 'https://pubs.acs.org' + df['Abstract']
    df['Abstractlink'] = df['Abstract']
    df = df.drop('Abstract',axis = 1)
    df['fulltext_link_fix'] = 'https://pubs.acs.org' + df['fulltext_link']
    df['pdf_link_fix'] = 'https://pubs.acs.org' + df['pdf_link']

    try:
        df['First_page_fix'] = 'https://pubs.acs.org' + df['First Page']
    except:
        1
    try:
        df['Fulltext_fix'] = 'https://pubs.acs.org' + df['Full text']
    except:
        1
    print('数据处理完成')
    return df


def QueryGener(file):
    df = pd.read_csv(file)
    query = ''
    for i in range(len(df)):
        queryi = 'DO = (' + df.iloc[i]['doi'] + ')'
        if i == 0:
            query = queryi
            continue
        query = query + ' OR ' + queryi

    newfile = file.split('.')[1][1:] + '.txt'
    with open(newfile,'w') as f:
        f.write(query)
    print('检索式生成完成')

def Concat_xls(files):
    files = r"./" + files + "/*.xls"
    df_all = pd.DataFrame()
    lst = glob.glob(files)
    for li in lst:
        dfi = pd.read_excel(li)
        df_all = pd.concat([df_all,dfi])
    return df_all


def ACSdownload():
    tag = 1
    title_last = ''
    lst_dic = []
    while(tag):
        print(tag)
        u = "https://pubs.acs.org/editorschoice/?widgetSort=EditorsChoiceDate&widgetFilter=&widgetPage=" + str(tag-1)
        r = requests.get(u)
        soupi = BeautifulSoup(r.text, 'lxml')

        for i in range(len(soupi.find_all('div',class_ = 'issue-item clearfix'))):
            #print(i)

            dic = {}
            contenti = str(soupi.find_all('div',class_ = 'issue-item clearfix')[i])
            try:
                dic['img_paper'] = re.match('[\s\S]*"Article figure" class="lazy" data-src="([\s\S]*?)"/><noscript>[\s\S]*',contenti).group(1)
            except:
                1
            try:
                dic['img_journal'] = re.match('[\s\S]*alt="Journal logo" src="([\s\S]*)"/></noscript>[\s\S]*',contenti).group(1)
            except:
                1
            dic['doi'] = re.match('[\s\S]*"issue-item_title"><a href="/([\s\S]*?)" title="[\s\S]*',contenti).group(1)
            dic['title'] = soupi.find_all('h5',class_ ='issue-item_title')[i].text
            dic['authors'] = soupi.find_all('ul',class_ ='rlist--inline loa mobile-authors issue-item_loa')[i].text.replace('\xa0',' ')
            dic['journal_full'] = soupi.find_all('div',class_ ='issue-item_info_list')[i].text
            dic['journal'] = re.match('[\s\S]*issue-item_jour-name"><i>([\s\S]*)</i></span>[\s\S]*',contenti,re.M).group(1)

            dic['year'] = re.match('[\s\S]*<span class="issue-item_yearpubdate"> <span>([\s\S]*?)</span></span>[\s\S]*',contenti).group(1)
            dic['paper_type'] = re.match('[\s\S]*<span class="issue-item_type"> \(([\s\S]*?)\)</span>[\s\S]*',contenti).group(1)
            dic['pubulicationdata'] = soupi.find_all('span',class_='issue-item_pubdate')[i+i].text
            try:
                dic['choicedate'] = re.match('[\s\S]*ACS Editors\' Choice Date</span><span class="date-separator">:</span>([\s\S]*?)</span>[\s\S]*',contenti).group(1)
            except:
                1
            key = soupi.find_all('ul',class_='issue-item_buttons-list')[i].find_all('li')[0].a['title']
            dic[key] = soupi.find_all('ul',class_='issue-item_buttons-list')[i].find_all('li')[0].a['href']
            dic['fulltext_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="Full text">[\s\S]*',contenti).group(1)
            dic['pdf_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="PDF"[\s\S]*',contenti).group(1)
            try:
                dic['abstract'] = soupi.find_all('div',class_='issue-item_footer')[i].find('div').find('div').text
            except:
                1
            #print(dic['title'])
            if i == 0:
                title_now = dic['title']
            lst_dic.append(dic)
        tag = tag + 1
        if title_now == title_last:
            tag = 0
        else:
            title_last =  title_now
        print(len(lst_dic))
    print('爬取完毕')
    print(len(lst_dic))
    return(lst_dic)

def ACS_updatedownload(df):
    tag = 1
    title_last = ''
    lst_dic = []
    lst_doi = list(df['doi'])
    while(tag):
        print(tag)
        u = "https://pubs.acs.org/editorschoice/?widgetSort=EditorsChoiceDate&widgetFilter=&widgetPage=" + str(tag-1)
        r = requests.get(u)
        soupi = BeautifulSoup(r.text, 'lxml')

        for i in range(len(soupi.find_all('div',class_ = 'issue-item clearfix'))):
            #print(i)

            dic = {}
            contenti = str(soupi.find_all('div',class_ = 'issue-item clearfix')[i])
            try:
                dic['img_paper'] = re.match('[\s\S]*"Article figure" class="lazy" data-src="([\s\S]*?)"/><noscript>[\s\S]*',contenti).group(1)
            except:
                1
            dic['img_journal'] = re.match('[\s\S]*alt="Journal logo" src="([\s\S]*)"/></noscript>[\s\S]*',contenti).group(1)
            dic['doi'] = re.match('[\s\S]*"issue-item_title"><a href="/([\s\S]*?)" title="[\s\S]*',contenti).group(1)
            dic['title'] = soupi.find_all('h5',class_ ='issue-item_title')[i].text
            dic['authors'] = soupi.find_all('ul',class_ ='rlist--inline loa mobile-authors issue-item_loa')[i].text.replace('\xa0',' ')
            dic['journal_full'] = soupi.find_all('div',class_ ='issue-item_info_list')[i].text
            dic['journal'] = re.match('[\s\S]*issue-item_jour-name"><i>([\s\S]*)</i></span>[\s\S]*',contenti,re.M).group(1)

            dic['year'] = re.match('[\s\S]*<span class="issue-item_yearpubdate"> <span>([\s\S]*?)</span></span>[\s\S]*',contenti).group(1)
            dic['paper_type'] = re.match('[\s\S]*<span class="issue-item_type"> \(([\s\S]*?)\)</span>[\s\S]*',contenti).group(1)
            dic['pubulicationdata'] = soupi.find_all('span',class_='issue-item_pubdate')[i+i].text
            try:
                dic['choicedate'] = re.match('[\s\S]*ACS Editors\' Choice Date</span><span class="date-separator">:</span>([\s\S]*?)</span>[\s\S]*',contenti).group(1)
            except:
                1
            key = soupi.find_all('ul',class_='issue-item_buttons-list')[i].find_all('li')[0].a['title']
            dic[key] = soupi.find_all('ul',class_='issue-item_buttons-list')[i].find_all('li')[0].a['href']
            dic['fulltext_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="Full text">[\s\S]*',contenti).group(1)
            dic['pdf_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="PDF"[\s\S]*',contenti).group(1)
            try:
                dic['abstract'] = soupi.find_all('div',class_='issue-item_footer')[i].find('div').find('div').text
            except:
                1
            #print(dic['title'])
            if i == 0:
                title_now = dic['title']
            lst_dic.append(dic)
            if dic['doi'] in lst_doi:
                tag = 0
                break
        if tag != 0:
            tag = tag + 1
        if title_now == title_last:
            tag = 0
        else:
            title_last =  title_now
        print(len(lst_dic))
    print('爬取完毕')
    print(len(lst_dic))
    return(lst_dic)

def Openwos():
    brower = webdriver.Chrome()
    #检索结果页地址
    url = "https://www.webofscience.com/wos/alldb/basic-search"
    brower.get(url)
    return brower

def Crul(brower):
    time.sleep(3)
    #设置爬取页面
    #handles = brower.window_handles
    #brower.switch_to_window(handles[3])
    num = brower.find_element_by_xpath('/html/body/app-wos/div/div/main/div/app-input-route/app-base-summary-component/app-search-friendly-display/div[1]/app-general-search-friendly-display/h1/span').text.replace(',','')
    page1000 = int(int(num)/1000)+1
    count = 0
    try:
        brower.find_element_by_xpath('//*[@id="pendo-close-guide-8fdced48"]').click()
        time.sleep(2)
        brower.find_element_by_xpath('//*[@id="pendo-close-guide-dc656865"]').click()
        time.sleep(1)
    except:
        1
    for i in range(page1000):
    #也可设置为从第n开始
    #for i in range(n, 120):
        count += 1
        if count ==60:
            time.sleep(30)
        #如果爬取超过90页，就休眠120S，可以自行设置页数
        print("第" + str(i+1) + "次")     
        
        time.sleep(7)
        brower.find_element_by_xpath('//*[@id="snRecListTop"]/app-export-menu/div/button').click()
        time.sleep(1)
        brower.find_element_by_xpath('//*[@id="exportToExcelButton"]').click()
        
        #点击recordfrom

        time.sleep(1)
        brower.find_element_by_xpath('//*[@id="radio3"]/label/span[2]').click() 
        time.sleep(1)

        start = brower.find_element_by_xpath('/html/body/app-wos/div/div/main/app-input-route/app-export-overlay/div/div[3]/div[2]/app-export-out-details/div/div[2]/div/fieldset/mat-radio-group/div[3]/mat-form-field[1]/div/div[1]/div/input')
        end = brower.find_element_by_xpath('/html/body/app-wos/div/div/main/app-input-route/app-export-overlay/div/div[3]/div[2]/app-export-out-details/div/div[2]/div/fieldset/mat-radio-group/div[3]/mat-form-field[2]/div/div[1]/div/input')
        start.clear()
        end.clear()
        if i != page1000-1:
            start_no = 1 + i*1000
            end_no =  1000 + i*1000
        else:
            start_no = end_no + 1
            end_no = num
        start.send_keys(start_no)
        end.send_keys(end_no)
        time.sleep(1)

        #选择record content
        brower.find_element_by_xpath('/html/body/app-wos/div/div/main/app-input-route/app-export-overlay/div/div[3]/div[2]/app-export-out-details/div/div[2]/div/div[1]/wos-select/button').click()
        brower.find_element_by_xpath('//*[@id="global-select"]/div/div[2]/div[1]').click()

        brower.find_element_by_xpath('/html/body/app-wos/div/div/main/app-input-route/app-export-overlay/div/div[3]/div[2]/app-export-out-details/div/div[2]/div/div[2]/button[1]/span[1]/span').click()
        time.sleep(7)

if __name__ == '__main__':
    APS()