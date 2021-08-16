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
import key
import datetime
from sqlalchemy import create_engine
from sqlalchemy.types import NVARCHAR, INT,Text, FLOAT

def ACS():
    starttime = time.time()
    Creattable_ACS(key)
    lst_dic = ACS_updatedownload(key)
    df = ACSprocess(lst_dic)
    df['ACS_tag'] = 1
    df['UT'] = ''
    ACSuploadData(df,key)
    QueryGener_ACS(key)
    endtime = time.time()
    print('总耗时', endtime - starttime, 'S')
def UpdateACS():
    lst_dic = ACS_updatedownload(key)
    if len(lst_dic) >0:
        df = ACSprocess(lst_dic)
        df['ACS_tag'] = 1
        df['UT'] = ''
        ACSuploadData(df,key)
        print('记录上传成功')
        QueryGener_ACS(key)


def UpdateAPS():
    lst_dic = APS_updatedownload(key)
    if len(lst_dic) >0:
        df = APSprocess(lst_dic)
        df['APS_tag'] = 1
        df['UT'] = ''
        APSuploadData(df,key)
        print('记录上传成功')
        QueryGener_APS(key)
def Creattable_ACS(key):
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    cs1 = conn.cursor()
    query = '''
    CREATE TABLE [BP_Extension].[dbo].[ACS_Edsug]
    (
        img_paper VARCHAR(255),
        img_journal VARCHAR(255),
        doi VARCHAR(255),
        title Text,
        authors Text,
        journal_full VARCHAR(255),
        Abstract VARCHAR(255),
        fulltext_link VARCHAR(255),
        pdf_link VARCHAR(255),
        PDF VARCHAR(255),
        [First Page] VARCHAR(255),
        [Full text] VARCHAR(255),
        img_paper_fix VARCHAR(255),
        img_journal_fix VARCHAR(255),
        Abstract_fix VARCHAR(255),
        fulltext_link_fix VARCHAR(255),
        pdf_link_fix VARCHAR(255),
        First_page_fix VARCHAR(255),
        Fulltext_fix VARCHAR(255),
        ACS_tag int,
        UT VARCHAR(255),
    )'''
    cs1.execute(query)
        # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    conn.commit()
    # 关闭cursor对象
    cs1.close()
        # 关闭connection对象
    conn.close()
    
def ACS_updatedownload(key):
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi from [BP_Extension].[dbo].[ACS_Edsug]"
    df_utnull = pd.read_sql(query,con=conn)
    lst_doi = list(df_utnull['doi'])
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    # 关闭connection对象
    conn.close()
    # 创建connection连接
    tag = 1
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
            dic['doi'] = re.match('[\s\S]*"issue-item_title"><a href="/([\s\S]*?)" title="[\s\S]*',contenti).group(1).replace('doi/','')
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
            try:
                dic['fulltext_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="Full text">[\s\S]*',contenti).group(1)
            except:
                1
            dic['pdf_link'] = re.match('[\s\S]*<li><a href="([\s\S]*?)" title="PDF"[\s\S]*',contenti).group(1)
            try:
                dic['abstract'] = soupi.find_all('div',class_='issue-item_footer')[i].find('div').find('div').text
            except:
                1
            #print(dic['title'])
            if dic['doi'] not in lst_doi:
                lst_doi.append(dic['doi'])
                lst_dic.append(dic)
            else:
                tag = -1
                break
        tag = tag + 1
        print('记录数',len(lst_dic))
    print('爬取完毕')
    print(len(lst_dic))
    return(lst_dic)
def ACSprocess(lst_dic):
    '''
    输入数据字典列表
    '''
    if len(lst_dic) >0:
        print('开始数据处理')
        df = pd.DataFrame(lst_dic)
        df['img_paper_fix'] = 'https://pubs.acs.org' + df['img_paper']
        df['img_journal_fix'] = 'https://pubs.acs.org' + df['img_journal']
        df['doi'] = df['doi'].str.replace('doi/','')

        df['Abstract_fix'] = 'https://pubs.acs.org' + df['Abstract']
        df['Abstract_link'] = df['Abstract']
        df = df.drop('Abstract',axis =1)
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
    else:
        print('无处理记录')
        return pd.DataFrame()

