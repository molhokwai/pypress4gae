#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of web2py Web Framework (Copyrighted, 2007-2009).
Developed by Massimo Di Pierro <mdipierro@cs.depaul.edu>.
License: GPL v2

Holds:

- SQLFORM: provide a form for a table (with/without record)
- SQLTABLE: provides a table for a set of records
- form_factory: provides a SQLFORM for an non-db backed table

"""

from http import HTTP
from html import *
from validators import *
from sql import SQLDB, Table, KeyedTable, Row
from storage import Storage

import logging
import urllib
import re
import sys
import os
import cStringIO
import copy
import base64

table_field = re.compile('[\w_]+\.[\w_]+')


class FormWidget(object):
    """
    helper for SQLFORM to generate form input fields (widget),
    related to the fieldtype
    """

    @staticmethod
    def _attributes(field, widget_attributes, **attributes):
        """
        helper to build a common set of attributes

        :param field: the field involved, some attributes are derived from this
        :param widget_attributes:  widget related attributes
        :param attributes: any other supplied attributes
        """
        attr = dict(
            _id = '%s_%s' % (field._tablename, field.name),
            _class = field.type,
            _name = field.name,
            requires = field.requires,
            )
        attr.update(widget_attributes)
        attr.update(attributes)
        return attr

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates the widget for the field.

        When serialized, will provide an INPUT tag:

        - id = tablename_fieldname
        - class = field.type
        - name = fieldname

        :param field: the field needing the widget
        :param value: value
        :param attributes: any other attributes to be applied
        """

        raise NotImplementedError


class StringWidget(FormWidget):

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates an INPUT text tag.

        see also: :meth:`FormWidget.widget`
        """

        default = dict(
            _type = 'text',
            value = (value!=None and str(value)) or '',
            )
        attr = StringWidget._attributes(field, default, **attributes)

        return INPUT(**attr)


class IntegerWidget(StringWidget):

    pass


class DoubleWidget(StringWidget):

    pass


class TimeWidget(StringWidget):

    pass


class DateWidget(StringWidget):

    pass


class DatetimeWidget(StringWidget):

    pass


class TextWidget(FormWidget):

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates a TEXTAREA tag.

        see also: :meth:`FormWidget.widget`
        """

        default = dict(
            value = value,
            )
        attr = TextWidget._attributes(field, default, **attributes)

        return TEXTAREA(**attr)


class BooleanWidget(FormWidget):

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates an INPUT checkbox tag.

        see also: :meth:`FormWidget.widget`
        """

        default=dict(
            _type='checkbox',
            value=value,
            )
        attr = BooleanWidget._attributes(field, default, **attributes)

        return INPUT(**attr)


class OptionsWidget(FormWidget):

    @staticmethod
    def has_options(field):
        """
        checks if the field has selectable options

        :param field: the field needing checking
        :returns: True if the field has options
        """

        return hasattr(field.requires, 'options')\
             or isinstance(field.requires, IS_EMPTY_OR)\
             and hasattr(field.requires.other, 'options')

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates a SELECT tag, including OPTIONs (only 1 option allowed)

        see also: :meth:`FormWidget.widget`
        """

        default = dict(
            value=value,
            )
        attr = OptionsWidget._attributes(field, default, **attributes)

        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            requires0 = requires[0]
            if isinstance(requires0, IS_EMPTY_OR)\
                    and hasattr(requires0.other, 'options'):
                opts = [OPTION(_value='')]
                options = requires0.other.options()
            elif hasattr(requires0, 'options'):
                opts = []
                options = requires0.options()
            else:
                raise SyntaxError, 'widget cannot determine options of %s' \
                    % field
        opts += [OPTION(v, _value=k) for (k, v) in options]

        return SELECT(*opts, **attr)


class MultipleOptionsWidget(OptionsWidget):

    @staticmethod
    def widget(field, value, size=5, **attributes):
        """
        generates a SELECT tag, including OPTIONs (multiple options allowed)

        see also: :meth:`FormWidget.widget`

        :param size: optional param (default=5) to indicate how many rows must
            be shown
        """

        attributes.update(dict(_size=size, _multiple=True))

        return OptionsWidget.widget(field, value, **attributes)


