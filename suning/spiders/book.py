# -*- coding: utf-8 -*-
import scrapy
import re
import json
from copy import deepcopy


class BookSpider(scrapy.Spider):
    name = 'book'
    # allowed_domains = ['suning.com']
    allowed_domains = ['suning.com']
    start_urls = ['http://book.suning.com/']

    def parse(self, response):
        '''获取菜单栏中的每个分类'''
        # 这里只获取了7个分类， 为了使能够描述清楚代码就不在过多的获取更多的分类， 不过原理都是一样的
        # 通过xpath来获取每个div_item, 通过浏览器检查，和response的相应进行对比
        div_list = response.xpath("//div[@class='menu-item']")

        sub_div_list = response.xpath("//div[@class='menu-sub']|//div[@class='menu-sub menu-sub-down']")
        # len_div = len(div_list)
        for i in range(7):
            item = {}
            item['b_cate_title'] = div_list[i].xpath(".//h3/a/text()").extract_first()

            p_list = sub_div_list[i].xpath(".//div[@class='submenu-left']/p")

            for p in p_list:
                # 获取大分类中的每个小分类的名字
                item['s_cate_title'] = p.xpath("./a/text()").extract_first()
                # 链接
                item['s_cate_title_href'] = p.xpath("./a/@href").extract_first()
                # 获取每个分类的Id, 目的是为了下面的分页跳转起作用
                categoryId = re.match(r'https://list.suning.com/1-(.*?)-0.html', item['s_cate_title_href']).group(1)
                if categoryId == '262504-0-0-0':
                    categoryId = re.sub(r'-0-0-0','',categoryId)

                item['s_categoryId'] = int(categoryId)
                item['s_cate_title_href'] = item['s_cate_title_href'] + '#second-filter'
                print('categoryId', item['s_categoryId'])

                # 访问每个小分类中的书本列表页面
                yield scrapy.Request(
                    item['s_cate_title_href'],callback=self.parse_booklist,meta=deepcopy({'item':deepcopy(item)})
                )

    def parse_booklist(self, response):
        '''获取每个分类中的列表中的书籍信息'''
        print('-------')
        item = deepcopy(response.meta['item'])
        li_list = response.xpath("//div[@id='filter-results']/ul/li")

        # 获取每个细分的分类页面中的所有的列表的书的信息
        for li in li_list:
            # 获取图片
            item['img'] = li.xpath(".//div[@class='wrap']/div[@class='res-img']//a/img/@src").extract_first()
            if item['img'] is None:
                item['img'] = 'https:'+li.xpath(".//div[@class='wrap']/div[@class='res-img']//a/img/@src2").extract_first()
            else:
                item['img'] = 'https:'+item['img']
            # 获取书本的详情页面的url
            item['book_href'] = 'https:'+li.xpath(".//div[@class='wrap']/div[@class='res-img']//a/@href").extract_first()
            # 把书本的详情页面的url传递给调度器， 并以Request对象的形式传递
            yield scrapy.Request(item['book_href'], callback=self.parse_book_info, meta={'item':deepcopy(item)})

        # 获取当前页码
        current_page = re.findall(r"param\.currentPage = (.*?);",response.body.decode())
        # 获取总页码
        page_Numbers = re.findall(r"param\.pageNumbers = (.*?);",response.body.decode())
        # 获取到每个细分分类的Id, 要对下一页进行访问时， 必须需要这个分类Id, 可以查看通过浏览器查看得出
        categoryId = item['s_categoryId']

        current_page = int(eval(current_page[0]))
        page_Numbers = int(eval(page_Numbers[0]))
        current_page = current_page + 1

        if current_page < page_Numbers:
            # 当当前页小于总页数时
            # 访问下一页
            url = 'https://list.suning.com/1-{ca}-{cp}-0-0-0-0-0-0-4.html'.format(ca=categoryId,cp=current_page)
            yield scrapy.Request(url, callback=self.parse_booklist, meta={'item':response.meta['item']})

    def parse_book_info(self, response):
        '''获取每本书的信息'''
        item = response.meta['item']
        # 获取书名
        item['book_name'] = response.xpath("//div[@class='proinfo-title']/h1/text()").extract_first()
        # 获取作者
        item['author'] = response.xpath("//ul[@class='bk-publish clearfix']/li[1]/text()").extract_first()
        # 获取内容简介
        item['content_profile'] = response.xpath("//dl[@moduleid='bookCon_5']/dd/p//text()").extract()
        # 获取到partNumber和vendorCode的信息, 用于获取书本的价格, 研究浏览器中的每个响应会发现获取价格必须需要这两个元素
        partNumber = re.findall(r"\"partNumber\":(.*?),",response.body.decode())
        item['partNumber'] = eval(partNumber[0])
        vendorCode = re.findall(r"\"vendorCode\":(.*?),",response.body.decode())
        item['vendorCode'] = eval(vendorCode[0])

        # 访问获取价格的等信息的url
        url = 'http://rec.suning.com/show/find/queryGoodsPrice.do?cmmdtyCode={partNumber}&cityId=025&type=1&type2=&vendorId={vendorCode}'.format(partNumber=item['partNumber'],vendorCode=item['vendorCode'])
        yield scrapy.Request(url,callback=self.parse_book_price,meta={'item':deepcopy(item)})

    def parse_book_price(self, response):
        '''获取书籍的价格'''
        item = response.meta['item']
        str_content = response.body.decode()
        list_content = eval(str_content)
        dict_content = list_content[0]
        # 获取原价
        item['refPrice'] = dict_content['refPrice']
        # 获取苏宁易购价
        item['snPrice'] = dict_content['snPrice']
        # 把item通过引擎抛给pipline
        yield item