def ACSuploadData(df,key):
    conn = create_engine('mssql+pymssql://'+ key.sql.username +':' + key.sql.password+ '@' + key.sql.host+ '/BP_Extension')
    dtypedict = {
        'img_paper' : NVARCHAR(length=255),
        'img_journal' : NVARCHAR(length=255),
        'doi': NVARCHAR(length=255),
        'title': Text(),
        'authors': Text(),
        'journal_full': NVARCHAR(length=255),
        'Abstract': NVARCHAR(length=255),
        'fulltext_link': NVARCHAR(length=255),
        'pdf_link': NVARCHAR(length=255),
        'PDF': NVARCHAR(length=255),
        '[First Page]': NVARCHAR(length=255),
        '[Full text]': NVARCHAR(length=255),
        'img_paper_fix': NVARCHAR(length=255),
        'img_journal_fix': NVARCHAR(length=255),
        'Abstract_fix': NVARCHAR(length=255),
        'fulltext_link_fix': NVARCHAR(length=255),
        'pdf_link_fix': NVARCHAR(length=255),
        'First_page_fix': NVARCHAR(length=255),
        'Fulltext_fix': NVARCHAR(length=255),
        'ACS_tag': INT(),
        'UT': NVARCHAR(length=255)
    }
    df.to_sql(name='ACS_Edsug', con=conn, if_exists='append', index=False, dtype=dtypedict)
    conn.dispose()

def QueryGener_ACS(key):
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi,title,UT from [BP_Extension].[dbo].[ACS_Edsug] where UT = '' or UT = 'nan' or UT is NULL"
    df = pd.read_sql(query,con=conn)
    conn.close()
    query = ''
    for i in range(len(df)):
        queryi = 'DO = (' + df.iloc[i]['doi'] + ')'
        if i == 0:
            query = queryi
            continue
        query = query + ' OR ' + queryi

    newfile = './Query_ACS.txt'
    with open(newfile,'w') as f:
        f.write(query)
    print('检索式生成完成')
def Updatewos_ACS(df_all):
    try:
        df_all['doi'] = df_all['DOI'].astype('str')
        df_all['UT'] = df_all['UT (Unique ID)'].astype('str')
    except:
        df_all['doi'] = df_all['doi'].astype('str')
        df_all['UT'] = df_all['UT'].astype('str')
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    # 获取cursor对象
    cs1 = conn.cursor()
    for i in range(len(df_all)):
        query = "update [BP_Extension].[dbo].[ACS_Edsug] set UT = '" + df_all.iloc[i]['UT'] +"' where doi = '" + df_all.iloc[i]['doi'] +"'"
        cs1.execute(query)
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    conn.commit()
    # 关闭cursor对象
    cs1.close()
    # 关闭connection对象
    conn.close()
    # 创建connection连接
    print('完成更新，共',len(df_all),'条记录')
def CheckACS():
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi,title,UT from [BP_Extension].[dbo].[ACS_Edsug] where UT = '' or UT = 'nan'or UT is NULL"
    df_utnull = pd.read_sql(query,con=conn)
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    # 关闭connection对象
    conn.close()
    # 创建connection连接
    df_utnull = df_utnull[['doi','UT','title']]
    print('仍有',len(df_utnull),'条空记录请检查acs_null.csv文件')
    df_utnull.to_csv(r'./acs_null.csv',index = False)
'''
----------------------------------------------------------------------
'''

def Concat_xls(files):
    files = r"./" + files + "/*.xls"
    df_all = pd.DataFrame()
    lst = glob.glob(files)
    for li in lst:
        dfi = pd.read_excel(li)
        df_all = pd.concat([df_all,dfi])
    return df_all
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
    print('下载完成')
'''
------------------------------------------------------------------------------
------------------------------------------------------------------------------
'''
def APS():
    starttime = time.time()
    Creattable_APS(key)
    lst_dic = APS_updatedownload(key)
    df = APSprocess(lst_dic)
    df['APS_tag'] = 1
    df['UT'] = ''
    APSuploadData(df,key)
    QueryGener_APS(key)
    endtime = time.time()
    print('总耗时', endtime - starttime, 'S')