class RadioWidget(OptionsWidget):

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates a TABLE tag, including INPUT radios (only 1 option allowed)

        see also: :meth:`FormWidget.widget`
        """

        attr = OptionsWidget._attributes(field, {}, **attributes)

        if isinstance(field.requires, IS_EMPTY_OR)\
             and hasattr(field.requires.other, 'options'):
            opts = [TR(INPUT(_type='radio', _name=field.name,
                             _value='', value=value), '')]
            options = field.requires.other.options()
        elif hasattr(field.requires, 'options'):
            opts = []
            options = field.requires.options()
        else:
            raise SyntaxError, 'widget cannot determine options of %s' % field
        opts += [TR(INPUT(_type='radio', _name=field.name,
                          requires=attr.get('requires',None),
                          _value=k, value=value), v) for (k, v) in options]
        return TABLE(*opts, **attr)


class CheckboxesWidget(OptionsWidget):

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates a TABLE tag, including INPUT checkboxes (multiple allowed)

        see also: :meth:`FormWidget.widget`
        """

        values = re.compile('[\w\-:]+').findall(str(value))

        attr = OptionsWidget._attributes(field, {}, **attributes)

        if hasattr(field.requires, 'options'):
            opts = []
            options = field.requires.options()
        else:
            raise SyntaxError, 'widget cannot determine options of %s' % field

        opts += [TR(INPUT(_type='checkbox', _name=field.name,
                          requires=attr.get('requires',None),
                          _value=k, value=(k in values)), v) \
                     for (k, v) in options]
        return TABLE(*opts, **attr)


class PasswordWidget(FormWidget):

    DEFAULT_PASSWORD_DISPLAY = 8*('*')

    @staticmethod
    def widget(field, value, **attributes):
        """
        generates a INPUT password tag.
        If a value is present it will be shown as a number of '*', not related
        to the length of the actual value.

        see also: :meth:`FormWidget.widget`
        """

        default=dict(
            _type='password',
            _value=(value and PasswordWidget.DEFAULT_PASSWORD_DISPLAY) or '',
            )
        attr = PasswordWidget._attributes(field, default, **attributes)

        return INPUT(**attr)


class UploadWidget(FormWidget):

    DEFAULT_WIDTH = '150px'
    ID_DELETE_SUFFIX = '__delete'
    GENERIC_DESCRIPTION = 'file'

    @staticmethod
    def widget(field, value, download_url=None, **attributes):
        """
        generates a INPUT file tag.

        Optionally provides an A link to the file, including a checkbox so
        the file can be deleted.
        All is wrapped in a DIV.

        see also: :meth:`FormWidget.widget`

        :param download_url: Optional URL to link to the file (default = None)
        """

        default=dict(
            _type='file',
            )
        attr = UploadWidget._attributes(field, default, **attributes)

        inp = INPUT(**attr)

        if download_url and value:
            url = download_url + '/' + value
            (br, image) = ('', '')
            if UploadWidget.is_image(value):
                (br, image) = \
                    (BR(), IMG(_src = url, _width = UploadWidget.DEFAULT_WIDTH))
            inp = DIV(inp, '[',
                      A(UploadWidget.GENERIC_DESCRIPTION, _href = url), '|',
                      INPUT(_type='checkbox',
                            _name=field.name + UploadWidget.ID_DELETE_SUFFIX),
                      'delete]', br, image)
        return inp

    @staticmethod
    def represent(field, value, download_url=None):
        """
        how to represent the file:

        - with download url and if it is an image: <A href=...><IMG ...></A>
        - otherwise with download url: <A href=...>file</A>
        - otherwise: file

        :param field: the field
        :param value: the field value
        :param download_url: url for the file download (default = None)
        """

        inp = UploadWidget.GENERIC_DESCRIPTION

        if download_url and value:
            url = download_url + '/' + value
            if UploadWidget.is_image(value):
                inp = IMG(_src = url, _width = UploadWidget.DEFAULT_WIDTH)
            inp = A(inp, _href = url)

        return inp

    @staticmethod
    def is_image(value):
        """
        Tries to check if the filename provided references to an image

        Checking is based on filename extension. Currently recognized:
           gif, png, jp(e)g, bmp

        :param value: filename
        """

        extension = value.split('.')[-1].lower()
        if extension in ['gif', 'png', 'jpg', 'jpeg', 'bmp']:
            return True
        return False


