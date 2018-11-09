import traceback
import hug
from falcon import HTTPInternalServerError, HTTPError
from config import setting, dataSources, db
from api.collect import progress

app = hug.API(__name__)
app.http.add_middleware(hug.middleware.CORSMiddleware(app, max_age='7'))
app.http.base_url = '/crontab/api'
# lms db
db.init_app(app, dataSources['lmsdb'])

app.extend(progress, '/progress')


@hug.not_found()
def not_found_handler(**kw):
    if kw:
        return {'errors': {'not_found': str(kw)}}
    else:
        if setting['lms_debug']:
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