def Creattable_APS(key):
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    cs1 = conn.cursor()
    query = '''
    CREATE TABLE [BP_Extension].[dbo].[APS_Edsug]
    (
    id VARCHAR(255),
    [index] VARCHAR(255),
    [type] VARCHAR(255),
    link VARCHAR(255),
    title Text,
    date VARCHAR(255),
    date_label VARCHAR(255),
    features VARCHAR(255),
    score FLOAT,
    citation VARCHAR(255),
    journal VARCHAR(255),
    doi VARCHAR(255),
    authors Text,
    summary Text,
    teaser Text,
    image VARCHAR(255),
    links Text,
    subject_areas Text,
    citation_count_text VARCHAR(255),
    pdf VARCHAR(255),
    html VARCHAR(255),
    len_links FLOAT,
    links_url VARCHAR(255),
    links_anchor VARCHAR(255),
    links_title Text,
    link_fix VARCHAR(255),
    summary_fix Text,
    teaser_fix Text,
    title_fix Text,
    pdf_fix VARCHAR(255),
    html_fix VARCHAR(255),
    links_anchor_fix VARCHAR(255),
    links_title_fix VARCHAR(255),
    APS_tag INT,
    UT VARCHAR(255)
    )'''
    cs1.execute(query)
        # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    conn.commit()
    # 关闭cursor对象
    cs1.close()
        # 关闭connection对象
    conn.close()
def APS_updatedownload(key):
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi from [BP_Extension].[dbo].[APS_Edsug]"
    df_utnull = pd.read_sql(query,con=conn)
    lst_doi = list(df_utnull['doi'])
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    # 关闭connection对象
    conn.close()
    tag = 0
    # 创建connection连接
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
            if dic['doi'] not in lst_doi:
                lst_doi.append(dic['doi'])
                lst_dic.append(dic)
            else:
                tag = 1
                break
        if tag == 1:
            print('无新纪录')
            break
        num_finish = len(lst_dic)
        print('已完成',num_finish,'篇','percent: {:.2%}'.format(float(num_finish)/float(num_papers)))
    print('爬取完毕')
    print(len(lst_dic))
    return(lst_dic)

def APSprocess(lst_dic):
    '''
    输入数据字典列表
    '''
    print('开始数据处理')
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
    def Clean(x):
        processed_x = ''
        try:
            processed_x = BeautifulSoup(x, 'lxml').text
        except:
            1
        return processed_x
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
 

    df['links_url'] = df['links'].apply(f_url)
    df['links_anchor'] = df['links'].apply(f_anchor)
    df['links_title'] = df['links'].apply(f_title)
    df['links_anchor_fix'] = df['links_anchor'].apply(Clean)
    df['links_title_fix'] = df['links_title'].apply(Clean)

    #直接将links扩展为三列，links_url,links_anchor,links_title

    df['link_fix'] = 'https://journals.aps.org' + df['link']
    df['summary_fix'] = df['summary'].apply(Clean)
    df['teaser_fix'] = df['teaser'].apply(Clean)
    df['title_fix'] = df['title'].apply(Clean)
    df['pdf_fix'] = 'https://journals.aps.org' + df['pdf']
    df['html_fix'] = 'https://journals.aps.org' + df['html']

    for col in df.columns:
        if col != 'len_links' or col != 'score':
            df[col] = df[col].astype('str')
    print('数据处理完成')

    return df