class SQLFORM(FORM):

    """
    SQLFORM is used to map a table (and a current record) into an HTML form

    given a SQLTable stored in db.table

    generates an insert form::

        SQLFORM(db.table)

    generates an update form::

        record=db(db.table.id==some_id).select()[0]
        SQLFORM(db.table, record)

    generates an update with a delete button::

        SQLFORM(db.table, record, deletable=True)

    if record is an int::

        record=db(db.table.id==record).select()[0]

    optional arguments:

    :param fields: a list of fields that should be placed in the form,
        default is all.
    :param labels: a dictionary with labels for each field, keys are the field
        names.
    :param col3: a dictionary with content for an optional third column
            (right of each field). keys are field names.
    :param linkto: the URL of a controller/function to access referencedby
        records
            see controller appadmin.py for examples
    :param upload: the URL of a controller/function to download an uploaded file
            see controller appadmin.py for examples

    any named optional attribute is passed to the <form> tag
            for example _class, _id, _style, _action, _method, etc.

    """

    # usability improvements proposal by fpp - 4 May 2008 :
    # - correct labels (for points to field id, not field name)
    # - add label for delete checkbox
    # - add translatable label for record ID
    # - add third column to right of fields, populated from the col3 dict

    widgets = Storage(dict(
        string = StringWidget,
        text = TextWidget,
        password = PasswordWidget,
        integer = IntegerWidget,
        double = DoubleWidget,
        time = TimeWidget,
        date = DateWidget,
        datetime = DatetimeWidget,
        upload = UploadWidget,
        boolean = BooleanWidget,
        blob = None,
        options = OptionsWidget,
        multiple = MultipleOptionsWidget,
        radio = RadioWidget,
        checkboxes = CheckboxesWidget,
        ))

    FIELDNAME_REQUEST_DELETE = 'delete_this_record'
    FIELDKEY_DELETE_RECORD = 'delete_record'

    def __init__(
        self,
        table,
        record = None,
        deletable = False,
        linkto = None,
        upload = None,
        fields = None,
        labels = None,
        col3 = {},
        submit_button = 'Submit',
        delete_label = 'Check to delete:',
        showid = True,
        readonly = False,
        comments = True,
        keepopts = [],
        ignore_rw = False,
        **attributes
        ):
        """
        SQLFORM(db.table,
               record=None,
               fields=['name'],
               labels={'name': 'Your name'},
               linkto=URL(r=request, f='table/db/')
        """
        
        ID_LABEL_SUFFIX = 'label'
        ID_ROW_SUFFIX = 'row'

        self.ignore_rw = ignore_rw
        nbsp = XML('&nbsp;') # Firefox2 does not display fields with blanks
        FORM.__init__(self, *[], **attributes)
        ofields = fields
        keyed = isinstance(table,KeyedTable)

        # if no fields are provided, build it from the provided table
        # will only use writable or readable fields, unless forced to ignore
        if fields == None:
            fields = [f for f in table.fields if \
                      ignore_rw or table[f].writable or table[f].readable]
        self.fields = fields

        # make sure we have an id
        if not 'id' in self.fields and isinstance(table,Table) and not keyed:
            self.fields.insert(0, 'id')

        self.table = table

        # try to retrieve the indicated record using its id
        # otherwise ignore it
        if record and isinstance(record, (int, long, str, unicode)):
            records = table._db(table.id == record).select()
            if records:
                record = records[0]
            else:
                raise HTTP(404, "Object not found")
        self.record = record

        self.record_id = None
        if keyed:
            if record:
                self.record_id = dict([(k,record[k]) for k in table._primarykey])
            else:
                self.record_id = dict([(k,None) for k in table._primarykey])
        self.trows = {}
        xfields = []
        self.fields = fields
        self.custom = Storage()
        self.custom.dspval = Storage()
        self.custom.inpval = Storage()
        self.custom.label = Storage()
        self.custom.comment = Storage()
        self.custom.widget = Storage()
        self.custom.linkto = Storage()

        for fieldname in self.fields:
            if fieldname.find('.') >= 0:
                continue

            field = self.table[fieldname]
            comment = None

            if comments:
                comment = col3.get(fieldname, field.comment)
            if comment == None:
                comment = ''
            self.custom.comment[fieldname] = comment

            if labels != None and fieldname in labels:
                label = labels[fieldname]
            else:
                label = str(field.label) + ': '
            self.custom.label[fieldname] = label

            field_id = '%s_%s' % (table._tablename, fieldname)

            label = LABEL(label, _for=field_id,
                _id='%s__%s' % (field_id, ID_LABEL_SUFFIX))

            row_id = '%s__%s' % (field_id, ID_ROW_SUFFIX)
            if field.type == 'id':
                self.custom.dspval.id = nbsp
                self.custom.inpval.id = ''
                widget = ''
                if record:
                    if showid and 'id' in fields and field.readable:
                        v = record['id']
                        widget = SPAN(v, _id=field_id)
                        self.custom.dspval.id = str(v)
                        xfields.append(TR(label, widget,
                            comment, _id='%s__%s' % ('id', ID_ROW_SUFFIX)))
                    self.record_id = str(record['id'])
                self.custom.widget.id = widget
                continue

            if readonly and not ignore_rw and not field.readable:
                continue

            if record:
                default = record[fieldname]
            else:
                default = field.default

            cond = readonly or \
                (not ignore_rw and not field.writable and field.readable)

            if default and not cond:
                default = field.formatter(default)
            dspval = default
            inpval = default

            if cond:

                # ## if field.represent is available else
                # ## ignore blob and preview uploaded images
                # ## format everything else

                if field.represent:
                    inp = field.represent(default)
                elif field.type in ['blob']:
                    continue
                elif field.type == 'upload':
                    inp = UploadWidget.represent(field, default, upload)
                else:
                    inp = field.formatter(default)
            elif hasattr(field, 'widget') and field.widget:
                inp = field.widget(field, default)
            elif field.type == 'upload':
                inp = self.widgets.upload.widget(field, default, upload)
            elif field.type == 'boolean':
                inp = self.widgets.boolean.widget(field, default)
                if default:
                    inpval = 'checked'
                else:
                    inpval = ''
            elif OptionsWidget.has_options(field):
                if not field.requires.multiple:
                    inp = self.widgets.options.widget(field, default)
                else:
                    inp = self.widgets.multiple.widget(field, default)
                if fieldname in keepopts:
                    inpval = TAG[''](*inp.components)
            elif field.type == 'text':
                inp = self.widgets.text.widget(field, default)
            elif field.type == 'password':
                inp = self.widgets.password.widget(field, default)
                if self.record:
                    dspval = PasswordWidget.DEFAULT_PASSWORD_DISPLAY
                else:
                    dspval = ''
            elif field.type == 'blob':
                continue
            else:
                inp = self.widgets.string.widget(field, default)

            tr = self.trows[fieldname] = TR(label, inp, comment,
                    _id=row_id)
            xfields.append(tr)
            self.custom.dspval[fieldname] = dspval or nbsp
            self.custom.inpval[fieldname] = inpval or ''
            self.custom.widget[fieldname] = inp

        # if a record is provided and found, as is linkto
        # build a link
        if record and linkto:
            for (rtable, rfield) in table._referenced_by:
                if keyed:
                    rfld = table._db[rtable][rfield] 
                    query = urllib.quote(str(rfld == record[rfld.type[10:].split('.')[1]]))
                else:
