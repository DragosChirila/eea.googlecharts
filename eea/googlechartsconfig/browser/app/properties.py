""" Exhibit properties
"""
import logging
try:
    import json as simplejson
    simplejson = simplejson # pylint
except ImportError:
    import simplejson
from zope import schema
from zope.interface import Interface
from zope.formlib.form import Fields
from zope.component import queryAdapter
from zope.formlib.form import SubPageForm
from Products.statusmessages.interfaces import IStatusMessage
from zope.formlib.form import action as formaction
from zope.formlib.form import setUpWidgets, haveInputWidgets
from eea.googlechartsconfig.app.interfaces import IChartsConfig

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("eea.daviz")
logger = logging.getLogger('eea.daviz')

class IExhibitPropertiesEdit(Interface):
    """ Edit Exhibit global properties
    """
    views = schema.List(
        title=u'Views',
        description=u'Enable exhibit views',
        unique=True,
        value_type=schema.Choice(
            vocabulary="eea.googlechartsconfig.vocabularies.ChartsVocabulary")
    )

class EditForm(SubPageForm):
    """ Layer to edit daviz properties.
    """
    label = u"Global settings"
    form_fields = Fields(IExhibitPropertiesEdit)

    def __init__(self, context, request):
        super(EditForm, self).__init__(context, request)
        name = self.__name__
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        self.prefix = name.replace('.edit', '', 1)
        self.message = 'Changes saved'

    @property
    def _data(self):
        """ Form data
        """
        accessor = queryAdapter(self.context, IChartsConfig)
        return {
            'name': self.prefix,
            'views': [view.get('name') for view in accessor.views],
        }

    def setUpWidgets(self, ignore_request=False):
        """ Setup widgets
        """
        self.adapters = {}
        self.widgets = setUpWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            form=self, data=self._data, adapters=self.adapters,
            ignore_request=ignore_request)


    def handle_views(self, data):
        """ Handle views property
        """
        mutator = queryAdapter(self.context, IChartsConfig)
        old = mutator.views
        old = dict((view.get('name', ''), dict(view))
                   for view in old)
        mutator.delete_views()

        for key in data.get('views', []):
            properties = old.get(key, {})
            properties.pop('name', None)
            mutator.add_view(name=key, **properties)

    @formaction(_('Save'), condition=haveInputWidgets)
    def save(self, action, data):
        """ Handle save action
        """

        self.handle_views(data)

        # Return
        name = action.__name__.encode('utf-8')
        value = self.request.form.get(name, '')
        if value == 'ajax':
            return self.message
        return self.nextUrl

    @property
    def nextUrl(self):
        """ Next
        """
        IStatusMessage(self.request).addStatusMessage(self.message, type='info')
        next_url = self.context.absolute_url() + '/daviz-edit.html'
        self.request.response.redirect(next_url)