def APSuploadData(df,key):
    conn = create_engine('mssql+pymssql://'+ key.sql.username +':' + key.sql.password+ '@' + key.sql.host+ '/BP_Extension')
    dtypedict = {
    #'actions': Text(),
    'id': NVARCHAR(length=255),
    '[index]': NVARCHAR(length=255),
    '[type]': NVARCHAR(length=255),
    'link': Text(),
    'title': Text(),
    'date': NVARCHAR(length=255),
    'date_label': NVARCHAR(length=255),
    'features': NVARCHAR(length=255),
    'score': FLOAT(),
    'citation': NVARCHAR(length=255),
    'journal': NVARCHAR(length=255),
    'doi': NVARCHAR(length=255),
    'authors': Text(),
    'summary': Text(),
    'teaser': Text(),
    'image': NVARCHAR(length=255),
    'links': Text(),
    'subject_areas': Text(),
    'citation_count_text':NVARCHAR(length=255),
    'pdf': NVARCHAR(length=255),
    'html': NVARCHAR(length=255),
    'len_links': FLOAT(),
    'links_url': NVARCHAR(length=255),
    'links_anchor': NVARCHAR(length=255),
    'links_title': Text(),
    'link_fix': NVARCHAR(length=255),
    'summary_fix': Text(),
    'teaser_fix': Text(),
    'title_fix': Text(),
    'pdf_fix': NVARCHAR(length=255),
    'html_fix': NVARCHAR(length=255),
    'links_anchor_fix': NVARCHAR(length=255),
    'links_title_fix': NVARCHAR(length=255),
    'APS_tag': INT(),
    'UT': NVARCHAR(length=255)
    }
    df.to_sql(name='APS_Edsug', con=conn, if_exists='append', index=False, dtype=dtypedict)
    conn.dispose()

def QueryGener_APS(key):
    print('开始生成检索式')
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi,title,UT from [BP_Extension].[dbo].[APS_Edsug] where UT = '' or UT = 'nan' or UT is NULL"
    df = pd.read_sql(query,con=conn)
    conn.close()
    query = ''
    for i in range(len(df)):
        queryi = 'DO = (' + df.iloc[i]['doi'] + ')'
        if i == 0:
            query = queryi
            continue
        query = query + ' OR ' + queryi

    newfile = './Query_APS.txt'
    with open(newfile,'w') as f:
        f.write(query)
    print('检索式生成完成')
def Updatewos_APS(df_all):
    try:
        df_all['doi'] = df_all['DOI'].astype('str')
        df_all['UT'] = df_all['UT (Unique ID)'].astype('str')
    except:
        df_all['doi'] = df_all['doi'].astype('str')
        df_all['UT'] = df_all['UT'].astype('str')
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    # 获取cursor对象
    cs1 = conn.cursor()
    for i in range(len(df_all)):
        query = "update [BP_Extension].[dbo].[APS_Edsug] set UT = '" + df_all.iloc[i]['UT'] +"' where doi = '" + df_all.iloc[i]['doi'] +"'"
        cs1.execute(query)
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    conn.commit()
    # 关闭cursor对象
    cs1.close()
    # 关闭connection对象
    conn.close()
    # 创建connection连接
    print('完成更新，共',len(df_all),'条记录')

def CheckAPS():
    conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
    query = "select doi,title_fix,UT from [BP_Extension].[dbo].[APS_Edsug] where UT = '' or UT = 'nan' or UT is NULL"
    df_utnull = pd.read_sql(query,con=conn)
    # 提交之前的操作，如果之前已经执行多次的execute，那么就都进行提交
    # 关闭connection对象
    conn.close()
    # 创建connection连接
    df_utnull = df_utnull[['doi','UT','title_fix']]
    print('仍有',len(df_utnull),'条空记录请检查aps_null.csv文件')
    df_utnull.to_csv(r'./aps_null.csv',index = False)
def Backup(text):
    timenow = datetime.datetime.now().strftime('%Y-%m-%d')
    if text == 'ACS':
        conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
        query = "select * from [BP_Extension].[dbo].[ACS_Edsug]"
        df = pd.read_sql(query,con=conn)
        conn.close()
        df.to_csv('./Backup/ACSbackup' + timenow + '.csv',index = False)
    if text =='APS':
        conn = pymssql.connect(host=key.sql.host, port=key.sql.port ,user=key.sql.username, password=key.sql.password)
        query = "select * from [BP_Extension].[dbo].[APS_Edsug]"
        df = pd.read_sql(query,con=conn)
        conn.close()
        df.to_csv('./Backup/ApSbackup' + timenow + '.csv',index = False)       

if __name__ == '__main__':
    ACS()
    APS()