#                 <block>
                    query = urllib.quote(str(table._db[rtable][rfield]
                             == record.id))
                lname = olname = '%s.%s' % (rtable, rfield)
                if ofields and not olname in ofields:
                    continue
                if labels and lname in labels:
                    lname = labels[lname]
                widget = A(lname,
                           _class='reference',
                           _href='%s/%s?query=%s' % (linkto, rtable, query))
                xfields.append(
                    TR('',
                       widget,
                       col3.get(olname, ''),
                       _id='%s__%s' % (olname.replace('.', '__'), ID_ROW_SUFFIX),
                    ))
                self.custom.linkto[olname.replace('.', '__')] = widget
#                 </block>

        # when deletable, add delete? checkbox
        self.custom.deletable = ''
        if record and deletable:
            widget = INPUT(_type='checkbox',
                            _class='delete',
                            _id=self.FIELDKEY_DELETE_RECORD,
                            _name=self.FIELDNAME_REQUEST_DELETE,
                            )
            xfields.append(TR(
                            LABEL(
                                delete_label,
                                _for=self.FIELDKEY_DELETE_RECORD,
                                _id='%s__%s' % (self.FIELDKEY_DELETE_RECORD,
                                    ID_LABEL_SUFFIX),
                            ),
                            widget,
                            col3.get(self.FIELDKEY_DELETE_RECORD, ''),
                            _id='%s__%s' % (self.FIELDKEY_DELETE_RECORD,
                                ID_ROW_SUFFIX)
                            ))
            self.custom.deletable = widget
        # when writable, add submit button
        self.custom.submit = ''
        if not readonly:
            widget = INPUT(_type='submit',
                           _value=submit_button)
            xfields.append(TR('', widget,
                           col3.get('submit_button', ''),
                           _id='submit_record__row'))
            self.custom.submit = widget
        # if a record is provided and found
        # make sure it's id is stored in the form
        if record:
            if not self['hidden']:
                self['hidden'] = {}
            if not keyed:
                self['hidden']['id'] = record['id']

        (begin, end) = self._xml()
        self.custom.begin = XML("<%s %s>" % (self.tag, begin))
        self.custom.end = XML("%s</%s>" % (end, self.tag))
        self.components = [TABLE(*xfields)]

    def accepts(
        self,
        request_vars,
        session=None,
        formname='%(tablename)s_%(record_id)s',
        keepvalues=False,
        onvalidation=None,
        dbio=True,
        ):
        """
        same as FORM.accepts but also does insert, update or delete in SQLDB.
        """

        keyed = isinstance(self.table,KeyedTable)
        if self.record:
            if keyed:
                formname_id = '.'.join([str(self.record[k]) for k in self.table._primarykey if hasattr(self.record,k)])
                record_id = dict([(k,request_vars[k]) for k in self.table._primarykey])
            else:
                (formname_id, record_id) = \
                    (self.record.id, request_vars.get('id', None))
        else:
            if keyed:
                formname_id = 'create'
                record_id = dict([(k,None) for k in self.table._primarykey])
            else:
                (formname_id, record_id) = ('create', None)

        if not keyed and isinstance(record_id, (list, tuple)):
            record_id = record_id[0]

        if formname:
            formname = formname % dict(tablename = self.table._tablename,
                                       record_id = formname_id)

        # ## THIS IS FOR UNIQUE RECORDS, read IS_NOT_IN_DB

        for fieldname in self.fields:
            field = self.table[fieldname]
            requires = field.requires or []
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            [item.set_self_id(self.record_id) for item in requires
            if hasattr(item, 'set_self_id')]

        # ## END

        fields = {}
        for key in self.vars:
            fields[key] = self.vars[key]
        ret = FORM.accepts(
            self,
            request_vars,
            session,
            formname,
            keepvalues,
            onvalidation,
            )

        if not ret and self.record and self.errors:
            for key in self.errors.keys():
                if not request_vars.get(key, None) \
                        and self.table[key].type=='upload' \
                        and self.record[key] \
                        and not key+UploadWidget.ID_DELETE_SUFFIX in \
                            request_vars:
                    del self.errors[key]
            if not self.errors:
                ret = True

        requested_delete = \
            request_vars.get(self.FIELDNAME_REQUEST_DELETE, False)

        self.custom.end = TAG[''](self.hidden_fields(), self.custom.end)

        auch = record_id and self.errors and requested_delete

        # auch is true when user tries to delete a record
        # that does not pass validation, yet it should be deleted

        if not ret and not auch:
            for fieldname in self.fields:
                field = self.table[fieldname]
                if hasattr(field, 'widget') and field.widget\
                    and fieldname in request_vars:
                    self.trows[fieldname][1].components = \
                        [field.widget(field, request_vars[fieldname])]
                    self.trows[fieldname][1][0].errors = self.errors
            return ret

        if record_id and record_id != self.record_id:
            raise SyntaxError, 'user is tampering with form\'s record_id: ' \
                               '%s != %s' % (record_id, self.record_id)

        if requested_delete:
            if keyed:
                qry = reduce(lambda x,y: x & y, [self.table[k]==record_id[k] for k in self.table._primarykey])
                if self.table._db(qry).delete():
                    self.vars.update(record_id)
            else:
                self.table._db(self.table.id == self.record.id).delete()
                self.vars.id = self.record.id
            return True

        for fieldname in self.fields:
            if not fieldname in self.table:
                continue

            if not self.ignore_rw and not self.table[fieldname].writable:
                continue

            field = self.table[fieldname]
            if field.type == 'id':
                continue
            if field.type == 'boolean':
                if self.vars.get(fieldname, False):
                    fields[fieldname] = True
                else:
                    fields[fieldname] = False
            elif field.type == 'password' and self.record\
                and request_vars.get(fieldname, None) == \
                    PasswordWidget.DEFAULT_PASSWORD_DISPLAY:
                continue  # do not update if password was not changed
            elif field.type == 'upload':
                f = self.vars[fieldname]
                fd = fieldname + '__delete'
                if f == '' or f == None:
                    if self.vars.get(fd, False) or not self.record:
                        fields[fieldname] = ''
                    else:
                        fields[fieldname] = self.record[fieldname]
                    continue
                elif hasattr(f,'file'):
                    (source_file, original_filename) = (f.file, f.filename)
                elif isinstance(f, (str, unicode)):
                    ### do not know why this happens, it should not
                    (source_file, original_filename) = \
                        (cStringIO.StringIO(f), 'file.txt')
                newfilename = field.store(source_file, original_filename)
                self.vars['%s_newfilename' % fieldname] = fields[fieldname] = newfilename 
                if field.uploadfield and not field.uploadfield==True:
                    fields[field.uploadfield] = source_file.read()
                continue
            elif fieldname in self.vars:
                fields[fieldname] = self.vars[fieldname]
            elif field.default == None:
                self.errors[fieldname] = 'no data'
                return False

            if field.type == 'integer':
                if fields[fieldname] != None:
                    fields[fieldname] = int(fields[fieldname])
            elif field.type[:9] == 'reference':
                if fields[fieldname] != None and isinstance(self.table,Table) and not keyed:
                    fields[fieldname] = int(fields[fieldname])
            elif field.type == 'double':
                if fields[fieldname] != None:
                    fields[fieldname] = float(fields[fieldname])

        for fieldname in self.vars:
            if fieldname != 'id' and fieldname in self.table.fields\
                 and not fieldname in fields and not fieldname\
                 in request_vars:
                fields[fieldname] = self.vars[fieldname]
        
        if dbio:
            if keyed:
                if reduce(lambda x,y: x and y, record_id.values()): # if record_id
                    if fields:
                        qry = reduce(lambda x,y: x & y, [self.table[k]==self.record[k] for k in self.table._primarykey])
                        self.table._db(qry).update(**fields)
                else:
                    pk = self.table.insert(**fields)
                    if pk:
                        self.vars.update(pk)
                    else:
                        ret = False
            else:
                if record_id:
                    self.vars.id = self.record.id
                    if fields:
                        self.table._db(self.table.id == self.record.id).update(**fields)
                else:
                    self.vars.id = self.table.insert(**fields)

        return ret

    @staticmethod
    def factory(*fields, **attributes):
        """
        generates a SQLFORM for the given fields.

        Internally will build a non-database based data model
        to hold the fields.
        """
        return SQLFORM(SQLDB(None).define_table('no_table', *fields),
                       **attributes)


