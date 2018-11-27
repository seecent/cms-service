from __future__ import absolute_import

import requests
import time

from api.errorcode import ErrorCode
from config import setting
from log import logger
from plugins.weixin.models.wxaccount import wxaccounts
from models import row2dict


class WxAccountService:

    def refresh_access_token(self, db, account_id):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            logger.info('<refresh_access_token> account_id: ' +
                        str(account_id))
            row = db.get(wxaccounts, account_id)
            if row:
                account = row2dict(row, wxaccounts)
                effective_time = account['effective_time']
                now = int(time.time())
                if effective_time is not None and effective_time > now:
                    pass
                else:
                    logger.info('<refresh_access_token> account: ' +
                                account['name'])
                    appid = account['app_id']
                    secret = account['app_secret']
                    api_url = setting['weixin_api_url'] + \
                        "token?grant_type=client_credential&"
                    api_url += "appid={0}&secret={1}".format(appid, secret)
                    headers = {
                        "Content-Type": "application/json;charset=UTF-8"}
                    res = requests.post(api_url, headers=headers)
                    logger.info('<refresh_access_token> status_code: ' +
                                str(res.status_code))
                    if res.status_code == 200:
                        logger.info('<refresh_access_token> res json: ' +
                                    str(res.json()))
                        data = res.json()
                        if "access_token" in data:
                            effect_time = now + data['expires_in']
                            access_token = data['access_token']
                            account['effective_time'] = effect_time
                            account['access_token'] = access_token
                            data = {'id': account_id,
                                    'access_token': access_token,
                                    'refresh_time': now,
                                    'effective_time': effect_time}
                            db.update(wxaccounts, data)
                        else:
                            # result['code'] = ErrorCode.API_FAILURE.value
                            result['code'] = data.get('errcode')
                            result['message'] = data.get('errmsg')
                    else:
                        result['code'] = ErrorCode.API_FAILURE.value
                        result['message'] = ErrorCode.API_FAILURE.name
                result['account'] = account
            else:
                result['code'] = ErrorCode.NOT_FOUND.value
                result['message'] = ErrorCode.NOT_FOUND.name
        except Exception:
            logger.exception('<refresh_access_token> account_id: ' +
                             str(account_id) + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = ErrorCode.EXCEPTION.name

        return result
