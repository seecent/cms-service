
from __future__ import absolute_import


# 根据去重主键合并数据，去除重复记录, 每条记录为字典
def merge_datalist(unique_keys, datas):
    merged_datas = []
    score_map = {}
    index = 0
    for d in datas:
        m_key = ''
        for k, v in d.items():
            if k in unique_keys:
                m_key = m_key + str(v) + '@'
        dqs = _data_quality_score(d)
        if m_key in score_map.keys():
            m = score_map[m_key]
            if dqs > m['dqs']:
                m['dqs'] = dqs
                score_map[m_key] = m
                merged_datas.insert(m['index'], d)
        else:
            score_map[m_key] = {'dqs': dqs, 'index': index}
            merged_datas.insert(index, d)
            index = index + 1
    return merged_datas


# 数据质量打分，字段值空值越多评分越低(字典)
def _data_quality_score(data):
    score = 0
    for k, v in data.items():
        if v is not None:
            score = score + 1
            if type(v) == str and v.strip() != '':
                score = score + 1
    return score


# 根据去重主键合并数据，去除重复记录
def merge_rows(unique_keys, titles, rows):
    merged_rows = []
    score_map = {}
    index = 0
    for r in rows:
        d = r['data']
        m_key = ''
        for k in unique_keys:
            t_index = titles.index(k)
            if t_index != -1:
                v = d[t_index]
                m_key = m_key + str(v) + '@'
        dqs = _row_quality_score(d)
        if m_key in score_map.keys():
            m = score_map[m_key]
            if dqs > m['dqs']:
                m['dqs'] = dqs
                score_map[m_key] = m
                merged_rows.insert(m['index'], r)
        else:
            score_map[m_key] = {'dqs': dqs, 'index': index}
            merged_rows.insert(index, r)
            index = index + 1
    return merged_rows


# 数据质量打分，字段值空值越多评分越低(数组)
def _row_quality_score(row):
    score = 0
    for v in row:
        if v is not None:
            score = score + 1
            if type(v) == str and v.strip() != '':
                score = score + 1
    return score