class SQLTABLE(TABLE):

    """
    given a SQLRows object, as returned by a db().select(), generates
    an html table with the rows.

    optional arguments:

    :param linkto: URL (or lambda to generate a URL) to edit individual records
    :param upload: URL to download uploaded files
    :param orderby: Add an orderby link to column headers.
    :param headers: dictionary of headers to headers redefinions
    :param truncate: length at which to truncate text in table cells.
        Defaults to 16 characters.

    optional names attributes for passed to the <table> tag

    Simple linkto example::

        rows = db.select(db.sometable.ALL)
        table = SQLTABLE(rows, linkto='someurl')

    This will link rows[id] to .../sometable/value_of_id


    More advanced linkto example::

        def mylink(field, type, ref):
            return URL(r=request, args=[field])

        rows = db.select(db.sometable.ALL)
        table = SQLTABLE(rows, linkto=mylink)

    This will link rows[id] to
        current_app/current_controlle/current_function/value_of_id


    """

    def __init__(
        self,
        sqlrows,
        linkto=None,
        upload=None,
        orderby=None,
        headers={},
        truncate=16,
        **attributes
        ):

        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not orderby:
            for c in sqlrows.colnames:
                row.append(TH(headers.get(c, c)))
        else:
            for c in sqlrows.colnames:
                row.append(TH(A(headers.get(c, c), _href='?orderby='
                            + c)))
        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = 'even'
            else:
                _class = 'odd'
            for colname in sqlrows.colnames:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split('.')
                field = sqlrows.db[tablename][fieldname]
                if tablename in record and isinstance(record,
                        Row) and isinstance(record[tablename],
                        Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, 'something wrong in SQLRows object'
                if field.represent:
                    r = field.represent(r)
                    row.append(TD(r))
                    continue
                if field.type == 'blob' and r:
                    row.append(TD('DATA'))
                    continue
                r = str(field.formatter(r))
                if field.type == 'upload':
                    if upload and r:
                        row.append(TD(A('file', _href='%s/%s' % (upload, r))))
                    elif r:
                        row.append(TD('file'))
                    else:
                        row.append(TD())
                    continue
                ur = unicode(r, 'utf8')
                if len(ur) > truncate:
                    r = ur[:truncate - 3].encode('utf8') + '...'
                if linkto and field.type == 'id':
                    try:
                        href = linkto(r, 'table', tablename)
                    except TypeError:
                        href = '%s/%s/%s' % (linkto, tablename, r)
                    row.append(TD(A(r, _href=href)))
                elif linkto and field.type[:9] == 'reference':
                    ref = field.type[10:]
                    try:
                        href = linkto(r, 'reference', ref)
                    except TypeError:
                        href = '%s/%s/%s' % (linkto, ref, r)
                        if ref.find('.') >= 0:
                            tref,fref = ref.split('.')
                            if hasattr(sqlrows.db[tref],'_primarykey'):
                                href = '%s/%s?%s' % (linkto, tref, urllib.urlencode({fref:ur}))
                            
                    row.append(TD(A(r, _href=href)))
                elif linkto and hasattr(field._table,'_primarykey') and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict( [ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) and 
                                 (k, record[tablename][k])) or (k, record[k]) \
                                    for k in field._table._primarykey ] ))
                    row.append(TD(A(r, _href='%s/%s?%s' % (linkto, tablename, key))))
                else:
                    row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))


form_factory = SQLFORM.factory
