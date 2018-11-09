
from __future__ import absolute_import

import codecs
import os.path
# from config import setting
from models.leads.activeleads import activeleads, activeleads_mapping


class CodeTool:

    def _title_case(self, text):
        SEP = ' '
        if '_' in text:
            splits = text.split('_')
            return SEP.join(list(map(lambda w: w.capitalize(), splits)))
        elif '-' in text:
            splits = text.split('-')
            return SEP.join(list(map(lambda w: w.capitalize(), splits)))
        return text[0].upper() + text[1:]

    def gcode(self):
        self.create_columns_mapping('ActiveLeads', 'activeleads', activeleads)
        self.create_collect_config_xml(
            'ActiveLeads', 'ActiveLeads', activeleads)
        self.create_i18n_message(
            'ActiveLeads', 'ActiveLeads', activeleads, activeleads_mapping)
        self.create_display_columns(
            'ActiveLeads', 'ActiveLeads', activeleads, activeleads_mapping)
        self.create_service('ActiveLeads', 'activeleads', 'activeleads')

    def save_file(self, module, filename, text, artifact=None):
        dir_name = "D:\\dev\\git\\lms\\out\\" + module
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        if artifact is not None:
            artifact_dir = dir_name + os.path.sep + artifact
            if not os.path.exists(artifact_dir):
                os.mkdir(artifact_dir)
            filename = artifact_dir + os.path.sep + filename
        else:
            filename = dir_name + os.path.sep + filename
        f = codecs.open(filename, 'w', 'utf-8')
        # f = open(filename, 'w')
        f.write(text)
        f.close()

    def create_columns_mapping(self, module, name, table):
        text = "mapping = {\n"
        for c in table.c:
            line = "    '{0}': '{1}', ".format(c.name, c.name)
            text += line + '\n'
        text += '}\n'
        self.save_file(module, name + '_mapping.txt', text)

    def create_display_columns(self, module, name, table, mapping=None):
        code = "displayColumns: {\n"
        if mapping is not None:
            for k, v in mapping.items():
                code += "      {0}: true,\n".format(k)
        else:
            for c in table.c:
                code += "      {0}: true,\n".format(c.name)
        code += "},\n"
        self.save_file(module, name + '_display_columns.js', code)

    def create_i18n_message(self, module, name, table, mapping=None):
        msg_json = "\"" + name + "\": {\n"
        if mapping is not None:
            for k, v in mapping.items():
                msg_json += "    \"{0}\": \"{1}\",\n".format(
                    k, self._title_case(k))
        else:
            for c in table.c:
                msg_json += "    \"{0}\": \"{1}\",\n".format(
                    c.name, self._title_case(c.name))
        msg_json += "},\n"
        self.save_file(module, name + '_locales.json', msg_json)

    def create_service(self, module, filename, name):
        service_template = """import { stringify } from 'qs';
import request from '../utils/request';

export async function query(params) {
  return request(`/api/{name}?${stringify(params)}`);
}

export async function create(params) {
  return request('/api/{name}', {
    method: 'POST',
    body: params,
  });
}

export async function remove(params) {
  return request(`/api/{name}/${params.id}`, {
    method: 'DELETE',
  });
}

export async function update(params) {
  return request(`/api/{name}/${params.id}`, {
    method: 'PATCH',
    body: params,
  });
}
        """
        code = service_template.replace("{name}", name)
        self.save_file(module, filename + '.js', code, 'services')

    def create_collect_config_xml(self, module, name, table):
        text = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
        text += "<{0} name=\"{1}\" table=\"{2}\">\n".\
            format(name, name.lower(), name.lower())
        text += "    <Columns>\n"
        for c in table.c:
            n = c.name
            tn = str(c.type)
            t = 'String'
            if 'INTEGER' == tn:
                t = 'Integer'
            elif 'BIGINT' == tn:
                t = 'BigInteger'
            elif 'NUMERIC' in tn:
                t = 'Integer'
            elif 'DATETIME' == tn:
                t = 'DateTime'
            text += "        " +\
                "<Column name=\"{0}\" mapping=\"{1}\" type=\"{2}\"/>\n".\
                format(n, n, t)
        text += "    </Columns>\n"
        text += "</{}>\n".format(name)
        self.save_file(module, name.lower() + '_collect_config.xml', text)
