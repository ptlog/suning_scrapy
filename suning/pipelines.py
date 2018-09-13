# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re

from pymongo import MongoClient

class SuningPipeline(object):

    def open_spider(self, spider):
        '''连接本地monggodb客户端'''
        # 使用open_spider 目的是， scrapy框架一开始会启用open_spider这个方法， 只执行一次，
        # 目的是为了存储信息的时候，不会反复的打开连接数据库
        client = MongoClient()
        self.collection = client['suning']['book']

    def process_item(self, item, spider):
        # item['content_profile'] = self.process_content(item['content_profile'])
        item['book_name'] = self.process_book_name(item['book_name'])
        if item['author'] is not None:
            item['author'] = self.process_book_name(item['author'])
        # print(item)
        # print('\n'*2)
        if item['content_profile'] is not None:
            item['content_profile'] = self.process_content(item['content_profile'])
        # return item
        # print(item)
        # print('\n'*2)
        print('done!!')
        # 把item存入mongodb中
        self.collection.insert(item)

    def process_content(self, content):
        '''这里处理内容简介中的内容'''
        # print(type(content))
        content = ''.join(content)
        content = re.sub(r'\xa0\xa0','',content)
        return content
    #
    def process_book_name(self, book_name):
        '''这里处理书名和作者的名字，都可以处理'''
        book_name = re.sub(r'\r\n\t\t\t\t\t\t|\s|[|]', '', book_name)
        return book_name

