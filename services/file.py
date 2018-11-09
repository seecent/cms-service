
from __future__ import absolute_import

from config import setting
import codecs
import xml.etree.ElementTree as ET


# 解析CSV文件，根据unique_key去除重复数据
def parse_csv_file(filename, unique_key, chartset):
    upload_filename = setting['upload'] + filename
    data = []
    titles = []

    flag = True
    m = {}
    for count, line in enumerate(codecs.open(upload_filename, 'r', chartset)):
        if flag:
            flag = False
            titles = line.strip("\n").strip("\r").strip("\ufeff").split(',')
        else:
            count += 1
            vs = line.strip("\n").strip("\r").split(',')
            row = {'rowid': count}
            i = 0
            check_key = False
            for t in titles:
                k = t.strip('"').strip()
                v = vs[i].strip('"').strip()
                if k == unique_key:
                    if v.strip() == '':
                        break
                    if v in m.keys():
                        break
                    else:
                        check_key = True
                        m[v] = v
                row[k] = v
                i += 1
            if check_key:
                data.append(row)
    return {'filename': filename, 'total': count - 1,
            'titles': titles, 'list': data}


def page_parse_file_csv(uid, offset, limit, total, chartset):
    save_filename = uid + '.csv'
    upload_filename = setting['upload'] + save_filename
    data = []
    titles = []

    flag = True
    offset = offset + 1
    end = offset + limit
    for index, line in enumerate(codecs.open(upload_filename, 'r', chartset)):
        if flag:
            flag = False
            titles = line.strip("\n").split(',')
        else:
            if index >= offset:
                if index < end:
                    vs = line.strip("\n").split(',')
                    row = {'id': index}
                    i = 0
                    for t in titles:
                        k = t.strip('"').strip()
                        row[k] = vs[i].strip('"').strip()
                        i += 1
                    data.append(row)
                else:
                    break

    return {'uid': uid, 'total': total, 'titles': titles, 'list': data}


def parse_file_csv(uid, chartset):
    save_filename = uid + '.csv'
    upload_filename = setting['upload'] + save_filename
    data = []
    titles = []

    flag = True
    for count, line in enumerate(codecs.open(upload_filename, 'r', chartset)):
        if flag:
            flag = False
            titles = line.strip("\n").split(',')
        else:
            count += 1
            vs = line.strip("\n").split(',')
            row = {'id': count}
            i = 0
            for t in titles:
                k = t.strip('"').strip()
                row[k] = vs[i].strip('"').strip()
                i += 1
            data.append(row)
    return {'uid': uid, 'total': count - 1, 'titles': titles, 'list': data}


def count_file_lines_csv(uid):
    sfn = uid + '.csv'
    ufn = setting['upload'] + sfn
    total = 0
    try:
        total = sum(1 for x in enumerate(codecs.open(ufn, 'r', 'utf-8')))
    except Exception:
        total = sum(1 for x in enumerate(codecs.open(ufn, 'r', 'GBK')))
    if total > 0:
        total = total - 1
    return total


def count_file_lines_xml(uid):
    sfn = uid + '.xml'
    ufn = setting['upload'] + sfn
    total = 0
    try:
        tree = ET.parse(ufn)
        root = tree.getroot()
        total = len(root)
    except Exception:
        print("parse xml file fail!")
    return total


def page_parse_file_xml(uid, offset, limit, total):
    save_filename = uid + '.xml'
    upload_filename = setting['upload'] + save_filename
    data = []
    titles = 'ChannelCode,CampaignCode,CampanyCode,EnName,FirstName,\
              LastName,FullName,IDType,IDNumber,Gender,Age,BirthYear,\
              BirthMonth,BirthDay,Marriage,NumOfChilds,Education,\
              Income,MobilePhone,HomePhone,WorkPhone,Email,QQ,Weixin,\
              OpenID,IPAddress,ProvinceCode,CityCode,DistrictCode,\
              Address,Budget,Need,Authority,TimeFrame,ProductCode,\
              ProductName,LastModifed'
    titles = titles.split(',')

    offset = offset - 1
    end = offset + limit
    tree = ET.parse(upload_filename)
    root = tree.getroot()
    i = 0
    for child in root:
        if i >= offset and i <= end:
            row = {'id': i}
            row['ChannelCode'] = root[i].find('SalesChannel').find('Code').text
            row['CampaignCode'] = root[i].find('Campaign').find('Code').text
            row['CampanyCode'] = root[i].find('Campany').find('Code').text
            row['EnName'] = root[i].find('Contact').find('EnName').text
            row['FirstName'] = root[i].find('Contact').find('FirstName').text
            row['LastName'] = root[i].find('Contact').find('LastName').text
            row['FullName'] = root[i].find('Contact').find('FullName').text
            row['IDType'] = root[i].find('Contact').find('IDType').text
            row['IDNumber'] = root[i].find('Contact').find('IDNumber').text
            row['Gender'] = root[i].find('Contact').find('Gender').text
            row['Age'] = root[i].find('Contact').find('Age').text
            row['BirthYear'] = root[i].find('Contact').find('BirthYear').text
            row['BirthMonth'] = root[i].find('Contact').find('BirthMonth').text
            row['BirthDay'] = root[i].find('Contact').find('BirthDay').text
            row['Marriage'] = root[i].find('Contact').find('Marriage').text
            row['NumOfChilds'] = root[i].find('Contact')\
                                        .find('NumOfChilds').text
            row['Education'] = root[i].find('Contact').find('Education').text
            row['Income'] = root[i].find('Contact').find('Income').text
            row['MobilePhone'] = root[i].find('Contact')\
                                        .find('MobilePhone').text
            row['HomePhone'] = root[i].find('Contact').find('HomePhone').text
            row['WorkPhone'] = root[i].find('Contact').find('WorkPhone').text
            row['Email'] = root[i].find('Contact').find('Email').text
            row['QQ'] = root[i].find('Contact').find('QQ').text
            row['Weixin'] = root[i].find('Contact').find('Weixin').text
            row['OpenID'] = root[i].find('Contact').find('OpenID').text
            row['IPAddress'] = root[i].find('Contact').find('IPAddress').text
            row['ProvinceCode'] = root[i].find('Location')\
                                         .find('ProvinceCode').text
            row['CityCode'] = root[i].find('Location').find('CityCode').text
            row['DistrictCode'] = root[i].find('Location')\
                                         .find('DistrictCode').text
            row['Address'] = root[i].find('Location').find('Address').text
            row['Budget'] = root[i].find('Lead').find('Budget').text
            row['Need'] = root[i].find('Lead').find('Need').text
            row['Authority'] = root[i].find('Lead').find('Authority').text
            row['TimeFrame'] = root[i].find('Lead').find('TimeFrame').text
            row['ProductCode'] = root[i].find('Product').find('Code').text
            row['ProductName'] = root[i].find('Product').find('Name').text
            row['LastModifed'] = root[i].find('LastModifed').text

            data.append(row)
        i += 1

    return {'uid': uid, 'total': total, 'titles': titles, 'list': data}


def parse_file_xml(uid):
    save_filename = uid + '.xml'
    upload_filename = setting['upload'] + save_filename
    tree = ET.parse(upload_filename)
    root = tree.getroot()
    total = len(root)
    return page_parse_file_xml(uid, 1, total, total)
