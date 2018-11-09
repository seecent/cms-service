
from __future__ import absolute_import

from config import db
from hug.exceptions import StoreKeyNotFound
from log import logger
from models.organization import organizations, OrgType

from sqlalchemy.sql import select


class OrganizationCache:

    def __init__(self):
        self._data = {}

    def init_cache(self):
        """
        初始化组织机构缓存
        """
        logger.info('<init_cache> start....')
        db.connect()
        self._init_org_cache(db, self._data, OrgType.Company)
        self._init_org_cache(db, self._data, OrgType.Branch)
        self._init_org_cache(db, self._data, OrgType.Department)
        db.close()
        logger.info('<init_cache> end!')

    def _init_org_cache(self, db, org_dict, org_type):
        """
        初始化组织机构缓存
        """
        t = organizations.alias('t')
        query = select([t.c.id, t.c.code, t.c.name,
                        t.c.parent_id, t.c.org_type])
        query = query.where(t.c.org_type == org_type)
        rows = db.execute(query).fetchall()
        for r in rows:
            oid = r[0]
            pid = r[3]
            code = r[1]
            name = r[2]
            otype = r[4]
            org = org_dict.get(oid)
            if org is None:
                org_dict[oid] = {'id': oid, 'code': code, 'name': name,
                                 'type': otype, 'parent_id': pid}
            if pid is not None:
                parent = org_dict.get(pid)
                if parent is not None:
                    if OrgType.Department == org_type:
                        dcodes = parent.get('dcodes')
                        if dcodes:
                            dcodes.append(code)
                        else:
                            dcodes = []
                            dcodes.append(code)
                            parent['dcodes'] = dcodes
                    else:
                        ccodes = parent.get('ccodes')
                        if ccodes:
                            ccodes.append(code)
                        else:
                            ccodes = []
                            ccodes.append(code)
                            parent['ccodes'] = ccodes
        return org_dict

    def get_org(self, orgid):
        """
        根据组织机构ID从缓存获取组织机构信息。

        :param orgid: 组织机构ID
        :retrun : 组织机构信息
        """
        d = self._data.get(orgid)
        if d:
            org_type = d['type']
            if org_type == OrgType.Department:
                company = None
                parent_id = d['parent_id']
                if parent_id is not None:
                    company = self._lookup_company()
                if company is not None:
                    return {'id': id, 'org_type': org_type,
                            'ccode': company['code'], 'cname': company['name'],
                            'dcode': d['code'], 'dname': d['name']}
                else:
                    return {'id': id, 'org_type': org_type,
                            'ccode': None, 'cname': None,
                            'dcode': d['code'], 'dname': d['name']}
            else:
                return {'id': d['id'], 'org_type': org_type,
                        'ccode': d['code'], 'cname': d['name'],
                        'dcode': None, 'dname': None}
        return None

    def get_org_code(self, orgid):
        """
        根据组织机构ID从缓存获取组织机构编码。

        :param orgid: 组织机构ID
        :retrun : 组织机构编码
        """
        d = self._data.get(orgid)
        if d:
            return d['code']
        return None

    def get_org_name(self, orgid):
        """
        根据组织机构ID从缓存获取组织机构名称。

        :param orgid: 组织机构ID
        :retrun : 组织机构称
        """
        d = self._data.get(orgid)
        if d:
            return d['code']
        return None

    def get_ccodes(self, orgid, qcode=None):
        """
        根据组织机构ID从缓存获取公司编码列表。

        :param orgid: 组织机构ID
        :retrun : 组织机构信息
        """
        if orgid is None:
            return None
        d = self._data.get(orgid)
        if d:
            org_type = d['type']
            if org_type != OrgType.Department:
                code = d['code']
                codes = [code]
                ccodes = d.get('ccodes')
                if ccodes:
                    codes.extend(ccodes)
                if qcode is not None:
                    if type(qcode) == list:
                        return filter(lambda c: c in codes, qcode)
                    else:
                        if qcode in codes:
                            return [qcode]
                else:
                    return codes
            else:
                parent_id = d['parent_id']
                if parent_id is not None:
                    company = self._lookup_company(parent_id)
                    ccode = company['code']
                    return [ccode]
        return None

    def get_dcodes(self, orgid, qcode=None):
        """
        根据组织机构ID从缓存获取部门编码列表。

        :param orgid: 组织机构ID
        :retrun : 部门编码列表
        """
        if orgid is None:
            return None
        d = self._data.get(orgid)
        if d:
            org_type = d['type']
            if org_type == OrgType.Department:
                code = d['code']
                codes = [code]
                dcodes = d.get('dcodes')
                if dcodes:
                    codes.extend(dcodes)
                if qcode is not None:
                    if type(qcode) == list:
                        return filter(lambda c: c in codes, qcode)
                    else:
                        if qcode in codes:
                            return [qcode]
                else:
                    return codes
        return None

    def _lookup_company(self, orgid):
        """
        根据组织机构ID查找公司信息。

        :param orgid: 根据组织机构ID
        :retrun : 公司信息
        """
        d = self._data.get(orgid)
        if d:
            org_type = d['type']
            if org_type != OrgType.Department:
                return d
            else:
                parent_id = d['parent_id']
                if parent_id is not None:
                    return self._lookup_company(parent_id)
        return None

    def get(self, key):
        try:
            data = self._data.get(key)
        except KeyError:
            raise StoreKeyNotFound(key)
        return data

    def exists(self, key):
        """Return whether key exists or not."""
        return key in self._data

    def set(self, key, data):
        """Set data object for given store key."""
        self._data[key] = data

    def delete(self, key):
        """Delete data for given store key."""
        if key in self._data:
            del self._data[key]
