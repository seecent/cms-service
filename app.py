import traceback
import hug
from falcon import HTTPInternalServerError, HTTPError
from cache import amscache, locationcache, orgcache
from config import setting, dataSources, db, mdb, campaign_db
from api import notification, organization,\
    collection, rawleads, saleschannel, transformrule,\
    campaign, monitorchart, monitorpanel, leadstatistic,\
    constant, department, template, operationlog,\
    menu, location, company, uploadfile
from api.auth import user, auth, role, ssoauth
from api.collect import csvimport, xmlimport, progress
from api.media import mediafolder, mediafile
from api.leads import activeleads
from api.open import customer, leads, response
from api.ams import amscso, amssso, amssales
from api.logs import logs
from plugins.weixin.api import wxaccount, wxuser, wxmedia
# from services.middleware import AuthMiddleware
from services.leadsrich import LeadsRichService

app = hug.API(__name__)
app.http.add_middleware(hug.middleware.CORSMiddleware(app, max_age='7'))
# app.http.add_middleware(AuthMiddleware(
#     auth_key='apikey', exclude_urls=['/api/auth/token', '/api/auth/logout',
#                                      '/api/scvimport/upload',
#                                      '/api/xmlimport/upload']))
app.http.base_url = '/api'
# print(app)
leadsrichservice = LeadsRichService()
# lms db
db.init_app(app, dataSources['cmsdb'])
# mdb
mdb.init_app(app, dataSources['mdb'])
# campaign db
campaign_db.init_app(app, dataSources['campaigndb'])
# init cache
amscache.init_cache()
orgcache.init_cache()
locationcache.init_cache()
# api
app.extend(auth, '/auth')
app.extend(menu, '/menus')
app.extend(role, '/roles')
app.extend(user, '/users')
app.extend(notification, '/notification')
app.extend(constant, '/constants')
app.extend(department, '/departments')
app.extend(location, '/locations')
app.extend(organization, '/organizations')
app.extend(operationlog, '/operationlogs')
app.extend(ssoauth, '/ssoauth')
app.extend(company, '/companies')
# media
app.extend(mediafolder, '/media/folders')
app.extend(mediafile, '/media/files')
# leads
app.extend(rawleads, '/rawleads')
app.extend(activeleads, '/activeleads')
app.extend(saleschannel, '/saleschannels')
app.extend(campaign, '/campaigns')
# collection
app.extend(collection, '/collections')
app.extend(csvimport, '/csvimport')
app.extend(xmlimport, '/xmlimport')
app.extend(progress, '/progress')
app.extend(monitorchart, '/monitorcharts')
app.extend(monitorpanel, '/monitorpanels')
app.extend(transformrule, '/transformrules')
app.extend(template, '/templates')
app.extend(leadstatistic, '/leadstatistic')
# open api
app.extend(leads, '/getLeads')
app.extend(customer, '/customer')
app.extend(response, '/response')
# ams
app.extend(amscso, '/amscsos')
app.extend(amssso, '/amsssos')
app.extend(amssales, '/amssales')
# logs
app.extend(logs, '/logs')
# upload
app.extend(uploadfile, '/upload')
# weixin
app.extend(wxaccount, '/wxaccounts')
app.extend(wxuser, '/wxusers')
app.extend(wxmedia, '/wxmedias')
# @hug.extend_api()
# def with_other_apis():
#     return [user]


@hug.not_found()
def not_found_handler(**kw):
    if kw:
        return {'errors': {'not_found': str(kw)}}
    else:
        if setting['cms_debug']:
            return app.http.documentation_404()
        else:
            return {'errors': {'not_found': str(kw)}}


@hug.exception((HTTPError, ))
def handle_falcon_exceptions(exception):
    raise exception


@hug.exception(Exception)
def handle_exception(exception):
    args = exception.args
    if not args:
        args = (str(exception),)
    traceback.print_exc()
    raise HTTPInternalServerError(title='internal_error',
                                  description=args[0])


@hug.cli()
def init_user():
    department.init_departments()
    menu.init_menus()
    role.init_roles()
    user.init_users()
    # campaignserver.init_campaignservers()
    # uauser.init_uausers()


@hug.cli()
def init_data():
    saleschannel.init_sales_channels()
    campaign.init_campaigns()
    template.init_templates()
    constant.init_constants()
    location.init_locations()
    organization.init_organizations()
    company.init_companies()


@hug.cli()
def init_organizations():
    organization.init_organizations()


@hug.cli()
def init_companies():
    company.init_companies()


@hug.cli()
def init_rule():
    transformrule.init_transformrule()


@hug.cli()
def init_test_data():
    activeleads.init_test_data()


@hug.cli()
def init_media():
    mediafolder.init_folders()


@hug.cli()
def init_wxaccount():
    wxaccount.init_wxaccounts()


@hug.cli()
def sync_wxusers():
    wxuser.sync_all_wxusers()


@hug.cli()
def sync_wxmedias():
    # wxmedia.sync_all_wxmedias()
    wxmedia.sync_all_wxmeida_images()


@hug.cli()
def init_ams_data():
    amscso.init_amscsos()
    amssso.init_amsssos()
    amssales.init_amssales()


@hug.cli()
def rich_leads(cid: hug.types.number):
    leadsrichservice.rich_raw_leads(cid)


if __name__ == '__main__':
    init_user.interface.cli()
    init_data.interface.cli()
